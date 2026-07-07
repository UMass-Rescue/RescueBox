#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::fs::{self, File, OpenOptions};
use std::io::{copy, Write};
use std::os::windows::process::CommandExt;
use std::path::{Component, Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use std::{thread, time::Duration};

use tauri::{Manager, RunEvent};
use tauri_plugin_dialog::MessageDialogKind;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

struct AppState {
    frontend: Mutex<Option<CommandChild>>,
    backend: Mutex<Option<CommandChild>>,
    closing_splash_for_main: AtomicBool,
    shell_log_path: Mutex<Option<PathBuf>>,
}

const UI_URL: &str = "http://127.0.0.1:8080/";
const UI_HOST: &str = "127.0.0.1:8080";
const BACKEND_HOST: &str = "127.0.0.1:8000";
const UI_READY_MAX_ATTEMPTS: u32 = 280;
const UI_READY_POLL_MS: u64 = 500;

const CREATE_NO_WINDOW: u32 = 0x08000000;

const BACKEND_EXE: &str = "rescuebox-x86_64-pc-windows-msvc.exe";
const BACKEND_EXE_FALLBACK: &str = "rescuebox.exe";


const MODELS_REGISTRY_KEY: &str = r"Software\rescuebox-desktop\RescueBox";
const MODELS_REGISTRY_VALUE: &str = "ModelsZipSource";
const MODELS_ZIP_CANDIDATE_NAMES: [&str; 2] = ["models.zip", "rb_3.1_onnx_models.zip"];

fn backend_exe_names() -> [&'static str; 2] {
    [BACKEND_EXE, BACKEND_EXE_FALLBACK]
}

/// Directory that contains the backend PyInstaller executable.
fn resolve_backend_root(base: &Path) -> Option<PathBuf> {
    for exe in backend_exe_names() {
        let direct = base.join(exe);
        if direct.is_file() {
            return Some(base.to_path_buf());
        }
    }
    let backend_sub = base.join("backend");
    if backend_sub.is_dir() {
        for exe in backend_exe_names() {
            if backend_sub.join(exe).is_file() {
                return Some(backend_sub);
            }
        }
    }
    if !base.is_dir() {
        return None;
    }
    let entries = fs::read_dir(base).ok()?;
    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }
        for exe in backend_exe_names() {
            if path.join(exe).is_file() {
                return Some(path);
            }
        }
    }
    None
}

fn backend_executable_in(root: &Path) -> Option<PathBuf> {
    for exe in backend_exe_names() {
        let path = root.join(exe);
        if path.is_file() {
            return Some(path);
        }
    }
    None
}

fn zip_contains_backend_exe(zip_path: &Path) -> Result<bool, String> {
    let file = File::open(zip_path).map_err(|e| e.to_string())?;
    let mut archive = zip::ZipArchive::new(file).map_err(|e| e.to_string())?;
    for i in 0..archive.len() {
        let name = archive
            .by_index(i)
            .map_err(|e| e.to_string())?
            .name()
            .replace('\\', "/");
        let lower = name.to_lowercase();
        if lower.ends_with(BACKEND_EXE) || lower.ends_with(BACKEND_EXE_FALLBACK) {
            return Ok(true);
        }
    }
    Ok(false)
}

fn remove_incomplete_backend_extract(install_home: &Path) {
    let backend_dir = install_home.join("backend");
    if backend_dir.is_dir() && resolve_backend_root(&backend_dir).is_none() {
        let _ = fs::remove_dir_all(&backend_dir);
    }
}

/// Writable install root (backend extracted to `<install_home>/backend` on first run).
fn install_home(app: &tauri::AppHandle) -> PathBuf {
    app.path()
    .app_data_dir()
    .unwrap_or_else(|_| PathBuf::from("."))
}

fn extract_zip_entries<F>(zip_path: &Path, mut map_out_path: F) -> Result<(), String>
where
    F: FnMut(&Path) -> Option<PathBuf>,
{
    let file = File::open(zip_path).map_err(|e| format!("open {}: {e}", zip_path.display()))?;
    let mut archive = zip::ZipArchive::new(file).map_err(|e| e.to_string())?;

    for i in 0..archive.len() {
        let mut entry = archive.by_index(i).map_err(|e| e.to_string())?;
        let Some(relative) = entry.enclosed_name() else {
            continue;
        };
        if relative
            .components()
            .any(|c| matches!(c, Component::ParentDir))
        {
            return Err(format!("unsafe path in zip: {}", entry.name()));
        }
        let Some(out_relative) = map_out_path(relative.as_ref()) else {
            continue;
        };
        if out_relative
            .components()
            .any(|c| matches!(c, Component::ParentDir))
        {
            return Err(format!("unsafe mapped path for: {}", entry.name()));
        }

        let out_path = out_relative;
        if entry.is_dir() || entry.name().ends_with('/') {
            fs::create_dir_all(&out_path).map_err(|e| e.to_string())?;
            continue;
        }
        if let Some(parent) = out_path.parent() {
            fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        }
        let mut out_file = File::create(&out_path).map_err(|e| e.to_string())?;
        copy(&mut entry, &mut out_file).map_err(|e| e.to_string())?;
    }
    Ok(())
}

