use std::path::PathBuf;
use tauri::{AppHandle, Emitter, Manager};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command;

#[tauri::command]
fn resolve_data_dir(app: tauri::AppHandle) -> String {
    // 1. User-configured path in .env (DATA_DIR key)
    if let Ok(content) = std::fs::read_to_string(env_path()) {
        for line in content.lines() {
            let t = line.trim();
            if t.starts_with("DATA_DIR=") {
                let v = t["DATA_DIR=".len()..].trim().trim_matches('"');
                if !v.is_empty() {
                    let p = PathBuf::from(v);
                    if p.exists() { return p.to_string_lossy().to_string(); }
                    // path configured but not yet created — return as-is so crawler can create it
                    return v.to_string();
                }
            }
        }
    }
    // 2. Dev repo path
    let dev = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../data/runs/servidores");
    if let Ok(resolved) = dev.canonicalize() {
        if resolved.exists() { return resolved.to_string_lossy().to_string(); }
    }
    // 3. App local data dir (installed app, first run)
    app.path().app_local_data_dir()
        .unwrap_or_default()
        .join("servidores")
        .to_string_lossy()
        .to_string()
}

fn resolve_node_bin() -> String {
    #[cfg(target_os = "windows")]
    let candidates: &[&str] = &[
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
    ];
    #[cfg(not(target_os = "windows"))]
    let candidates: &[&str] = &[
        "/opt/homebrew/bin/node",
        "/usr/local/bin/node",
        "/usr/bin/node",
    ];
    for c in candidates {
        if std::path::Path::new(c).exists() {
            return c.to_string();
        }
    }
    "node".to_string()
}

fn resolve_crawler_sidecar() -> Option<PathBuf> {
    #[cfg(debug_assertions)]
    return None; // dev mode: always use node + cli.js

    #[cfg(not(debug_assertions))]
    {
        let ext = if cfg!(windows) { ".exe" } else { "" };
        if let Ok(exe) = std::env::current_exe() {
            if let Some(dir) = exe.parent() {
                let sidecar = dir.join(format!("crawler{}", ext));
                if sidecar.exists() { return Some(sidecar); }
            }
        }
        None
    }
}

#[tauri::command]
async fn run_crawler(app: AppHandle, extra_args: Vec<String>) -> Result<(), String> {
    let base = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let cli      = base.join("../src-crawler/cli.js");
    let yaml     = base.join("../../servidores.yaml");
    let env_file = env_path();

    // output-dir for the crawler is the parent of the servidores dir
    // resolve_data_dir returns .../data/runs/servidores → parent = .../data/runs
    let servidores_dir = resolve_data_dir(app.clone());
    let output_dir = PathBuf::from(&servidores_dir)
        .parent()
        .map(|p| p.to_path_buf())
        .unwrap_or_else(|| base.join("../../data/runs"));

    let (bin, mut args) = if let Some(sidecar) = resolve_crawler_sidecar() {
        (sidecar.to_string_lossy().to_string(), vec![])
    } else {
        let node = resolve_node_bin();
        (node, vec![cli.to_string_lossy().to_string()])
    };

    if extra_args.is_empty() {
        args.extend(["batch", "--file"].map(String::from));
        args.push(yaml.to_string_lossy().to_string());
        args.extend(["--output-dir"].map(String::from));
        args.push(output_dir.to_string_lossy().to_string());
        args.extend(["--env-file"].map(String::from));
        args.push(env_file.to_string_lossy().to_string());
    } else {
        args.extend(extra_args);
    }

    let expanded_path = format!(
        "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:{}",
        std::env::var("PATH").unwrap_or_default()
    );

    let mut child = Command::new(&bin)
        .args(&args)
        .env("PATH", &expanded_path)
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .map_err(|e| format!("Falha ao iniciar crawler ({bin}): {e}"))?;

    let stdout = child.stdout.take().unwrap();
    let stderr = child.stderr.take().unwrap();

    let app_out = app.clone();
    let app_err = app.clone();

    let out_task = tokio::spawn(async move {
        let mut lines = BufReader::new(stdout).lines();
        while let Ok(Some(line)) = lines.next_line().await {
            let _ = app_out.emit("crawler-log", line);
        }
    });

    let err_task = tokio::spawn(async move {
        let mut lines = BufReader::new(stderr).lines();
        while let Ok(Some(line)) = lines.next_line().await {
            let _ = app_err.emit("crawler-log", format!("[err] {line}"));
        }
    });

    let status = child.wait().await.map_err(|e| e.to_string())?;
    let _ = out_task.await;
    let _ = err_task.await;
    let code = status.code().unwrap_or(-1);
    let _ = app.emit("crawler-done", code);
    Ok(())
}

fn env_path() -> PathBuf {
    let p = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../.env");
    p.canonicalize().unwrap_or(p)
}

fn servidores_path() -> PathBuf {
    let p = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../servidores.yaml");
    p.canonicalize().unwrap_or(p)
}

#[tauri::command]
fn get_config_paths() -> serde_json::Value {
    serde_json::json!({
        "env_path": env_path().to_string_lossy(),
        "servidores_path": servidores_path().to_string_lossy(),
    })
}

#[tauri::command]
fn read_env_file() -> Result<String, String> {
    std::fs::read_to_string(env_path()).map_err(|e| e.to_string())
}

#[tauri::command]
fn write_env_file(content: String) -> Result<(), String> {
    std::fs::write(env_path(), content).map_err(|e| e.to_string())
}

#[tauri::command]
fn read_servidores_file() -> Result<String, String> {
    std::fs::read_to_string(servidores_path()).map_err(|e| e.to_string())
}

#[tauri::command]
fn write_servidores_file(content: String) -> Result<(), String> {
    std::fs::write(servidores_path(), content).map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            resolve_data_dir, run_crawler,
            get_config_paths,
            read_env_file, write_env_file,
            read_servidores_file, write_servidores_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
