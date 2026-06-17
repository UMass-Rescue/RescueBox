#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

// 1. Define the AppState struct at the top level
struct AppState {
    frontend: Mutex<Option<CommandChild>>,
    backend: Mutex<Option<CommandChild>>,
}

fn main() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    // 2. Register the state management before setup
    .manage(AppState {
        frontend: Mutex::new(None),
        backend: Mutex::new(None),
    })
    .setup(|app| {
      let resource_path = app.path().resource_dir()
        .expect("failed to get resource dir");
      let frontend_path = resource_path.join("frontend");
      let backend_path = resource_path.join("backend");

      // Explicitly point to the executable inside the dependency folder
      let frontend_exe = frontend_path.join("frontend-x86_64-pc-windows-msvc.exe");
      let backend_exe = backend_path.join("rescuebox-x86_64-pc-windows-msvc.exe");
        
      // Ask Tauri for the system's local AppData directory
      let local_data = app.path().local_data_dir()
        .expect("failed to get local data dir")
        .join("RescueBox-Desktop");

      // --- START FRONTEND SIDECAR ---
      let sidecar_command = app.shell()
        .command(frontend_exe.to_str().unwrap());
        
      // Renamed _child to child so we can save it to state
      let (mut rx, child) = sidecar_command
        .current_dir(frontend_path.clone())
        .env("PYTHONPATH", frontend_path.to_str().unwrap())
        .env("NICEGUI_STORAGE_PATH", local_data.join("nicegui").to_str().unwrap())
        .env("UVICORN_LOG_CONFIG", "")
        .env("NO_PROXY", "127.0.0.1,localhost")
        // FORCE OLLAMA TO USE IPv4:
        .env("OLLAMA_HOST", "http://127.0.0.1:11434")
        .env("RESCUEBOX_HOME", resource_path.join("demo").to_str().unwrap())
        .spawn()
        .expect("Failed to spawn sidecar");

      // --- START BACKEND SIDECAR ---
      let backend_sidecar = app.shell()
        .command(backend_exe.to_str().unwrap());

      // Renamed _child_backend to child_backend so we can save it to state
      let (mut rx_backend, child_backend) = backend_sidecar
        .current_dir(backend_path.clone())
        .env("PYTHONPATH", backend_path.to_str().unwrap())
        // INJECT CACHE VARIABLES HERE:
        .env("MPLCONFIGDIR", local_data.join("matplotlib").to_str().unwrap())
        .env("XDG_CACHE_HOME", local_data.join("xdg_cache").to_str().unwrap())
        .env("NO_PROXY", "127.0.0.1,localhost")
        // FORCE OLLAMA TO USE IPv4:
        .env("OLLAMA_HOST", "http://127.0.0.1:11434")
        .env("RESCUEBOX_HOME", resource_path.to_str().unwrap())
        .spawn()
        .expect("Failed to spawn backend sidecar");

      // 3. Save the processes to the managed state so they can be killed later
      let state = app.state::<AppState>();
      *state.frontend.lock().unwrap() = Some(child);
      *state.backend.lock().unwrap() = Some(child_backend);

      // --- ASYNC LOGGERS ---
      tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
          match event {
            tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                println!("Frontend STDOUT: {}", String::from_utf8_lossy(&line));
            }
            tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                eprintln!("Frontend STDERR: {}", String::from_utf8_lossy(&line));
            }
            _ => {}
          }
        }
      });

      tauri::async_runtime::spawn(async move {
        while let Some(event) = rx_backend.recv().await {
          match event {
            tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                println!("Backend STDOUT: {}", String::from_utf8_lossy(&line));
            }
            tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                eprintln!("Backend STDERR: {}", String::from_utf8_lossy(&line));
            }
            _ => {}
          }
        }
      });

      Ok(())
    })
    .on_window_event(|window, event| {
      if let tauri::WindowEvent::CloseRequested { .. } = event {
        // This ensures the entire app (and children) shut down 
        // when the user clicks the 'X'
        println!("Cleaning up RescueBox processes...");
        let state = window.state::<AppState>();

        // 4. Explicitly kill the background processes when the UI closes
        if let Some(child) = state.frontend.lock().unwrap().take() {
            let _ = child.kill();
        }
        if let Some(child) = state.backend.lock().unwrap().take() {
            let _ = child.kill();
        }
        window.app_handle().exit(0); 
      }
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}