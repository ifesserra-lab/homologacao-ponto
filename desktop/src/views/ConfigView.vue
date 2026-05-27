<script setup lang="ts">
import { ref, onMounted } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import yaml from "js-yaml";
import { useAuthStore } from "@/stores/auth";
import { useServidoresStore } from "@/stores/servidores";
import { useCrawlerStore } from "@/stores/crawler";
import TabNav from "@/components/TabNav.vue";
import ThemeToggle from "@/components/ThemeToggle.vue";

const auth = useAuthStore();
const servidoresStore = useServidoresStore();
const crawler = useCrawlerStore();
const activeTab = ref<"sigrh" | "dados" | "app" | "servidores" | "homologacao">("sigrh");

const configPath = ref("");
const servidoresPath = ref("");

// ── helpers ───────────────────────────────────────────────────
async function loadConfig(): Promise<any> {
  try {
    const content = await invoke<string>("read_config_file");
    return (yaml.load(content) as any) ?? {};
  } catch { return {}; }
}

async function saveConfig(patch: Record<string, any>) {
  const current = await loadConfig();
  const merged = deepMerge(current, patch);
  const content = yaml.dump(merged, { indent: 2, lineWidth: -1 });
  await invoke("write_config_file", { content });
}

function deepMerge(base: any, patch: any): any {
  const out = { ...base };
  for (const [k, v] of Object.entries(patch)) {
    if (v && typeof v === "object" && !Array.isArray(v) && typeof base[k] === "object") {
      out[k] = deepMerge(base[k], v);
    } else {
      out[k] = v;
    }
  }
  return out;
}

async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
}

// ── Credenciais SIGRH ─────────────────────────────────────────
const sigrh_usuario = ref("");
const sigrh_senha = ref("");
const showSigrhPass = ref(false);
const sigrh_setor = ref("");
const sigrhSaving = ref(false);
const sigrhMsg = ref<{ ok: boolean; text: string } | null>(null);

async function loadSigrh() {
  const cfg = await loadConfig();
  sigrh_usuario.value = cfg?.sigrh?.usuario ?? "";
  sigrh_senha.value = cfg?.sigrh?.senha ?? "";
  sigrh_setor.value = cfg?.chefia?.setor ?? "";
}

async function saveSigrh() {
  sigrhSaving.value = true; sigrhMsg.value = null;
  try {
    await saveConfig({ sigrh: { usuario: sigrh_usuario.value.trim(), senha: sigrh_senha.value }, chefia: { setor: sigrh_setor.value.trim() } });
    sigrhMsg.value = { ok: true, text: "✓ Credenciais salvas" };
  } catch (e) { sigrhMsg.value = { ok: false, text: `Erro: ${e}` }; }
  finally { sigrhSaving.value = false; }
}

// ── Pasta de dados ────────────────────────────────────────────
const dataDir = ref("");
const dataDirSaving = ref(false);
const dataDirMsg = ref<{ ok: boolean; text: string } | null>(null);

async function loadDataDir() {
  const cfg = await loadConfig();
  dataDir.value = cfg?.dados?.pasta ?? await invoke<string>("resolve_data_dir");
}

async function pickDataDir() {
  const selected = await openDialog({ directory: true, multiple: false, title: "Selecionar pasta de dados" });
  if (selected && typeof selected === "string") dataDir.value = selected;
}

async function saveDataDir() {
  dataDirSaving.value = true; dataDirMsg.value = null;
  try {
    await saveConfig({ dados: { pasta: dataDir.value.trim() } });
    await servidoresStore.load();
    dataDirMsg.value = { ok: true, text: "✓ Pasta salva e dados recarregados" };
  } catch (e) { dataDirMsg.value = { ok: false, text: `Erro: ${e}` }; }
  finally { dataDirSaving.value = false; }
}

// ── Homologação ───────────────────────────────────────────────
const politicaHe = ref<"manual" | "autorizar" | "zerar">("manual");
const homologSaving = ref(false);
const homologMsg = ref<{ ok: boolean; text: string } | null>(null);

async function loadHomologacao() {
  const cfg = await loadConfig();
  politicaHe.value = cfg?.homologacao?.politica_he ?? "manual";
}

