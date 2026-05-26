use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use tauri::{AppHandle, Emitter, Manager};

#[tauri::command]
fn resolve_data_dir(app: tauri::AppHandle) -> String {
    let candidates = vec![
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../data/runs/servidores"),
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
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../data/runs/servidores")
        .to_string_lossy()
        .to_string()
}

#[tauri::command]
fn run_crawler(app: AppHandle, extra_args: Vec<String>) -> Result<(), String> {
    let cli = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../src-crawler/cli.js");
    let yaml = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../servidores.yaml");
    let output_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../data/runs");

    let mut args = vec![
        cli.to_string_lossy().to_string(),
    ];
    if extra_args.is_empty() {
        args.push("batch".to_string());
        args.push("--file".to_string());
        args.push(yaml.to_string_lossy().to_string());
        args.push("--output-dir".to_string());
        args.push(output_dir.to_string_lossy().to_string());
    } else {
        args.extend(extra_args);
    }

    let mut child = Command::new("node")
        .args(&args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Falha ao iniciar node: {e}"))?;

    let stdout = child.stdout.take().unwrap();
    let stderr = child.stderr.take().unwrap();

    let app_out = app.clone();
    std::thread::spawn(move || {
        for line in BufReader::new(stdout).lines().map_while(Result::ok) {
            let _ = app_out.emit("crawler-log", line);
        }
    });

    let app_err = app.clone();
    std::thread::spawn(move || {
        for line in BufReader::new(stderr).lines().map_while(Result::ok) {
            let _ = app_err.emit("crawler-log", format!("[err] {line}"));
        }
    });

    let status = child.wait().map_err(|e| e.to_string())?;
    let code = status.code().unwrap_or(-1);
    let _ = app.emit("crawler-done", code);
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![resolve_data_dir, run_crawler])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
