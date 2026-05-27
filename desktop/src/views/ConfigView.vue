<script setup lang="ts">
import { ref, onMounted } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import yaml from "js-yaml";
import { useAuthStore } from "@/stores/auth";
import { useServidoresStore } from "@/stores/servidores";
import TabNav from "@/components/TabNav.vue";
import ThemeToggle from "@/components/ThemeToggle.vue";

const auth = useAuthStore();
const servidoresStore = useServidoresStore();
const activeTab = ref<"credenciais" | "dados" | "servidores">("credenciais");

// ── Pasta de dados ───────────────────────────────────────────
const dataDir = ref("");
const dataDirSaving = ref(false);
const dataDirMsg = ref<{ ok: boolean; text: string } | null>(null);

async function loadDataDir() {
  dataDir.value = await invoke<string>("resolve_data_dir");
}

async function pickDataDir() {
  const selected = await openDialog({ directory: true, multiple: false, title: "Selecionar pasta de dados" });
  if (selected && typeof selected === "string") dataDir.value = selected;
}

async function saveDataDir() {
  dataDirSaving.value = true; dataDirMsg.value = null;
  try {
    let content = await invoke<string>("read_env_file");
    content = updateEnvKey(content, "DATA_DIR", dataDir.value.trim());
    await invoke("write_env_file", { content });
    await servidoresStore.load();
    dataDirMsg.value = { ok: true, text: "✓ Pasta salva e dados recarregados" };
  } catch (e) { dataDirMsg.value = { ok: false, text: `Erro: ${e}` }; }
  finally { dataDirSaving.value = false; }
}

const envPath = ref("");
const servidoresPath = ref("");

// ── Credenciais ──────────────────────────────────────────────
const username = ref("");
const password = ref("");
const showPass = ref(false);
const credSaving = ref(false);
const credMsg = ref<{ ok: boolean; text: string } | null>(null);

// ── Servidores ───────────────────────────────────────────────
interface Servidor { nome: string; siape: string }
const servidores = ref<Servidor[]>([]);
const anosInput = ref("");
const novoNome = ref("");
const novoSiape = ref("");
const servSaving = ref(false);
const servMsg = ref<{ ok: boolean; text: string } | null>(null);

onMounted(async () => {
  const paths = await invoke<{ env_path: string; servidores_path: string }>("get_config_paths");
  envPath.value = paths.env_path;
  servidoresPath.value = paths.servidores_path;
  await loadCredenciais();
  await loadServidores();
  await loadDataDir();
});

// ── .env helpers ─────────────────────────────────────────────
function updateEnvKey(content: string, key: string, value: string): string {
  const lines = content.split("\n");
  const idx = lines.findIndex(l => l.trim().startsWith(key + "="));
  if (idx >= 0) { lines[idx] = `${key}=${value}`; }
  else { lines.push(`${key}=${value}`); }
  return lines.join("\n");
}

async function loadCredenciais() {
  try {
    const content = await invoke<string>("read_env_file");
    for (const line of content.split("\n")) {
      const t = line.trim();
      if (!t || t.startsWith("#") || !t.includes("=")) continue;
      const eq = t.indexOf("=");
      const k = t.slice(0, eq).trim();
      const v = t.slice(eq + 1).trim();
      if (k === "SIGRH_USERNAME") username.value = v;
      if (k === "SIGRH_PASSWORD") password.value = v;
    }
  } catch (e) { credMsg.value = { ok: false, text: `Erro ao ler .env: ${e}` }; }
}

async function saveCredenciais() {
  credSaving.value = true; credMsg.value = null;
  try {
    let content = await invoke<string>("read_env_file");
    content = updateEnvKey(content, "SIGRH_USERNAME", username.value.trim());
    content = updateEnvKey(content, "SIGRH_PASSWORD", password.value);
    await invoke("write_env_file", { content });
    credMsg.value = { ok: true, text: "✓ Credenciais salvas" };
  } catch (e) { credMsg.value = { ok: false, text: `Erro: ${e}` }; }
  finally { credSaving.value = false; }
}

// ── servidores.yaml helpers ───────────────────────────────────
async function loadServidores() {
  try {
    const content = await invoke<string>("read_servidores_file");
    const parsed = yaml.load(content) as any;
    servidores.value = (parsed?.servidores ?? []).map((s: any) => ({
      nome: String(s.nome ?? ""),
      siape: String(s.siape ?? ""),
    }));
    const anos = parsed?.anos;
    anosInput.value = Array.isArray(anos) ? anos.join(", ") : String(anos ?? new Date().getFullYear());
  } catch (e) { servMsg.value = { ok: false, text: `Erro ao ler servidores.yaml: ${e}` }; }
}