async function saveHomologacao() {
  homologSaving.value = true; homologMsg.value = null;
  try {
    await saveConfig({ homologacao: { politica_he: politicaHe.value } });
    homologMsg.value = { ok: true, text: "✓ Política salva" };
  } catch (e) { homologMsg.value = { ok: false, text: `Erro: ${e}` }; }
  finally { homologSaving.value = false; }
}

// ── Login do app ──────────────────────────────────────────────
const appUsuario = ref("");
const appSenha = ref("");
const showAppPass = ref(false);
const appSaving = ref(false);
const appMsg = ref<{ ok: boolean; text: string } | null>(null);

async function saveAppLogin() {
  if (!appUsuario.value.trim() || !appSenha.value) {
    appMsg.value = { ok: false, text: "Preencha usuário e senha" }; return;
  }
  appSaving.value = true; appMsg.value = null;
  try {
    const [uh, ph] = await Promise.all([sha256(appUsuario.value.trim()), sha256(appSenha.value)]);
    await saveConfig({ app: { usuario_hash: uh, senha_hash: ph } });
    appMsg.value = { ok: true, text: "✓ Login salvo — ativo no próximo acesso" };
    appUsuario.value = ""; appSenha.value = "";
  } catch (e) { appMsg.value = { ok: false, text: `Erro: ${e}` }; }
  finally { appSaving.value = false; }
}

async function clearAppLogin() {
  appSaving.value = true; appMsg.value = null;
  try {
    await saveConfig({ app: { usuario_hash: "", senha_hash: "" } });
    appMsg.value = { ok: true, text: "✓ Login removido — app ficará sem autenticação" };
  } catch (e) { appMsg.value = { ok: false, text: `Erro: ${e}` }; }
  finally { appSaving.value = false; }
}

// ── Servidores ────────────────────────────────────────────────
interface Servidor { nome: string; siape: string }
const servidores = ref<Servidor[]>([]);
const anosInput = ref("");
const novoNome = ref("");
const novoSiape = ref("");
const servSaving = ref(false);
const servMsg = ref<{ ok: boolean; text: string } | null>(null);

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