fn extract_backend_zip(zip_path: &Path, install_home: &Path) -> Result<(), String> {
    fs::create_dir_all(install_home).map_err(|e| e.to_string())?;
    extract_zip_entries(zip_path, |relative| Some(install_home.join(relative)))
}

fn cached_backend_zip_path(home: &Path) -> PathBuf {
    home.join("backend.zip")
}

fn normalize_models_zip_source(raw: &str) -> String {
    let mut s = raw.trim();
    loop {
        if s.len() >= 2 && s.starts_with('"') && s.ends_with('"') {
            s = s[1..s.len() - 1].trim();
            continue;
        }
        if s.len() >= 2 && s.starts_with('\'') && s.ends_with('\'') {
            s = s[1..s.len() - 1].trim();
            continue;
        }
        break;
    }
    if let Some(rest) = s.strip_prefix("file:///") {
        s = rest;
    } else if let Some(rest) = s.strip_prefix("file://") {
        s = rest;
    }
    s.trim_end_matches(['\\', '/']).to_string()
}

#[cfg(windows)]
fn read_registry_models_zip_source() -> Option<String> {
    use winreg::enums::HKEY_CURRENT_USER;
    use winreg::RegKey;

    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let key = hkcu.open_subkey(MODELS_REGISTRY_KEY).ok()?;
    let value: String = key.get_value(MODELS_REGISTRY_VALUE).ok()?;
    let value = normalize_models_zip_source(&value);
    if value.is_empty() {
        None
    } else {
        Some(value)
    }
}

#[cfg(not(windows))]
fn read_registry_models_zip_source() -> Option<String> {
    None
}

fn resolve_local_models_zip_path(source: &str) -> Result<PathBuf, String> {
    let source = normalize_models_zip_source(source);
    if source.is_empty() {
        return Err("Models source path is empty.".into());
    }
    let path = PathBuf::from(&source);
    if path.is_file() {
        return Ok(path);
    }
    if path.extension().is_some_and(|e| e.eq_ignore_ascii_case("zip")) {
        return Err(format!("Models zip not found: {}", path.display()));
    }
    if !path.is_dir() {
        return Err(format!(
            "Models source is not a folder or zip file: {source}"
        ));
    }
    for name in MODELS_ZIP_CANDIDATE_NAMES {
        let candidate = path.join(name);
        if candidate.is_file() {
            return Ok(candidate);
        }
    }
    let mut zips: Vec<PathBuf> = fs::read_dir(&path)
        .map_err(|e| e.to_string())?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| {
            p.is_file()
                && p.extension()
                    .is_some_and(|ext| ext.eq_ignore_ascii_case("zip"))
        })
        .collect();
    zips.sort();
    match zips.len() {
        0 => Err(format!(
            "No .zip file found in {} (expected one of {:?}).",
            path.display(),
            MODELS_ZIP_CANDIDATE_NAMES
        )),
        1 => Ok(zips.remove(0)),
        _ => Err(format!(
            "Multiple zip files in {}; name one {:?} or set ModelsZipSource to the full zip path.",
            path.display(),
            MODELS_ZIP_CANDIDATE_NAMES
        )),
    }
}

fn backend_internal_dir(backend_root: &Path) -> PathBuf {
    backend_root.join("_internal")
}

fn backend_onnx_models_present(backend_root: &Path) -> bool {
    let internal = backend_internal_dir(backend_root);
    internal
        .join("image_embeddings")
        .join("clip_onnx_models")
        .join("text.onnx")
        .is_file()
}

