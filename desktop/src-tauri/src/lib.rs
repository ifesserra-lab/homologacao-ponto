use std::path::PathBuf;

#[tauri::command]
fn resolve_data_dir(app: tauri::AppHandle) -> String {
    // In dev: binary cwd is desktop/src-tauri → ../../../data/runs/servidores
    // In production: use app resource dir as anchor
    let candidates = vec![
        // dev: navigate from src-tauri/target/debug/ up to project root
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../data/runs/servidores"),
        // fallback: app local data dir
        app.path().app_local_data_dir()
            .unwrap_or_default()
            .join("servidores"),
    ];

    for candidate in candidates {
        if let Ok(resolved) = candidate.canonicalize() {
            if resolved.exists() {
                return resolved.to_string_lossy().to_string();
            }
        }
    }

    // Return the dev path even if it doesn't exist yet — user sees it
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../data/runs/servidores")
        .to_string_lossy()
        .to_string()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![resolve_data_dir])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