// ── init ──────────────────────────────────────────────────────
onMounted(async () => {
  const paths = await invoke<{ config_path: string; servidores_path: string }>("get_config_paths");
  configPath.value = paths.config_path;
  servidoresPath.value = paths.servidores_path;
  await Promise.all([loadSigrh(), loadDataDir(), loadServidores(), loadHomologacao()]);
});
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-row">
        <div>
          <h1 class="page-title">Configurações</h1>
          <p class="page-meta">Credenciais · Dados · Servidores</p>
        </div>
        <div class="nav-actions">
          <ThemeToggle />
          <button class="logout-btn" type="button" @click="auth.logout(); $router.push('/login')">Sair</button>
        </div>
      </div>
    </header>

    <TabNav />

    <div class="config-tabs">
      <button :class="['ctab', activeTab === 'sigrh' && 'ctab--active']" @click="activeTab = 'sigrh'">
        Credenciais SIGRH
      </button>
      <button :class="['ctab', activeTab === 'dados' && 'ctab--active']" @click="activeTab = 'dados'">
        Pasta de Dados
      </button>
      <button :class="['ctab', activeTab === 'app' && 'ctab--active']" @click="activeTab = 'app'">
        Login do App
      </button>
      <button :class="['ctab', activeTab === 'servidores' && 'ctab--active']" @click="activeTab = 'servidores'">
        Servidores ({{ servidores.length }})
      </button>
      <button :class="['ctab', activeTab === 'homologacao' && 'ctab--active']" @click="activeTab = 'homologacao'">
        Homologação
      </button>
    </div>

    <!-- ── Credenciais SIGRH ── -->
    <div v-if="activeTab === 'sigrh'" class="card">
      <p class="card-hint">Credenciais usadas pelo crawler para acessar o SIGRH.</p>
      <div class="field">
        <label>Usuário SIGRH</label>
        <input v-model="sigrh_usuario" type="text" autocomplete="off" placeholder="ex: 1234567" />
      </div>
      <div class="field">
        <label>Senha SIGRH</label>
        <div class="pass-wrap">
          <input v-model="sigrh_senha" :type="showSigrhPass ? 'text' : 'password'" autocomplete="off" placeholder="••••••••" />
          <button type="button" class="btn-toggle" @click="showSigrhPass = !showSigrhPass">
            {{ showSigrhPass ? 'Ocultar' : 'Mostrar' }}
          </button>
        </div>
      </div>
      <div class="field">
        <label>Setor / Unidade (SIGRH)</label>
        <input
          v-model="sigrh_setor"
          type="text"
          autocomplete="off"
          placeholder="Ex: COORDENAÇÃO DE GESTÃO DE PESSOAS"
        />
        <span class="field-sublabel">Nome exato da unidade como aparece na tela de homologação do SIGRH</span>
      </div>
      <div class="actions">
        <button class="btn-save" :disabled="sigrhSaving" @click="saveSigrh">
          {{ sigrhSaving ? 'Salvando…' : 'Salvar credenciais' }}
        </button>
        <span v-if="sigrhMsg" :class="['msg', sigrhMsg.ok ? 'msg--ok' : 'msg--err']">{{ sigrhMsg.text }}</span>
      </div>
      <p class="card-path">{{ configPath }}</p>
    </div>

    <!-- ── Pasta de dados ── -->
    <div v-if="activeTab === 'dados'" class="card">
      <p class="card-hint">Pasta onde os espelhos de ponto são salvos e lidos pelo app.</p>
      <div class="field">
        <label>Caminho da pasta</label>
        <div class="dir-wrap">
          <input v-model="dataDir" type="text" placeholder="Ex: /Users/nome/espelhos" class="dir-input" />
          <button type="button" class="btn-toggle" @click="pickDataDir">Selecionar…</button>
        </div>
      </div>
      <div class="actions">
        <button class="btn-save" :disabled="dataDirSaving" @click="saveDataDir">
          {{ dataDirSaving ? 'Salvando…' : 'Salvar pasta' }}
        </button>
        <span v-if="dataDirMsg" :class="['msg', dataDirMsg.ok ? 'msg--ok' : 'msg--err']">{{ dataDirMsg.text }}</span>
      </div>
      <p class="card-hint" style="font-size:11px; opacity:0.65;">
        O crawler salva em <code>pasta/servidores/&lt;nome&gt;/espelho-*.json</code>. Deixe vazio para usar o padrão.
      </p>
      <p class="card-path">{{ configPath }}</p>
    </div>

    <!-- ── Login do app ── -->
    <div v-if="activeTab === 'app'" class="card">
      <p class="card-hint">
        Define o usuário e senha para entrar no aplicativo. Os valores são armazenados
        como hashes SHA-256 — a senha original não é salva.
      </p>
      <div class="field">
        <label>Novo usuário</label>
        <input v-model="appUsuario" type="text" autocomplete="off" placeholder="ex: admin" />
      </div>
      <div class="field">
        <label>Nova senha</label>
        <div class="pass-wrap">
          <input v-model="appSenha" :type="showAppPass ? 'text' : 'password'" autocomplete="new-password" placeholder="••••••••" />
          <button type="button" class="btn-toggle" @click="showAppPass = !showAppPass">
            {{ showAppPass ? 'Ocultar' : 'Mostrar' }}
          </button>
        </div>
      </div>
      <div class="actions">
        <button class="btn-save" :disabled="appSaving" @click="saveAppLogin">
          {{ appSaving ? 'Salvando…' : 'Definir login' }}
        </button>
        <button class="btn-danger" :disabled="appSaving" @click="clearAppLogin" title="Remove autenticação — qualquer pessoa poderá entrar">
          Remover login
        </button>
        <span v-if="appMsg" :class="['msg', appMsg.ok ? 'msg--ok' : 'msg--err']">{{ appMsg.text }}</span>
      </div>
      <p class="card-path">{{ configPath }}</p>
    </div>

    <!-- ── Homologação ── -->
    <div v-if="activeTab === 'homologacao'" class="card">
      <p class="card-hint">Define como o sistema trata Horas Excedentes (HE) na homologação automática.</p>

      <div class="field">
        <label>Política de HE</label>
        <div class="politica-group">
          <label :class="['politica-opt', politicaHe === 'manual' && 'politica-opt--active']">
            <input type="radio" v-model="politicaHe" value="manual" />
            <span class="politica-title">Manual</span>
            <span class="politica-desc">HE não autorizado bloqueia a homologação — chefia decide caso a caso</span>
          </label>
          <label :class="['politica-opt', politicaHe === 'autorizar' && 'politica-opt--active']">
            <input type="radio" v-model="politicaHe" value="autorizar" />
            <span class="politica-title">Autorizar automaticamente</span>
            <span class="politica-desc">HE é autorizado antes de homologar — HA recebe o mesmo valor de HE</span>
          </label>
          <label :class="['politica-opt', politicaHe === 'zerar' && 'politica-opt--active']">
            <input type="radio" v-model="politicaHe" value="zerar" />
            <span class="politica-title">Zerar HE</span>
            <span class="politica-desc">HA é zerado antes de homologar — horas excedentes desconsideradas</span>
          </label>
        </div>
      </div>

      <div class="actions">
        <button class="btn-save" :disabled="homologSaving" @click="saveHomologacao">
          {{ homologSaving ? 'Salvando…' : 'Salvar política' }}
        </button>
        <span v-if="homologMsg" :class="['msg', homologMsg.ok ? 'msg--ok' : 'msg--err']">{{ homologMsg.text }}</span>
      </div>
      <p class="card-path">{{ configPath }}</p>
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
        <button class="btn-descobrir" :disabled="crawler.running" @click="crawler.startDescobrir()" :title="crawler.running ? 'Aguarde…' : 'Buscar servidores da unidade no SIGRH'">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          {{ crawler.running ? '…' : 'Descobrir servidores' }}
        </button>
        <span v-if="servMsg" :class="['msg', servMsg.ok ? 'msg--ok' : 'msg--err']">{{ servMsg.text }}</span>
      </div>
      <p class="card-path">{{ servidoresPath }}</p>
    </div>
  </div>
