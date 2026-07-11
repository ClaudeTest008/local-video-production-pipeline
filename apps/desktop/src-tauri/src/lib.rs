//! LVPP Studio desktop shell.
//!
//! Spawns the bundled backend (PyInstaller sidecar) on launch, waits for it to
//! come up, and kills it on exit. The web UI (static export) talks to it on
//! 127.0.0.1:8321.

use std::sync::Mutex;

use tauri::{Manager, RunEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

struct BackendChild(Mutex<Option<CommandChild>>);

fn spawn_backend(app: &tauri::AppHandle) {
    match app.shell().sidecar("lvpp-backend") {
        Ok(cmd) => match cmd
            .args(["--parent-pid", &std::process::id().to_string()])
            .spawn()
        {
            Ok((_rx, child)) => {
                app.state::<BackendChild>().0.lock().unwrap().replace(child);
            }
            Err(e) => eprintln!("backend spawn failed: {e} — start it manually on :8321"),
        },
        Err(e) => eprintln!("backend sidecar missing: {e} (dev mode? run uvicorn yourself)"),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendChild(Mutex::new(None)))
        .setup(|app| {
            spawn_backend(app.handle());
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building LVPP Studio")
        .run(|app, event| {
            if let RunEvent::Exit = event {
                if let Some(child) = app.state::<BackendChild>().0.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        });
}