function addServidor() {
  const nome = novoNome.value.trim().toUpperCase();
  const siape = novoSiape.value.trim();
  if (!nome || !siape) return;
  if (servidores.value.some(s => s.siape === siape)) {
    servMsg.value = { ok: false, text: `SIAPE ${siape} já cadastrado` }; return;
  }
  servidores.value.push({ nome, siape });
  novoNome.value = ""; novoSiape.value = "";
  servMsg.value = null;
}

function removeServidor(i: number) { servidores.value.splice(i, 1); }

async function saveServidores() {
  servSaving.value = true; servMsg.value = null;
  try {
    const anos = anosInput.value.split(/[,\s]+/).map(s => parseInt(s)).filter(n => !isNaN(n));
    const data = { anos, servidores: servidores.value.map(s => ({ nome: s.nome, siape: s.siape })) };
    await invoke("write_servidores_file", { content: yaml.dump(data, { indent: 2, lineWidth: -1 }) });
    servMsg.value = { ok: true, text: "✓ servidores.yaml salvo" };
  } catch (e) { servMsg.value = { ok: false, text: `Erro: ${e}` }; }
  finally { servSaving.value = false; }
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-row">
        <div>
          <h1 class="page-title">Configurações</h1>
          <p class="page-meta">Credenciais SIGRH · Servidores cadastrados</p>
        </div>
        <div class="nav-actions">
          <ThemeToggle />
          <button class="logout-btn" type="button" @click="auth.logout(); $router.push('/login')">Sair</button>
        </div>
      </div>
    </header>

    <TabNav />

    <div class="config-tabs">
      <button :class="['ctab', activeTab === 'credenciais' && 'ctab--active']" @click="activeTab = 'credenciais'">
        Credenciais SIGRH
      </button>
      <button :class="['ctab', activeTab === 'dados' && 'ctab--active']" @click="activeTab = 'dados'">
        Pasta de Dados
      </button>
      <button :class="['ctab', activeTab === 'servidores' && 'ctab--active']" @click="activeTab = 'servidores'">
        Servidores ({{ servidores.length }})
      </button>
    </div>

    <!-- ── Credenciais ── -->
    <div v-if="activeTab === 'credenciais'" class="card">
      <p class="card-hint">Credenciais usadas pelo crawler para acessar o SIGRH.</p>

      <div class="field">
        <label>Usuário SIGRH</label>
        <input v-model="username" type="text" autocomplete="off" placeholder="ex: 1234567" />
      </div>

      <div class="field">
        <label>Senha SIGRH</label>
        <div class="pass-wrap">
          <input v-model="password" :type="showPass ? 'text' : 'password'" autocomplete="off" placeholder="••••••••" />
          <button type="button" class="btn-toggle-pass" @click="showPass = !showPass">
            {{ showPass ? 'Ocultar' : 'Mostrar' }}
          </button>
        </div>
      </div>

      <div class="actions">
        <button class="btn-save" :disabled="credSaving" @click="saveCredenciais">
          {{ credSaving ? 'Salvando…' : 'Salvar credenciais' }}
        </button>
        <span v-if="credMsg" :class="['msg', credMsg.ok ? 'msg--ok' : 'msg--err']">{{ credMsg.text }}</span>
      </div>

      <p class="card-path">{{ envPath }}</p>
    </div>

    <!-- ── Pasta de dados ── -->
    <div v-if="activeTab === 'dados'" class="card">
      <p class="card-hint">Pasta onde os espelhos de ponto são salvos e lidos pelo app.</p>

      <div class="field">
        <label>Caminho da pasta</label>
        <div class="dir-wrap">
          <input v-model="dataDir" type="text" placeholder="Ex: /Users/nome/espelhos" class="dir-input" />
          <button type="button" class="btn-pick" @click="pickDataDir">Selecionar…</button>
        </div>
      </div>

      <div class="actions">
        <button class="btn-save" :disabled="dataDirSaving" @click="saveDataDir">
          {{ dataDirSaving ? 'Salvando…' : 'Salvar pasta' }}
        </button>
        <span v-if="dataDirMsg" :class="['msg', dataDirMsg.ok ? 'msg--ok' : 'msg--err']">{{ dataDirMsg.text }}</span>
      </div>

      <p class="card-hint" style="font-size:11px; opacity:0.65;">
        O crawler salva os arquivos em <code>pasta/servidores/&lt;nome&gt;/espelho-*.json</code>.
        Deixe em branco para usar o padrão do sistema.
      </p>
      <p class="card-path">{{ envPath }}</p>
    </div>

    <!-- ── Servidores ── -->
    <div v-if="activeTab === 'servidores'" class="card">
      <p class="card-hint">Lista de servidores que o crawler vai buscar no SIGRH.</p>

      <div class="field field--inline">
        <label>Anos do batch</label>
        <input v-model="anosInput" type="text" placeholder="ex: 2025, 2026" class="field-anos" />
        <span class="field-hint">separados por vírgula</span>
      </div>

      <div class="serv-list">
        <div v-if="servidores.length === 0" class="serv-empty">Nenhum servidor cadastrado.</div>
        <div v-for="(s, i) in servidores" :key="s.siape" class="serv-row">
          <span class="serv-nome">{{ s.nome }}</span>
          <span class="serv-siape">{{ s.siape }}</span>
          <button class="btn-remove" @click="removeServidor(i)" title="Remover">✕</button>
        </div>
      </div>

      <div class="add-form">
        <input v-model="novoNome" type="text" placeholder="NOME COMPLETO" class="add-nome" @keyup.enter="addServidor" />
        <input v-model="novoSiape" type="text" placeholder="SIAPE" class="add-siape" @keyup.enter="addServidor" />
        <button class="btn-add" @click="addServidor">+ Adicionar</button>
      </div>

      <div class="actions">
        <button class="btn-save" :disabled="servSaving" @click="saveServidores">
          {{ servSaving ? 'Salvando…' : 'Salvar servidores.yaml' }}
        </button>
        <span v-if="servMsg" :class="['msg', servMsg.ok ? 'msg--ok' : 'msg--err']">{{ servMsg.text }}</span>
      </div>

      <p class="card-path">{{ servidoresPath }}</p>
    </div>
  </div>
</template>

<style scoped>
.config-tabs { display: flex; gap: 4px; margin-bottom: 1.5rem; }
.ctab { padding: 6px 18px; font-size: 13px; font-weight: 500; color: var(--muted); background: transparent; border: 1px solid var(--border); border-radius: var(--radius-sm); cursor: pointer; transition: all 0.15s; }
.ctab--active { background: var(--blue); color: #fff; border-color: var(--blue); }
.ctab:hover:not(.ctab--active) { color: var(--text); }

.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.5rem; max-width: 560px; display: flex; flex-direction: column; gap: 1rem; }
.card-hint { font-size: 13px; color: var(--muted); margin: 0; }
.card-path { font-size: 10px; color: var(--muted); font-family: var(--mono); margin: 0; opacity: 0.6; }

.field { display: flex; flex-direction: column; gap: 5px; }
.field label { font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
.field input { padding: 8px 10px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--bg); color: var(--text); font-size: 13px; }
.field input:focus { outline: none; border-color: var(--blue); }

.field--inline { flex-direction: row; align-items: center; }
.field--inline label { white-space: nowrap; }
.field-anos { flex: 0 0 180px; }
.field-hint { font-size: 11px; color: var(--muted); }

.dir-wrap { display: flex; gap: 6px; }
.dir-input { flex: 1; padding: 8px 10px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--bg); color: var(--text); font-size: 13px; font-family: var(--mono); }
.dir-input:focus { outline: none; border-color: var(--blue); }
.btn-pick { padding: 7px 14px; font-size: 12px; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); cursor: pointer; white-space: nowrap; }
.btn-pick:hover { border-color: var(--blue); color: var(--blue); }
.pass-wrap { display: flex; gap: 6px; }
.pass-wrap input { flex: 1; }
.btn-toggle-pass { padding: 6px 12px; font-size: 12px; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--muted); cursor: pointer; white-space: nowrap; }
.btn-toggle-pass:hover { color: var(--text); }