fn models_zip_entry_to_internal(relative: &Path) -> Option<PathBuf> {
    let joined = relative.to_string_lossy().replace('\\', "/");
    let joined = joined.trim_start_matches("./");

    // Zip of the PyInstaller backend tree (e.g. backend-o/models.zip)
    if let Some(rest) = joined.strip_prefix("backend/_internal/") {
        return Some(PathBuf::from(rest));
    }
    if let Some(rest) = joined.strip_prefix("_internal/") {
        return Some(PathBuf::from(rest));
    }

    // Repo src/... layout (rb_3.1_onnx_models.zip)
    let mut parts: Vec<&str> = joined.split('/').filter(|p| !p.is_empty()).collect();
    if parts.first().copied() != Some("src") {
        return None;
    }
    parts.remove(0);
    if parts.is_empty() {
        return None;
    }
    let joined = parts.join("/");
    let remapped = if let Some(rest) = joined.strip_prefix("image-embeddings/image_embeddings/") {
        format!("image_embeddings/{rest}")
    } else if let Some(rest) = joined.strip_prefix("image-similarity/image_similarity/") {
        format!("image_similarity/{rest}")
    } else if let Some(rest) = joined.strip_prefix("deepfake-detection/deepfake_detection/") {
        format!("deepfake_detection/{rest}")
    } else if let Some(rest) =
        joined.strip_prefix("face-detection-recognition/face_detection_recognition/")
    {
        format!("face_detection_recognition/{rest}")
    } else if let Some(rest) = joined.strip_prefix("age_and_gender_detection/") {
        format!("src/age_and_gender_detection/{rest}")
    } else {
        joined
    };
    Some(PathBuf::from(remapped))
}

fn extract_models_zip(zip_path: &Path, backend_root: &Path) -> Result<(), String> {
    let internal = backend_internal_dir(backend_root);
    fs::create_dir_all(&internal).map_err(|e| e.to_string())?;
    let internal_for_map = internal.clone();
    extract_zip_entries(zip_path, move |relative| {
        models_zip_entry_to_internal(relative).map(|p| internal_for_map.join(p))
    })
}

fn ensure_models_for_backend(
    app: &tauri::AppHandle,
    backend_root: &Path,
) -> Result<(), String> {
    if backend_onnx_models_present(backend_root) {
        return Ok(());
    }

    let Some(source) = read_registry_models_zip_source() else {
        append_shell_log(
            app,
            "WARN",
            "ONNX models missing and no ModelsZipSource in registry (set during MSI install).",
        );
        return Ok(());
    };

    let zip_path = resolve_local_models_zip_path(&source)?;

    set_splash_status(
        app,
        "This may take a few minutes",
    );
    append_shell_log(
        app,
        "INFO",
        &format!(
            "Extracting models {} -> {}",
            zip_path.display(),
            backend_internal_dir(backend_root).display()
        ),
    );
    extract_models_zip(&zip_path, backend_root)?;

    if !backend_onnx_models_present(backend_root) {
        let expected = backend_internal_dir(backend_root)
            .join("image_embeddings")
            .join("clip_onnx_models")
            .join("text.onnx");
        return Err(format!(
            "models.zip was extracted but expected ONNX files were not found (e.g. {}). \
             Use a zip with backend/_internal/... or src/... layout.",
            expected.display()
        ));
    }
    Ok(())
}

fn ensure_backend_zip_on_disk(app: &tauri::AppHandle, home: &Path) -> Result<PathBuf, String> {
    let zip_path = cached_backend_zip_path(home);
    if zip_path.is_file() {
        match zip_contains_backend_exe(&zip_path) {
            Ok(true) => return Ok(zip_path),
            Ok(false) => {
                append_shell_log(
                    app,
                    "WARN",
                    &format!("Removing invalid cached zip {}", zip_path.display()),
                );
                let _ = fs::remove_file(&zip_path);
            }
            Err(e) => return Err(format!("Could not read cached backend.zip: {e}")),
        }
    }

    Err(format!(
        "No backend bundle found. Copy a valid backend.zip (PyInstaller tree with {BACKEND_EXE}) to {}.",
        zip_path.display()
    ))
}

/// Resolve backend folder: app-data extract, bundled resource dir, or extract from local backend.zip.
fn ensure_backend_dir(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let home = install_home(app);
    if let Some(root) = resolve_backend_root(&home) {
        return Ok(root);
    }

    let resource_path = app.path().resource_dir().map_err(|e| e.to_string())?;
    let legacy = resource_path.join("backend");
    if let Some(root) = resolve_backend_root(&legacy) {
        return Ok(root);
    }

    let zip_path = ensure_backend_zip_on_disk(app, &home)?;

    remove_incomplete_backend_extract(&home);

    set_splash_status(
        app,
        "Extracting backend (ONNX models and plugins). This may take a minute…",
    );
    append_shell_log(
        app,
        "INFO",
        &format!("Extracting {} -> {}", zip_path.display(), home.display()),
    );

    extract_backend_zip(&zip_path, &home)?;

    resolve_backend_root(&home).ok_or_else(|| {
        format!(
            "backend.zip was extracted but neither {BACKEND_EXE} nor {BACKEND_EXE_FALLBACK} \
             was found under {}.",
            home.display()
        )
    })
}

