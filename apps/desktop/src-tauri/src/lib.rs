//! LVPP Studio desktop shell.
//!
//! Wraps the web UI and exposes the shell plugin so the frontend can launch
//! local helper processes (backend, ComfyUI) with user consent via capabilities.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .run(tauri::generate_context!())
        .expect("error while running LVPP Studio");
}
