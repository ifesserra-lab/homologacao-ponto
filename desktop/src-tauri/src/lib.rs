use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Emitter, Manager};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command;

// ── Config structs ────────────────────────────────────────────────────────────

#[derive(Serialize, Deserialize, Default, Clone)]
struct AppConfig {
    #[serde(default)]
    dados: DadosConfig,
    #[serde(default)]
    sigrh: SigrhConfig,
    #[serde(default)]
    app: AppLoginConfig,
    #[serde(default)]
    homologacao: HomologacaoConfig,
    #[serde(default)]
    chefia: ChefiaConfig,
}

#[derive(Serialize, Deserialize, Default, Clone)]
struct ChefiaConfig {
    #[serde(default)]
    setor: String,
}

#[derive(Serialize, Deserialize, Default, Clone)]
struct DadosConfig {
    #[serde(default)]
    pasta: String,
}

#[derive(Serialize, Deserialize, Default, Clone)]
struct SigrhConfig {
    #[serde(default)]
    usuario: String,
    #[serde(default)]
    senha: String,
}

#[derive(Serialize, Deserialize, Default, Clone)]
struct AppLoginConfig {
    #[serde(default)]
    usuario_hash: String,
    #[serde(default)]
    senha_hash: String,
}

fn default_politica_he() -> String { "manual".to_string() }

#[derive(Serialize, Deserialize, Clone)]
struct HomologacaoConfig {
    #[serde(default = "default_politica_he")]
    politica_he: String,
}
impl Default for HomologacaoConfig {
    fn default() -> Self { Self { politica_he: default_politica_he() } }
}

fn config_path() -> PathBuf {
    let p = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../configuration.yaml");
    p.canonicalize().unwrap_or(p)
}

fn read_app_config() -> AppConfig {
    std::fs::read_to_string(config_path())
        .ok()
        .and_then(|s| serde_yaml::from_str(&s).ok())
        .unwrap_or_default()
}

// ── Tauri commands ────────────────────────────────────────────────────────────

#[tauri::command]
fn get_config_path() -> String {
    config_path().to_string_lossy().to_string()
}

#[tauri::command]
fn read_config_file() -> Result<String, String> {
    std::fs::read_to_string(config_path()).map_err(|e| e.to_string())
}

#[tauri::command]
fn write_config_file(content: String) -> Result<(), String> {
    let path = config_path();
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    std::fs::write(path, content).map_err(|e| e.to_string())
}

#[tauri::command]
fn get_app_auth() -> serde_json::Value {
    let cfg = read_app_config();
    serde_json::json!({
        "usuario_hash": cfg.app.usuario_hash,
        "senha_hash": cfg.app.senha_hash,
    })
}

#[tauri::command]
fn resolve_data_dir(app: tauri::AppHandle) -> String {
    let cfg = read_app_config();
    if !cfg.dados.pasta.is_empty() {
        // dados.pasta is the root dir chosen by the user.
        // The frontend reads the servidores subdirectory.
        return PathBuf::from(&cfg.dados.pasta)
            .join("servidores")
            .to_string_lossy()
            .to_string();
    }
    let dev = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../data/runs/servidores");
    if let Ok(resolved) = dev.canonicalize() {
        if resolved.exists() { return resolved.to_string_lossy().to_string(); }
    }
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
        if std::path::Path::new(c).exists() { return c.to_string(); }
    }
    "node".to_string()
}

fn resolve_crawler_sidecar() -> Option<PathBuf> {
    #[cfg(debug_assertions)]
    return None;

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
async fn run_crawler(app: AppHandle, command: Option<String>, extra_args: Vec<String>) -> Result<(), String> {
    let base = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let cli  = base.join("../src-crawler/cli.js");
    let yaml = base.join("../../servidores.yaml");

    let cfg = read_app_config();
    // output_dir is the root folder; crawler writes to output_dir/servidores/<slug>/
    let output_dir = if !cfg.dados.pasta.is_empty() {
        PathBuf::from(&cfg.dados.pasta)
    } else {
        base.join("../../data/runs")
    };

    let (bin, mut args) = if let Some(sidecar) = resolve_crawler_sidecar() {
        (sidecar.to_string_lossy().to_string(), vec![])
    } else {
        let node = resolve_node_bin();
        (node, vec![cli.to_string_lossy().to_string()])
    };

    let cmd = command.as_deref().unwrap_or("batch");
    args.push(cmd.to_string());
    args.extend(["--file".to_string(), yaml.to_string_lossy().to_string()]);
    args.extend(["--output-dir".to_string(), output_dir.to_string_lossy().to_string()]);
    if !extra_args.is_empty() {
        args.extend(extra_args);
    }

    let expanded_path = format!(
        "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:{}",
        std::env::var("PATH").unwrap_or_default()
    );

    let mut child = Command::new(&bin)
        .args(&args)
        .env("PATH", &expanded_path)
        .env("SIGRH_USERNAME", &cfg.sigrh.usuario)
        .env("SIGRH_PASSWORD", &cfg.sigrh.senha)
        .env("POLITICA_HE", &cfg.homologacao.politica_he)
        .env("CHEFIA_SETOR", &cfg.chefia.setor)
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

fn servidores_path() -> PathBuf {
    let p = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../servidores.yaml");
    p.canonicalize().unwrap_or(p)
}

#[tauri::command]
fn get_config_paths() -> serde_json::Value {
    serde_json::json!({
        "config_path": config_path().to_string_lossy(),
        "servidores_path": servidores_path().to_string_lossy(),
    })
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
            resolve_data_dir,
            run_crawler,
            get_config_path,
            get_config_paths,
            get_app_auth,
            read_config_file,
            write_config_file,
            read_servidores_file,
            write_servidores_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