fn http_get_ready(host_port: &str, path: &str, host_header: &str) -> bool {
    use std::io::{Read, Write};
    use std::net::TcpStream;

    let mut stream = match TcpStream::connect(host_port) {
        Ok(s) => s,
        Err(_) => return false,
    };
    let _ = stream.set_read_timeout(Some(Duration::from_millis(1500)));
    let _ = stream.set_write_timeout(Some(Duration::from_millis(1500)));
    let request = format!(
        "GET {path} HTTP/1.1\r\nHost: {host_header}\r\nConnection: close\r\n\r\n"
    );
    if stream.write_all(request.as_bytes()).is_err() {
        return false;
    }
    let mut buf = [0u8; 512];
    let n = stream.read(&mut buf).unwrap_or(0);
    if n < 12 {
        return false;
    }
    let head = String::from_utf8_lossy(&buf[..n]);
    head.starts_with("HTTP/1.") && !head.contains(" 5")
}

fn backend_http_ready() -> bool {
    http_get_ready(BACKEND_HOST, "/", "127.0.0.1:8000")
}

fn frontend_http_ready() -> bool {
    http_get_ready(UI_HOST, "/", "127.0.0.1:8080")
}

fn wait_for_backend(app: &tauri::AppHandle) {
    set_splash_status(app, "Waiting for backend…");
    for attempt in 0..UI_READY_MAX_ATTEMPTS {
        if backend_http_ready() {
            append_shell_log(
                app,
                "INFO",
                &format!(
                    "Backend ready on http://{BACKEND_HOST} (attempt {})",
                    attempt + 1
                ),
            );
            return;
        }
        thread::sleep(Duration::from_millis(UI_READY_POLL_MS));
    }
    append_shell_log(
        app,
        "WARN",
        &format!(
            "Timed out waiting for backend at http://{BACKEND_HOST}; starting frontend anyway."
        ),
    );
}

fn shell_log_path(app: &tauri::AppHandle) -> PathBuf {
    let state = app.state::<AppState>();
    let mut guard = state.shell_log_path.lock().unwrap();
    if let Some(path) = guard.as_ref() {
        return path.clone();
    }
    let path = app
        .path()
        .app_data_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
        .join("logs")
        .join("rescuebox-startup.log");
    if let Some(parent) = path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    *guard = Some(path.clone());
    path
}

fn append_shell_log(app: &tauri::AppHandle, level: &str, message: &str) {
    let path = shell_log_path(app);
    let stamp = chrono_lite_timestamp();
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(&path) {
        let _ = writeln!(file, "[{stamp}] {level}: {message}");
    }
}

/// Best-effort timestamp without adding the chrono crate.
fn chrono_lite_timestamp() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    format!("epoch-{secs}")
}

fn run_splash_js(app: &tauri::AppHandle, script: String) {
    let app = app.clone();
    let app_for_thread = app.clone();
    let _ = app.run_on_main_thread(move || {
        if let Some(w) = app_for_thread.get_webview_window("splashscreen") {
            let _ = w.eval(&script);
        }
    });
}

fn set_splash_status(app: &tauri::AppHandle, message: &str) {
    append_shell_log(app, "INFO", message);
    if let Ok(json) = serde_json::to_string(message) {
        run_splash_js(app, format!("window.setStartupStatus?.({json});"));
    }
}

fn show_startup_error(app: &tauri::AppHandle, message: impl AsRef<str>) {
    let msg = message.as_ref();
    append_shell_log(app, "ERROR", msg);
    if let Ok(json) = serde_json::to_string(msg) {
        run_splash_js(app, format!("window.setStartupError?.({json});"));
    }
}

fn notify_user(
    app: &tauri::AppHandle,
    title: impl Into<String>,
    message: impl Into<String>,
    kind: MessageDialogKind,
) {
    let title = title.into();
    let message = message.into();
    let level = match kind {
        MessageDialogKind::Error => "ERROR",
        MessageDialogKind::Warning => "WARN",
        MessageDialogKind::Info => "INFO",
        _ => "LOG",
    };
    append_shell_log(app, level, &format!("{title} — {message}"));
}