</template>

<style scoped>
.config-tabs { display: flex; gap: 4px; margin-bottom: 1.5rem; flex-wrap: wrap; }
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

.pass-wrap, .dir-wrap { display: flex; gap: 6px; }
.pass-wrap input, .dir-wrap input { flex: 1; }
.dir-wrap input { font-family: var(--mono); font-size: 12px; }
.btn-toggle { padding: 6px 12px; font-size: 12px; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--muted); cursor: pointer; white-space: nowrap; }
.btn-toggle:hover { color: var(--text); border-color: var(--blue); }

.actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.btn-save { padding: 7px 18px; background: var(--blue); color: #fff; border: none; border-radius: var(--radius-sm); font-size: 13px; font-weight: 500; cursor: pointer; }
.btn-save:disabled { opacity: 0.6; cursor: default; }
.btn-danger { padding: 7px 14px; background: transparent; color: var(--red, #ef4444); border: 1px solid var(--red, #ef4444); border-radius: var(--radius-sm); font-size: 13px; cursor: pointer; }
.btn-danger:hover { background: var(--red, #ef4444); color: #fff; }
.btn-danger:disabled { opacity: 0.5; cursor: default; }
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
.btn-descobrir { display: inline-flex; align-items: center; gap: 5px; padding: 7px 14px; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 13px; cursor: pointer; color: var(--text); white-space: nowrap; }
.btn-descobrir:hover:not(:disabled) { border-color: var(--blue); color: var(--blue); }
.btn-descobrir:disabled { opacity: 0.5; cursor: not-allowed; }

.politica-group { display: flex; flex-direction: column; gap: 8px; }
.politica-opt { display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); cursor: pointer; transition: border-color 0.15s, background 0.15s; }
.politica-opt input[type="radio"] { margin-top: 2px; accent-color: var(--blue); flex-shrink: 0; }
.politica-opt--active { border-color: var(--blue); background: var(--blue-light, #e8f2fc); }
.politica-opt:hover:not(.politica-opt--active) { border-color: var(--blue); }
.politica-title { font-size: 13px; font-weight: 600; color: var(--text); white-space: nowrap; }
.politica-desc { font-size: 11px; color: var(--muted); line-height: 1.4; flex: 1; }
.field-sublabel { font-size: 11px; color: var(--muted); }
</style>
