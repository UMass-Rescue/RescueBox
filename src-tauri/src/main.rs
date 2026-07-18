#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::fs::{self, File, OpenOptions};
use std::io::{copy, Write};
use std::os::windows::process::CommandExt;
use std::path::{Component, Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use std::{thread, time::Duration};

use tauri::webview::PageLoadEvent;
use tauri::{Manager, RunEvent};
use tauri_plugin_dialog::MessageDialogKind;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

struct AppState {
    frontend: Mutex<Option<CommandChild>>,
    backend: Mutex<Option<CommandChild>>,
    closing_splash_for_main: AtomicBool,
    quit_on_close: AtomicBool,
    startup_scheduled: AtomicBool,
    shell_log_path: Mutex<Option<PathBuf>>,
}

const UI_URL: &str = "http://127.0.0.1:8080/";
const UI_HOST: &str = "127.0.0.1:8080";
const BACKEND_HOST: &str = "127.0.0.1:8000";
const UI_READY_MAX_ATTEMPTS: u32 = 280;
const UI_READY_POLL_MS: u64 = 500;

const CREATE_NO_WINDOW: u32 = 0x08000000;

const BACKEND_EXE: &str = "rescuebox-x86_64-pc-windows-msvc.exe";

const MODELS_REGISTRY_KEY: &str = r"Software\RescueBox\RescueBox";
const MODELS_REGISTRY_VALUE: &str = "ModelsZipSource";
const PRE_REQS_ZIP_NAMES: [&str; 1] = ["pre-reqs_3.1.zip"];
const PRE_REQS_FOLDER_NAMES: [&str; 2] = ["pre-reqs", "pre_reqs"];
const PREREQS_BUNDLE_DIR: &str = "prereqs_status";
const PREREQS_SETUP_MARKER: &str = ".prereqs_setup_done.txt";
const OLLAMA_SETUP_EXE: &str = "OllamaSetup.exe";
const OLLAMA_MODELS_ZIP: &str = "ollama_models_3.1.zip";
const ONNX_MODELS_ZIP: &str = "onnx_models_3.1.zip";
const OLLAMA_OFFLINE_MODELS_MARKER: &str = ".ollama_models_installed.txt";
const WINFSP_MSI_NAME: &str = "winfsp-2.1.25156.msi";
const POSTGRES_ZIP_NAME: &str = "postgres.zip";
const POSTGRES_SETUP_BAT: &str = "setup.bat";

fn backend_exe_names() -> [&'static str; 1] {
    [BACKEND_EXE]
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

/// Writable install root (backend extracted to `<install_home>/backend` on first run).
fn install_home(app: &tauri::AppHandle) -> PathBuf {
    app.path()
    .app_local_data_dir()
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
fn read_registry_string_value(name: &str) -> Option<String> {
    use winreg::enums::HKEY_CURRENT_USER;
    use winreg::RegKey;

    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let key = hkcu.open_subkey(MODELS_REGISTRY_KEY).ok()?;
    let value: String = key.get_value(name).ok()?;
    let value = normalize_models_zip_source(&value);
    if value.is_empty() {
        None
    } else {
        Some(value)
    }
}

#[cfg(windows)]
fn read_registry_models_zip_source() -> Option<String> {
    read_registry_string_value(MODELS_REGISTRY_VALUE)
}

#[cfg(not(windows))]
fn read_registry_models_zip_source() -> Option<String> {
    None
}

/// Prereqs bundle layout: files live directly under ``root`` (e.g. ``pre-reqs/OllamaSetup.exe``).
fn find_file_in_tree(root: &Path, names: &[&str]) -> Option<PathBuf> {
    for name in names {
        let path = root.join(name);
        if path.is_file() {
            return Some(path);
        }
    }
    None
}

fn resolve_pre_reqs_folder(source: &str) -> Option<PathBuf> {
    let source = normalize_models_zip_source(source);
    if source.is_empty() {
        return None;
    }
    let path = PathBuf::from(&source);
    if !path.is_dir() {
        return None;
    }
    for name in PRE_REQS_FOLDER_NAMES {
        let candidate = path.join(name);
        if candidate.is_dir() {
            return Some(candidate);
        }
    }
    None
}

#[cfg(windows)]
fn winfsp_installed() -> bool {
    use winreg::enums::HKEY_LOCAL_MACHINE;
    use winreg::RegKey;

    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    if hklm.open_subkey(r"SOFTWARE\WinFsp").is_ok() {
        return true;
    }
    if hklm.open_subkey(r"SOFTWARE\WOW6432Node\WinFsp").is_ok() {
        return true;
    }
    PathBuf::from(r"C:\Program Files (x86)\WinFsp\bin\winfsp-x64.dll").is_file()
}

#[cfg(not(windows))]
fn winfsp_installed() -> bool {
    false
}

fn ollama_installed() -> bool {
    if let Ok(local) = std::env::var("LOCALAPPDATA") {
        let candidate = PathBuf::from(local)
            .join("Programs")
            .join("Ollama")
            .join("ollama.exe");
        if candidate.is_file() {
            return true;
        }
    }
    Command::new("where")
        .arg("ollama")
        .creation_flags(CREATE_NO_WINDOW)
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

fn ollama_exe() -> PathBuf {
    if let Ok(local) = std::env::var("LOCALAPPDATA") {
        let candidate = PathBuf::from(local)
            .join("Programs")
            .join("Ollama")
            .join("ollama.exe");
        if candidate.is_file() {
            return candidate;
        }
    }
    PathBuf::from("ollama")
}

/// Default Ollama model store: ``%USERPROFILE%\.ollama\models`` (see ``OLLAMA_MODELS``).
fn ollama_models_dir() -> PathBuf {
    if let Ok(path) = std::env::var("OLLAMA_MODELS") {
        return PathBuf::from(path);
    }
    std::env::var("USERPROFILE")
        .map(|home| PathBuf::from(home).join(".ollama").join("models"))
        .unwrap_or_else(|_| PathBuf::from(".ollama").join("models"))
}

fn install_ollama_models_from_zip(app: &tauri::AppHandle, launch_dir: &Path) -> Result<(), String> {
    let zip_path = launch_dir.join(OLLAMA_MODELS_ZIP);
    if !zip_path.is_file() {
        append_shell_log(
            app,
            "INFO",
            &format!(
                "No {} in {}; skipping offline Ollama models.",
                OLLAMA_MODELS_ZIP,
                launch_dir.display()
            ),
        );
        return Ok(());
    }

    let dest = ollama_models_dir();
    let roaming = install_home(app);
    let ollama_marker = roaming.join(PREREQS_BUNDLE_DIR);
    fs::create_dir_all(&ollama_marker).map_err(|e| e.to_string())?;
    let marker = ollama_marker.join(OLLAMA_OFFLINE_MODELS_MARKER);
    if !marker.is_file() && dest.join("manifests").join("registry.ollama.ai").join("ibm").is_dir() {
        fs::write(&marker, zip_path.to_string_lossy().as_bytes()).map_err(|e| e.to_string())?;
    }
    if marker.is_file() {
        append_shell_log(
            app,
            "INFO",
            &format!("Ollama models already installed under {}", dest.display()),
        );
        return Ok(());
    }

    set_splash_status(app, "Extracting Ollama models…");
    if let Some(parent) = dest.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    append_shell_log(
        app,
        "INFO",
        &format!(
            "Extracting {} -> {} (OLLAMA_MODELS)",
            zip_path.display(),
            dest.display()
        ),
    );
    extract_zip_to_dir(&zip_path, &dest)?;
    fs::write(&marker, zip_path.to_string_lossy().as_bytes()).map_err(|e| e.to_string())?;
    append_shell_log(
        app,
        "INFO",
        &format!("Offline Ollama models ready at {}", dest.display()),
    );
    Ok(())
}

fn ollama_models_env_value() -> String {
    ollama_models_dir().to_string_lossy().into_owned()
}

fn run_exe_installer(app: &tauri::AppHandle, installer: &Path, label: &str) -> Result<(), String> {
    append_shell_log(
        app,
        "INFO",
        &format!("Running {label}: {}", installer.display()),
    );
    let status = Command::new(installer)
        .args(["/SP-", "/VERYSILENT", "/NORESTART"])
        .creation_flags(CREATE_NO_WINDOW)
        .status()
        .map_err(|e| format!("Failed to start {label}: {e}"))?;
    if status.success() {
        Ok(())
    } else {
        Err(format!(
            "{label} exited with code {:?}",
            status.code()
        ))
    }
}

fn msi_exit_ok(code: Option<i32>) -> bool {
    matches!(code, Some(0) | Some(3010))
}

fn run_msi_install(
    app: &tauri::AppHandle,
    msi_path: &Path,
    label: &str,
    elevate: bool,
) -> Result<(), String> {
    append_shell_log(
        app,
        "INFO",
        &format!(
            "Installing {label}{}: {}",
            if elevate { " (elevated)" } else { "" },
            msi_path.display()
        ),
    );

    let status = if elevate {
        let msi = msi_path.to_string_lossy().replace('\'', "''");
        let ps = format!(
            "$p = Start-Process -FilePath msiexec.exe -ArgumentList @('/i','{msi}','/qn','/norestart') -Wait -PassThru -Verb RunAs; exit $p.ExitCode"
        );
        Command::new("powershell")
            .args([
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                &ps,
            ])
            .creation_flags(CREATE_NO_WINDOW)
            .status()
            .map_err(|e| format!("Failed to run elevated msiexec for {label}: {e}"))?
    } else {
        Command::new("msiexec")
            .args([
                "/i",
                &msi_path.to_string_lossy(),
                "/qn",
                "/norestart",
            ])
            .creation_flags(CREATE_NO_WINDOW)
            .status()
            .map_err(|e| format!("Failed to run msiexec for {label}: {e}"))?
    };

    if msi_exit_ok(status.code()) {
        Ok(())
    } else {
        Err(format!(
            "{label} MSI exited with code {:?}",
            status.code()
        ))
    }
}

fn run_winfsp_msi(app: &tauri::AppHandle, msi_path: &Path) -> Result<(), String> {
    if winfsp_installed() {
        append_shell_log(app, "INFO", "WinFSP already installed; skipping MSI.");
        return Ok(());
    }
    match run_msi_install(app, msi_path, "WinFSP", false) {
        Ok(()) => Ok(()),
        Err(e) if e.contains("1603") => {
            append_shell_log(
                app,
                "INFO",
                "WinFSP install needs administrator approval (UAC); retrying elevated…",
            );
            run_msi_install(app, msi_path, "WinFSP", true)
        }
        Err(e) => Err(e),
    }
}

fn extract_zip_to_dir(zip_path: &Path, dest: &Path) -> Result<(), String> {
    fs::create_dir_all(dest).map_err(|e| e.to_string())?;
    let dest = dest.to_path_buf();
    extract_zip_entries(zip_path, |relative| Some(dest.join(relative)))
}

fn run_postgres_setup(app: &tauri::AppHandle, bat_path: &Path) -> Result<(), String> {
    let work_dir = bat_path.parent().unwrap_or(Path::new("."));
    let script_file = format!("call {} & echo. & echo Exit code: %ERRORLEVEL%", bat_path.display());
    append_shell_log(
        app,
        "INFO",
        &format!(
            "Running PostgreSQL setup (work_dir): {} (script {})",
            work_dir.display(),
            script_file.to_string()
        ),
    );

    
    let status = Command::new("cmd.exe")
        .current_dir(work_dir)
        .args(["/c", &script_file])
        .creation_flags(CREATE_NO_WINDOW)
        .status()
        .map_err(|e| format!("Failed to run postgres setup.bat: {e}"))?;

    append_shell_log(
        app,
        if status.success() {
            "INFO"
        } else {
            "WARN"
        },
        &format!(
            "PostgreSQL setup.bat finished with status {:?}",
            status.code()
        ),
    );

    if !status.success() {
        return Err(format!(
            "setup.bat exited with code {:?}",
            status.code()
        ));
    }
    Ok(())
}

fn ensure_pre_reqs(app: &tauri::AppHandle) -> Result<(), String> {
    let Some(source) = read_registry_models_zip_source() else {
        append_shell_log(
            app,
            "WARN",
            "Skipping pre-reqs: ModelsZipSource not set (MSI launch folder).",
        );
        return Ok(());
    };

    let folder_root = resolve_pre_reqs_folder(&source);
    let source = normalize_models_zip_source(&source);
    let launch_dir = PathBuf::from(&source);

    if let Err(e) = install_ollama_models_from_zip(app, &launch_dir) {
        append_shell_log(app, "WARN", &format!("Offline Ollama models: {e}"));
    }

    let pre_reqs_zip = PRE_REQS_ZIP_NAMES
        .iter()
        .map(|name| launch_dir.join(name))
        .find(|path| path.is_file());

    if folder_root.is_none() && pre_reqs_zip.is_none() {
        append_shell_log(
            app,
            "INFO",
            &format!(
                "No pre-reqs in {} (expected {:?} folder or zip).",
                source, PRE_REQS_FOLDER_NAMES
            ),
        );
        return Ok(());
    }

    let roaming = install_home(app);
    let bundle_root = roaming.join(PREREQS_BUNDLE_DIR);
    let marker = bundle_root.join(PREREQS_SETUP_MARKER);
    

    if !marker.is_file() {
        set_splash_status(app, "Extracting prerequisites…");

        let prereqs_root = if let Some(ref folder) = folder_root {
            folder.clone()
        } else {
            if bundle_root.exists() {
                let _ = fs::remove_dir_all(&bundle_root);
            }
            let zip = pre_reqs_zip.as_ref().expect("pre_reqs_zip");
            append_shell_log(
                app,
                "INFO",
                &format!(
                    "Extracting pre-reqs {} -> {}",
                    zip.display(),
                    bundle_root.display()
                ),
            );
            fs::create_dir_all(&bundle_root).map_err(|e| e.to_string())?;
            extract_zip_to_dir(zip, &bundle_root)?;
            bundle_root.clone()
        };
        
        set_splash_status(app, "Installing prerequisites (Ollama)…");
        if let Some(ollama_setup) = find_file_in_tree(&prereqs_root, &[OLLAMA_SETUP_EXE]) {
            if ollama_installed() {
                append_shell_log(app, "INFO", "Ollama already installed; skipping setup.");
            } else if let Err(e) = run_exe_installer(app, &ollama_setup, "OllamaSetup") {
                append_shell_log(app, "WARN", &e);
            }
            let _ = fs::remove_file(&ollama_setup);
        }

        set_splash_status(app, "Installing prerequisites (WinFSP)…");
        if let Some(msi) = find_file_in_tree(&prereqs_root, &WINFSP_MSI_NAME) {
            if let Err(e) = run_winfsp_msi(app, &msi) {
                append_shell_log(app, "WARN", &e);
            }
            let _ = fs::remove_file(&msi);
        }
        let postgres_zip = prereqs_root.join(POSTGRES_ZIP_NAME);
        append_shell_log(
            app,
            "INFO",
            &format!("extract postgres_zip: {}", postgres_zip.display()),
        );
        extract_zip_to_dir(&postgres_zip, &roaming.join("postgres"))?;
        let _ = fs::remove_file(&postgres_zip);
        fs::write(&marker, b"pre-reqs installed ok").map_err(|e| e.to_string())?;
    }

    set_splash_status(app, "DB startup…");
    let postgres_bat_file = roaming.join("postgres").join(POSTGRES_SETUP_BAT);
    append_shell_log(
        app,
        "INFO",
        &format!("run postgres startup: {}", postgres_bat_file.display()),
    );

    run_postgres_setup(app, &postgres_bat_file)?;

    Ok(())
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

fn extract_models_zip(zip_path: &Path, backend_root: &Path) -> Result<(), String> {
    let internal = backend_internal_dir(backend_root);
    fs::create_dir_all(&internal).map_err(|e| e.to_string())?;
    let target = internal.clone();
    extract_zip_entries(zip_path, move |relative| {
        let name = relative.to_string_lossy().replace('\\', "/");
        let name = name.trim_start_matches("./");
        name.strip_prefix("backend/_internal/")
            .map(|rest| target.join(rest))
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
            "ONNX models missing and no ModelsZipSource in registry (MSI launch folder; set during install).",
        );
        return Ok(());
    };

    let launch_dir = PathBuf::from(normalize_models_zip_source(&source));
    let zip_path = launch_dir.join(ONNX_MODELS_ZIP);
    if !zip_path.is_file() {
        return Err(format!(
            "{} not found next to MSI launch folder: {}",
            ONNX_MODELS_ZIP,
            zip_path.display()
        ));
    }

    set_splash_status(
        app,
        "This may take a few minutes. Extracting models...",
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
            "{} was extracted but expected ONNX files were not found (e.g. {}). \
             Zip entries must start with backend/_internal/.",
             ONNX_MODELS_ZIP,
            expected.display()
        ));
    }
    Ok(())
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

    let zip_path = cached_backend_zip_path(&home);
   

    append_shell_log(
        app,
        "INFO",
        &format!("Extracting {} -> {}", zip_path.display(), home.display()),
    );

    extract_backend_zip(&zip_path, &home)?;

    resolve_backend_root(&home).ok_or_else(|| {
        format!(
            "backend.zip was extracted but no backend executable was found under {}.",
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

fn services_already_running() -> bool {
    backend_http_ready() && frontend_http_ready()
}

fn wait_for_backend(app: &tauri::AppHandle) {
    set_splash_status(app, "RescueBox Server startup…");
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
    let path = install_home(app)
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

/// Eastern Time (America/New_York — EST/EDT) for shell log lines.
fn chrono_lite_timestamp() -> String {
    use chrono_tz::America::New_York;
    chrono::Utc::now()
        .with_timezone(&New_York)
        .format("%Y-%m-%d %H:%M:%S %Z")
        .to_string()
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

fn notify_error(app: &tauri::AppHandle, title: impl Into<String>, message: impl Into<String>) {
    notify_user(app, title, message, MessageDialogKind::Error);
}

/// Python log lines on stderr are not errors; map ``[DEBUG]`` / ``[INFO]`` / … to shell log level.
fn infer_sidecar_log_level(line: &str) -> &'static str {
    if line.contains("[CRITICAL]") || line.contains("[ERROR]") {
        "ERROR"
    } 
    else {
        "INFO"
    }
}

fn log_sidecar_line(app: &tauri::AppHandle, sidecar: &str, text: &str) {
    let trimmed = text.trim_end_matches(['\r', '\n']);
    if trimmed.is_empty() {
        return;
    }
    let level = infer_sidecar_log_level(trimmed);
    append_shell_log(app, level, &format!("{sidecar} — {trimmed}"));
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
        let roaming = install_home(app);
        let postgres_bat_file = roaming.join("postgres").join("stop.bat");
        let work_dir = roaming.join("postgres");
        let script_file = format!("call {} & echo. & echo Exit code: %ERRORLEVEL%", postgres_bat_file.display());
        let _ =  Command::new("cmd.exe")
        .creation_flags(CREATE_NO_WINDOW)
        .current_dir(work_dir)
        .args(["/c", &script_file])
        .status();
    }
}

fn shutdown_app(app: &tauri::AppHandle) {
    kill_sidecars(app);
    app.exit(0);
}

#[tauri::command]
fn open_ui_url(url: Option<String>) {
    open_system_browser(url.as_deref().unwrap_or(UI_URL));
}

#[tauri::command]
fn set_quit_on_close(state: tauri::State<'_, AppState>, quit: bool) {
    state.quit_on_close.store(quit, Ordering::SeqCst);
}

fn open_system_browser(url: &str) {
    #[cfg(target_os = "windows")]
    {
        let _ = Command::new("cmd")
            .args(["/C", "start", "", url])
            .creation_flags(CREATE_NO_WINDOW)
            .spawn();
    }
    #[cfg(target_os = "macos")]
    {
        let _ = Command::new("open").arg(url).spawn();
    }
    #[cfg(all(not(target_os = "windows"), not(target_os = "macos")))]
    {
        let _ = Command::new("xdg-open").arg(url).spawn();
    }
}

/// Splash ready state: link + quit checkbox (Flow A or B).
fn present_splash_ready(app: &tauri::AppHandle, already_running: bool, open_browser: bool) {
    app.state::<AppState>()
        .quit_on_close
        .store(false, Ordering::SeqCst);

    if open_browser {
        open_system_browser(UI_URL);
    }

    if let Ok(json) = serde_json::to_string(&serde_json::json!({
        "url": UI_URL,
        "alreadyRunning": already_running,
    })) {
        run_splash_js(app, format!("window.setStartupReady?.({json});"));
    } else {
        set_splash_status(app, &format!("Open {UI_URL} in your web browser."));
    }

    if already_running {
        append_shell_log(app, "INFO", "RescueBox already running; showing launcher.");
    } else {
        append_shell_log(
            app,
            "INFO",
            &format!("Opened default browser at {UI_URL}"),
        );
    }
}

fn finish_startup_for_browser(app: &tauri::AppHandle) {
    present_splash_ready(app, false, true);
}

fn show_manager_splash(app: &tauri::AppHandle) {
    show_splash_screen(app);
    present_splash_ready(app, true, false);
}

fn spawn_sidecars(app: &tauri::AppHandle) -> bool {

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
    if let Err(e) = ensure_pre_reqs(app) {
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
    set_splash_status(app, "Starting backend server…");

    let ollama_models = ollama_models_env_value();

    let (mut rx_backend, child_backend) = match app
        .shell()
        .command(backend_exe.to_str().unwrap())
        .current_dir(backend_path.clone())
        .env("PYTHONPATH", backend_path.to_str().unwrap())
        .env("NO_PROXY", "127.0.0.1,localhost")
        .env("OLLAMA_HOST", "http://127.0.0.1:11434")
        .env("OLLAMA_MODELS", &ollama_models)
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

    let local_data = app
        .path()
        .app_local_data_dir()
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
        .env("OLLAMA_MODELS", &ollama_models)
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
                    log_sidecar_line(&app_fe, "Frontend", &text);
                }
                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                    let text = String::from_utf8_lossy(&line).into_owned();
                    log_sidecar_line(&app_fe, "Frontend", &text);
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
                    log_sidecar_line(&app_be, "Backend", &text);
                }
                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                    let text = String::from_utf8_lossy(&line).into_owned();
                    log_sidecar_line(&app_be, "Backend", &text);
                }
                _ => {}
            }
        }
    });

    wait_for_backend(app);
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
    if let Some(splash) = app.get_webview_window("splashscreen") {
        let _ = splash.show();
        let _ = splash.set_focus();
    }
}

fn schedule_app_startup(app_handle: tauri::AppHandle) {
    let state = app_handle.state::<AppState>();
    if state
        .startup_scheduled
        .swap(true, Ordering::SeqCst)
    {
        return;
    }

    set_splash_status(&app_handle, "Initializing…");

    tauri::async_runtime::spawn(async move {
        if services_already_running() {
            let handle = app_handle.clone();
            let _ = app_handle.run_on_main_thread(move || {
                show_manager_splash(&handle);
            });
            return;
        }

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
            finish_startup_for_browser(&handle);
        });
    });
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _argv, _cwd| {
            let handle = app.clone();
            let _ = app.run_on_main_thread(move || {
                show_manager_splash(&handle);
            });
        }))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![open_ui_url, set_quit_on_close])
        .manage(AppState {
            frontend: Mutex::new(None),
            backend: Mutex::new(None),
            closing_splash_for_main: AtomicBool::new(false),
            quit_on_close: AtomicBool::new(false),
            startup_scheduled: AtomicBool::new(false),
            shell_log_path: Mutex::new(None),
        })
        .on_page_load(|webview, payload| {
            if webview.label() != "splashscreen" {
                return;
            }
            if payload.event() != PageLoadEvent::Finished {
                return;
            }
            schedule_app_startup(webview.app_handle().clone());
        })
        .setup(|app| {
            show_splash_screen(app.handle());
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                let app = window.app_handle();
                let label = window.label();

                if label == "splashscreen" {
                    let state = app.state::<AppState>();
                    if state.closing_splash_for_main.load(Ordering::SeqCst) {
                        return;
                    }
                    if state.quit_on_close.load(Ordering::SeqCst) {
                        shutdown_app(&app);
                    } else {
                        api.prevent_close();
                        let _ = window.hide();
                    }
                    return;
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