fn notify_info(app: &tauri::AppHandle, title: impl Into<String>, message: impl Into<String>) {
    notify_user(app, title, message, MessageDialogKind::Info);
}

fn notify_error(app: &tauri::AppHandle, title: impl Into<String>, message: impl Into<String>) {
    notify_user(app, title, message, MessageDialogKind::Error);
}

fn kill_sidecars(app: &tauri::AppHandle) {
    append_shell_log(app, "INFO", "Stopping RescueBox services…");
    let state = app.state::<AppState>();
    if let Some(child) = state.frontend.lock().unwrap().take() {
        let _ = child.kill();
    }
    if let Some(child) = state.backend.lock().unwrap().take() {
        let _ = child.kill();
    }
    #[cfg(target_os = "windows")]
    {
        for exe in [
            "frontend-x86_64-pc-windows-msvc.exe",
            "rescuebox-x86_64-pc-windows-msvc.exe",
        ] {
            let _ = std::process::Command::new("taskkill")
                .args(["/F", "/IM", exe, "/T"])
                .creation_flags(CREATE_NO_WINDOW)
                .stdout(std::process::Stdio::null())
                .stderr(std::process::Stdio::null())
                .status();
        }
    }
}

fn shutdown_app(app: &tauri::AppHandle) {
    kill_sidecars(app);
    app.exit(0);
}

fn reveal_main_and_close_splash(app: &tauri::AppHandle) {
    let ui_url: url::Url = UI_URL.parse().expect("valid UI url");

    let Some(main_window) = app.get_webview_window("main") else {
        show_startup_error(
            app,
            "Main webview window missing from tauri.conf.json",
        );
        return;
    };

    let _ = main_window.navigate(ui_url);
    let _ = main_window.show();
    let _ = main_window.set_focus();

    if let Some(splash) = app.get_webview_window("splashscreen") {
        let _ = splash.hide();
    }

    notify_info(
        app,
        "RescueBox",
        format!("Assistant UI opened at {UI_URL}"),
    );
}

fn spawn_sidecars(app: &tauri::AppHandle) -> bool {
    set_splash_status(app, "Preparing RescueBox…");

    let resource_path = match app.path().resource_dir() {
        Ok(p) => p,
        Err(e) => {
            show_startup_error(
                app,
                format!("No resource directory ({e}). Expecting dev servers on {UI_URL}"),
            );
            return false;
        }
    };

    let frontend_path = resource_path.join("frontend");
    let frontend_exe = frontend_path.join("frontend-x86_64-pc-windows-msvc.exe");

    let backend_path = match ensure_backend_dir(app) {
        Ok(p) => p,
        Err(e) => {
            show_startup_error(app, e);
            return false;
        }
    };
    if let Err(e) = ensure_models_for_backend(app, &backend_path) {
        show_startup_error(app, e);
        return false;
    }
    let backend_exe = match backend_executable_in(&backend_path) {
        Some(p) => p,
        None => {
            show_startup_error(
                app,
                format!("No backend executable under {}", backend_path.display()),
            );
            return false;
        }
    };

    if !frontend_exe.is_file() {
        show_startup_error(
            app,
            format!(
                "Missing RescueBox binaries. Frontend: {} Backend: {}",
                frontend_exe.display(),
                backend_exe.display()
            ),
        );
        return false;
    }

    let log_path = shell_log_path(app);
    append_shell_log(
        app,
        "INFO",
        &format!(
            "Starting backend and frontend. Full sidecar log: {}",
            log_path.display()
        ),
    );
    set_splash_status(app, "Starting backend…");

    let (mut rx_backend, child_backend) = match app
        .shell()
        .command(backend_exe.to_str().unwrap())
        .current_dir(backend_path.clone())
        .env("PYTHONPATH", backend_path.to_str().unwrap())
        .env("NO_PROXY", "127.0.0.1,localhost")
        .env("OLLAMA_HOST", "http://127.0.0.1:11434")
        .env("RESCUEBOX_HOME", resource_path.to_str().unwrap())
        .spawn()
    {
        Ok(pair) => pair,
        Err(e) => {
            show_startup_error(
                app,
                format!("RescueBox could not start the backend process: {e}"),
            );
            return false;
        }
    };

    
    set_splash_status(app, "Starting frontend…");

    let local_data = app
        .path()
        .app_data_dir()
        .expect("failed to get local data dir");

    let (mut rx, child) = match app
        .shell()
        .command(frontend_exe.to_str().unwrap())
        .current_dir(frontend_path.clone())
        .env("PYTHONPATH", frontend_path.to_str().unwrap())
        .env(
            "NICEGUI_STORAGE_PATH",
            local_data.join("nicegui").to_str().unwrap(),
        )
        .env("UVICORN_LOG_CONFIG", "")
        .env("NO_PROXY", "127.0.0.1,localhost")
        .env("RESCUEBOX_SHOW_BROWSER", "false")
        .env("OLLAMA_HOST", "http://127.0.0.1:11434")
        .env(
            "RESCUEBOX_HOME",
            resource_path.join("demo").to_str().unwrap(),
        )
        .spawn()
    {
        Ok(pair) => pair,
        Err(e) => {
            show_startup_error(
                app,
                format!("RescueBox could not start the frontend process: {e}"),
            );
            let _ = child_backend.kill();
            return false;
        }
    };

    let state = app.state::<AppState>();
    *state.frontend.lock().unwrap() = Some(child);
    *state.backend.lock().unwrap() = Some(child_backend);

    let app_fe = app.clone();
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                    let text = String::from_utf8_lossy(&line).into_owned();
                    append_shell_log(&app_fe, "INFO", &format!("[frontend stdout] {text}"));
                }
                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                    let text = String::from_utf8_lossy(&line).into_owned();
                    notify_error(&app_fe, "Frontend", text);
                }
                _ => {}
            }
        }
    });

    let app_be = app.clone();
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx_backend.recv().await {
            match event {
                tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                    let text = String::from_utf8_lossy(&line).into_owned();
                    append_shell_log(&app_be, "INFO", &format!("[backend stdout] {text}"));
                }
                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                    let text = String::from_utf8_lossy(&line).into_owned();
                    notify_error(&app_be, "Backend", text);
                }
                _ => {}
            }
        }
    });

    true
}