.actions { display: flex; align-items: center; gap: 12px; }
.btn-save { padding: 7px 18px; background: var(--blue); color: #fff; border: none; border-radius: var(--radius-sm); font-size: 13px; font-weight: 500; cursor: pointer; }
.btn-save:disabled { opacity: 0.6; cursor: default; }
.msg { font-size: 12px; }
.msg--ok { color: var(--green); }
.msg--err { color: var(--red); }

.serv-list { display: flex; flex-direction: column; gap: 4px; min-height: 48px; }
.serv-empty { font-size: 13px; color: var(--muted); padding: 8px 0; }
.serv-row { display: flex; align-items: center; gap: 10px; padding: 6px 10px; background: var(--surface-2); border-radius: var(--radius-sm); }
.serv-nome { flex: 1; font-size: 13px; font-weight: 500; }
.serv-siape { font-size: 12px; font-family: var(--mono); color: var(--muted); }
.btn-remove { background: none; border: none; color: var(--muted); cursor: pointer; font-size: 12px; padding: 2px 6px; border-radius: var(--radius-sm); }
.btn-remove:hover { color: var(--red); background: var(--surface); }

.add-form { display: flex; gap: 8px; }
.add-nome { flex: 1; padding: 7px 10px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--bg); color: var(--text); font-size: 13px; }
.add-nome:focus { outline: none; border-color: var(--blue); }
.add-siape { flex: 0 0 110px; padding: 7px 10px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--bg); color: var(--text); font-size: 13px; font-family: var(--mono); }
.add-siape:focus { outline: none; border-color: var(--blue); }
.btn-add { padding: 7px 14px; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 13px; cursor: pointer; color: var(--text); white-space: nowrap; }
.btn-add:hover { border-color: var(--blue); color: var(--blue); }
</style>
