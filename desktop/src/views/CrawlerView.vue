<script setup lang="ts">
import { ref, onUnmounted, nextTick } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { useAuthStore } from "@/stores/auth";
import ThemeToggle from "@/components/ThemeToggle.vue";

const auth = useAuthStore();
const running = ref(false);
const logs = ref<string[]>([]);
const exitCode = ref<number | null>(null);
const termEl = ref<HTMLElement | null>(null);

let unlistenLog: (() => void) | null = null;
let unlistenDone: (() => void) | null = null;

async function scrollBottom() {
  await nextTick();
  if (termEl.value) termEl.value.scrollTop = termEl.value.scrollHeight;
}

async function startBatch() {
  if (running.value) return;
  running.value = true;
  exitCode.value = null;
  logs.value = ["Iniciando crawler…"];

  unlistenLog = await listen<string>("crawler-log", (e) => {
    logs.value.push(e.payload);
    scrollBottom();
  });

  unlistenDone = await listen<number>("crawler-done", (e) => {
    exitCode.value = e.payload;
    const ok = e.payload === 0;
    logs.value.push(ok ? "✓ Concluído com sucesso" : `✗ Encerrado com código ${e.payload}`);
    running.value = false;
    scrollBottom();
    unlistenLog?.();
    unlistenDone?.();
    unlistenLog = null;
    unlistenDone = null;
  });

  try {
    await invoke("run_crawler", { extraArgs: [] });
  } catch (e) {
    logs.value.push(`Erro: ${e}`);
    running.value = false;
    unlistenLog?.();
    unlistenDone?.();
  }
}

function clearLogs() {
  if (!running.value) {
    logs.value = [];
    exitCode.value = null;
  }
}

onUnmounted(() => {
  unlistenLog?.();
  unlistenDone?.();
});
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-row">
        <div>
          <h1 class="page-title">Crawler SIGRH</h1>
          <p class="page-meta">Baixa espelhos de ponto via Playwright · Node.js</p>
        </div>
        <div class="nav-actions">
          <ThemeToggle />
          <button class="logout-btn" type="button" @click="auth.logout(); $router.push('/login')">Sair</button>
        </div>
      </div>
    </header>

    <div class="tab-nav">
      <router-link class="tab-btn" to="/" exact>Servidores</router-link>
      <router-link class="tab-btn" to="/indicadores">Indicadores</router-link>
      <router-link class="tab-btn" to="/crawler" active-class="active">Crawler</router-link>
    </div>

    <div class="crawler-card">
      <div class="crawler-header">
        <div>
          <p class="crawler-hint">
            Lê <code>servidores.yaml</code> e baixa espelhos para <code>data/runs/servidores/</code>.
            Requer credenciais em <code>desktop/.env</code>:
          </p>
          <pre class="env-example">SIGRH_USERNAME=seu.login
SIGRH_PASSWORD=sua.senha</pre>
        </div>
        <div class="actions">
          <button
            v-if="!running"
            class="btn-run"
            :disabled="running"
            @click="startBatch"
          >
            ▶ Executar Batch
          </button>
          <button v-else class="btn-run btn-run--running" disabled>
            <span class="spinner"></span> Executando…
          </button>
          <button v-if="logs.length > 0 && !running" class="btn-clear" @click="clearLogs">Limpar</button>
        </div>
      </div>

      <div
        v-if="logs.length > 0"
        ref="termEl"
        class="terminal"
      >
        <div
          v-for="(line, i) in logs"
          :key="i"
          :class="['log-line', line.startsWith('[err]') ? 'log-err' : line.startsWith('✓') ? 'log-ok' : line.startsWith('✗') ? 'log-fail' : '']"
        >{{ line }}</div>
      </div>

      <div v-if="exitCode !== null" :class="['exit-badge', exitCode === 0 ? 'exit-ok' : 'exit-fail']">
        Exit {{ exitCode }} · {{ exitCode === 0 ? "Sucesso" : "Com falhas" }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.crawler-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }
.crawler-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 16px; flex-wrap: wrap; }
.crawler-hint { font-size: 13px; color: var(--muted); margin-bottom: 8px; }
.crawler-hint code { font-family: var(--mono); font-size: 12px; background: var(--surface-2); padding: 1px 5px; border-radius: 3px; }
.env-example { font-family: var(--mono); font-size: 12px; background: var(--surface-2); border: 1px solid var(--border); border-radius: 4px; padding: 8px 12px; color: var(--text); margin: 0; }
.actions { display: flex; gap: 8px; align-items: flex-start; flex-shrink: 0; }
.btn-run { padding: 8px 18px; background: var(--blue); color: var(--on-accent); border: none; border-radius: var(--radius-sm); font-size: 13px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-run:disabled { opacity: 0.7; cursor: default; }
.btn-run--running { background: var(--muted); }
.btn-clear { padding: 8px 12px; background: transparent; color: var(--muted); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 13px; cursor: pointer; }
.btn-clear:hover { color: var(--text); border-color: var(--text); }
.terminal { background: #1a1a1a; color: #d4d4d4; font-family: var(--mono); font-size: 12px; line-height: 1.6; border-radius: 6px; padding: 12px 16px; max-height: 420px; overflow-y: auto; margin-top: 4px; }
.log-line { white-space: pre-wrap; word-break: break-all; }
.log-err { color: #f87171; }
.log-ok { color: #4ade80; font-weight: 500; }
.log-fail { color: #f87171; font-weight: 500; }
.exit-badge { display: inline-block; margin-top: 12px; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; }
.exit-ok { background: var(--green-light); color: var(--green); }
.exit-fail { background: var(--amber-light); color: var(--amber); }
.spinner { width: 12px; height: 12px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
.tab-nav { display: flex; gap: 4px; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); }
.tab-btn { padding: 8px 20px; font-size: 13px; font-weight: 500; color: var(--muted); text-decoration: none; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: color 0.15s, border-color 0.15s; }
.tab-btn:hover, .tab-btn.active, .router-link-active { color: var(--text); border-bottom-color: var(--blue); font-weight: 600; }
</style>