fn wait_for_frontend_ui(app: &tauri::AppHandle) {
    for attempt in 0..UI_READY_MAX_ATTEMPTS {
        if frontend_http_ready() {
            append_shell_log(
                app,
                "INFO",
                &format!("NiceGUI ready on {UI_URL} (attempt {})", attempt + 1),
            );
            set_splash_status(app, "Opening assistant…");
            return;
        }
        thread::sleep(Duration::from_millis(UI_READY_POLL_MS));
    }
    set_splash_status(
        app,
        &format!("Timed out waiting for {UI_URL}; opening the UI anyway."),
    );
}

fn show_splash_screen(app: &tauri::AppHandle) {
    if let Some(main_window) = app.get_webview_window("main") {
        let _ = main_window.hide();
    }
    if let Some(splash) = app.get_webview_window("splashscreen") {
        let _ = splash.show();
        let _ = splash.set_focus();
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(AppState {
            frontend: Mutex::new(None),
            backend: Mutex::new(None),
            closing_splash_for_main: AtomicBool::new(false),
            shell_log_path: Mutex::new(None),
        })
        .setup(|app| {
            show_splash_screen(app.handle());
            set_splash_status(app.handle(), "Initializing…");
            let app_handle = app.handle().clone();

            tauri::async_runtime::spawn(async move {
                // Let the splash webview paint before long extract/download work.
                thread::sleep(Duration::from_millis(200));

                let extract_app = app_handle.clone();
                let sidecars_ok = tauri::async_runtime::spawn_blocking(move || {
                    spawn_sidecars(&extract_app)
                })
                .await
                .unwrap_or(false);

                if !sidecars_ok {
                    return;
                }

                let wait_app = app_handle.clone();
                let _ = tauri::async_runtime::spawn_blocking(move || {
                    wait_for_frontend_ui(&wait_app);
                })
                .await;

                let handle = app_handle.clone();
                let _ = app_handle.run_on_main_thread(move || {
                    reveal_main_and_close_splash(&handle);
                });
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let app = window.app_handle();
                let label = window.label();

                if label == "splashscreen" {
                    let state = app.state::<AppState>();
                    if app
                        .get_webview_window("main")
                        .is_some_and(|w| w.is_visible().unwrap_or(false))
                    {
                        return;
                    }
                    if state.closing_splash_for_main.load(Ordering::SeqCst) {
                        return;
                    }
                    shutdown_app(&app);
                    return;
                }

                if label == "main" {
                    shutdown_app(&app);
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if matches!(event, RunEvent::Exit) {
                kill_sidecars(app_handle);
            }
        });
}
