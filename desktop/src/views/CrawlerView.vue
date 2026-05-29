<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useCrawlerStore } from "@/stores/crawler";
import ThemeToggle from "@/components/ThemeToggle.vue";
import TabNav from "@/components/TabNav.vue";

const auth = useAuthStore();
const crawler = useCrawlerStore();
const termEl = ref<HTMLElement | null>(null);
const showTip = ref(false);

async function scrollBottom() {
  await nextTick();
  if (termEl.value) termEl.value.scrollTop = termEl.value.scrollHeight;
}

watch(() => crawler.logs.length, () => scrollBottom());
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-row">
        <div>
          <h1 class="page-title">Crawler SIGRH</h1>
        </div>
        <div class="nav-actions">
          <ThemeToggle />
          <button class="logout-btn" type="button" @click="auth.logout(); $router.push('/login')">Sair</button>
        </div>
      </div>
    </header>

    <TabNav />

    <div class="crawler-layout">
      <!-- Toolbar -->
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="terminal-label">OUTPUT</span>
          <span v-if="crawler.running" class="status-running"><span class="dot-pulse"></span> Executando</span>
          <span v-else-if="crawler.exitCode === 0" class="status-ok">● Sucesso</span>
          <span v-else-if="crawler.exitCode !== null" class="status-fail">● Falha (exit {{ crawler.exitCode }})</span>
        </div>
        <div class="toolbar-right">
          <button v-if="crawler.logs.length > 0 && !crawler.running" class="btn-clear" @click="crawler.clearLogs()">Limpar</button>
          <div v-if="!crawler.running" class="btn-run-wrap">
            <button
              class="btn-run"
              @click="crawler.startRefresh()"
              @mouseenter="showTip = true"
              @mouseleave="showTip = false"
            >▶ Executar</button>
            <Teleport to="body">
              <div v-if="showTip" class="run-tooltip">
                <div class="run-tooltip-title">Algoritmo inteligente</div>
                <ul>
                  <li><span class="tip-dot new"></span> Arquivo ausente → <b>baixa</b></li>
                  <li><span class="tip-dot warn"></span> Dias pendentes → <b>atualiza</b></li>
                  <li><span class="tip-dot warn"></span> Débito não autorizado → <b>atualiza</b></li>
                  <li><span class="tip-dot warn"></span> Mês atual → <b>sempre atualiza</b></li>
                  <li><span class="tip-dot ok"></span> Completo e homologado → <b>ignora</b></li>
                </ul>
              </div>
            </Teleport>
          </div>
          <button v-else class="btn-run btn-run--running" disabled>
            <span class="spinner"></span> Executando…
          </button>
        </div>
      </div>

      <!-- Barra de progresso -->
      <div v-if="crawler.running || crawler.progressTotal > 0" class="progress-wrap">
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: crawler.progressPct + '%' }"></div>
        </div>
        <span class="progress-label">
          <template v-if="crawler.progressTotal > 0">{{ crawler.progressDone }}/{{ crawler.progressTotal }} ({{ crawler.progressPct }}%)</template>
          <template v-else>Aguardando…</template>
        </span>
      </div>

      <!-- Terminal sempre visível -->
      <div ref="termEl" class="terminal">
        <template v-if="crawler.logs.length === 0">
          <span class="term-placeholder">▶ Executar — analisa JSONs existentes e baixa apenas meses desatualizados<br/>"Forçar tudo" — re-baixa todos os meses sem análise prévia</span>
        </template>
        <template v-else>
          <div
            v-for="(line, i) in crawler.logs"
            :key="i"
            :class="['log-line',
              line.startsWith('[err]') ? 'log-err' :
              line.startsWith('✓') ? 'log-ok' :
              line.startsWith('✗') ? 'log-fail' :
              line.startsWith('$') ? 'log-cmd' :
              line.startsWith('  ✓') ? 'log-ok' :
              line.startsWith('  ✗') ? 'log-err' :
              line.startsWith('→') ? 'log-info' : ''
            ]"
          >{{ line }}</div>
          <span v-if="crawler.running" class="cursor">▌</span>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.crawler-layout { display: flex; flex-direction: column; gap: 0; border-radius: var(--radius); overflow: hidden; border: 1px solid var(--border); }

.toolbar { display: flex; justify-content: space-between; align-items: center; padding: 8px 14px; background: var(--surface-2); border-bottom: 1px solid var(--border); gap: 12px; }
.toolbar-left { display: flex; align-items: center; gap: 10px; }
.toolbar-right { display: flex; align-items: center; gap: 8px; }
.terminal-label { font-size: 10px; font-weight: 600; color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase; }

.status-running { font-size: 11px; color: var(--amber); display: flex; align-items: center; gap: 5px; }
.status-ok { font-size: 11px; color: var(--green); font-weight: 500; }
.status-fail { font-size: 11px; color: var(--red); font-weight: 500; }

.btn-run-wrap { position: relative; }
.run-tooltip {
  position: fixed;
  bottom: 32px; right: 32px;
  background: #1a1a1a;
  color: #e8e8e5;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 16px 20px;
  font-size: 13px;
  line-height: 1.9;
  z-index: 9999;
  box-shadow: 0 8px 32px rgba(0,0,0,0.55);
  pointer-events: none;
  min-width: 280px;
}
.run-tooltip-title {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #333;
}
.run-tooltip ul { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.run-tooltip li { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #ccc; }
.run-tooltip li b { color: #fff; font-weight: 500; }
.tip-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.tip-dot.new  { background: #5b9fe8; }
.tip-dot.warn { background: #f4c66a; }
.tip-dot.ok   { background: #4caf90; }
.btn-run { padding: 5px 14px; background: var(--blue); color: var(--on-accent); border: none; border-radius: var(--radius-sm); font-size: 12px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.btn-run:disabled { opacity: 0.7; cursor: default; }
.btn-run--running { background: #444; color: #ccc; }
.btn-clear { padding: 5px 10px; background: transparent; color: var(--muted); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 12px; cursor: pointer; }
.btn-clear:hover { color: var(--text); }

.terminal { background: #111; color: #d4d4d4; font-family: var(--mono); font-size: 12px; line-height: 1.65; padding: 16px 18px; min-height: 380px; max-height: calc(100vh - 260px); overflow-y: auto; position: relative; }
.term-placeholder { color: #555; font-style: italic; }

.log-line { white-space: pre-wrap; word-break: break-all; }
.log-cmd  { color: #7dd3fc; }
.log-info { color: #a3a3a3; }
.log-ok   { color: #4ade80; font-weight: 500; }
.log-fail { color: #f87171; font-weight: 500; }
.log-err  { color: #f87171; }

.cursor { display: inline-block; animation: blink 1s step-end infinite; color: #d4d4d4; }
@keyframes blink { 50% { opacity: 0; } }

.dot-pulse { width: 6px; height: 6px; border-radius: 50%; background: var(--amber); display: inline-block; animation: pulse 1.2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

.spinner { width: 11px; height: 11px; border: 2px solid rgba(255,255,255,0.25); border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

.progress-wrap { display: flex; align-items: center; gap: 10px; padding: 8px 14px; background: #0d0d0d; border-bottom: 1px solid #222; }
.progress-track { flex: 1; height: 6px; background: #2a2a2a; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--blue, #3b82f6); border-radius: 3px; transition: width 0.3s ease; }
.progress-label { font-size: 11px; color: #888; font-family: var(--mono); white-space: nowrap; min-width: 110px; text-align: right; }
</style>
