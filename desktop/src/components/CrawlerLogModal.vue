<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { useRoute } from "vue-router";
import { useCrawlerStore } from "@/stores/crawler";

const crawler = useCrawlerStore();
const route = useRoute();
const termEl = ref<HTMLElement | null>(null);
const visible = ref(false);

watch(() => crawler.running, (val) => {
  if (val && route.path !== "/crawler") visible.value = true;
});

watch(() => crawler.logs.length, async () => {
  await nextTick();
  if (termEl.value) termEl.value.scrollTop = termEl.value.scrollHeight;
});

function close() {
  if (!crawler.running) {
    visible.value = false;
    crawler.clearLogs();
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="visible" class="cl-backdrop" @click.self="close">
        <div class="cl-drawer">
          <div class="cl-toolbar">
            <div class="cl-toolbar-left">
              <span class="cl-label">OUTPUT</span>
              <span v-if="crawler.running" class="cl-status-running">
                <span class="dot-pulse"></span> Executando
              </span>
              <span v-else-if="crawler.exitCode === 0" class="cl-status-ok">● Concluído</span>
              <span v-else-if="crawler.exitCode !== null" class="cl-status-fail">● Falha (exit {{ crawler.exitCode }})</span>
            </div>
            <button class="cl-close" :disabled="crawler.running" @click="close" title="Fechar">✕</button>
          </div>

          <div v-if="crawler.running || crawler.progressTotal > 0" class="cl-progress-wrap">
            <div class="cl-progress-track">
              <div class="cl-progress-fill" :style="{ width: crawler.progressPct + '%' }"></div>
            </div>
            <span class="cl-progress-label">
              <template v-if="crawler.progressTotal > 0">
                {{ crawler.progressDone }}/{{ crawler.progressTotal }} ({{ crawler.progressPct }}%)
              </template>
              <template v-else>Aguardando…</template>
            </span>
          </div>

          <div ref="termEl" class="cl-terminal">
            <template v-if="crawler.logs.length === 0">
              <span class="cl-placeholder">Iniciando…</span>
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
    </Transition>
  </Teleport>
</template>

<style scoped>
.cl-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  z-index: 1000;
  display: flex; align-items: flex-end; justify-content: center;
}

.cl-drawer {
  width: 100%; max-width: 780px;
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  overflow: hidden;
  display: flex; flex-direction: column;
  box-shadow: 0 -8px 40px rgba(0,0,0,0.4);
}

.cl-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 16px;
  background: #1a1a1a;
  border-bottom: 1px solid #2a2a2a;
}
.cl-toolbar-left { display: flex; align-items: center; gap: 10px; }
.cl-label { font-size: 10px; font-weight: 600; color: #666; letter-spacing: 0.08em; text-transform: uppercase; }
.cl-status-running { font-size: 11px; color: #f4c66a; display: flex; align-items: center; gap: 5px; }
.cl-status-ok   { font-size: 11px; color: #4ade80; font-weight: 500; }
.cl-status-fail { font-size: 11px; color: #f87171; font-weight: 500; }
.cl-close {
  background: none; border: none; color: #666; font-size: 14px; cursor: pointer;
  width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;
  border-radius: 4px; transition: color 0.15s, background 0.15s;
}
.cl-close:hover:not(:disabled) { color: #fff; background: #333; }
.cl-close:disabled { opacity: 0.3; cursor: not-allowed; }

.cl-progress-wrap {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 16px; background: #0d0d0d; border-bottom: 1px solid #222;
}
.cl-progress-track { flex: 1; height: 6px; background: #2a2a2a; border-radius: 3px; overflow: hidden; }
.cl-progress-fill { height: 100%; background: var(--blue, #3b82f6); border-radius: 3px; transition: width 0.3s ease; }
.cl-progress-label { font-size: 11px; color: #888; font-family: var(--mono); white-space: nowrap; min-width: 120px; text-align: right; }

.cl-terminal {
  background: #111; color: #d4d4d4;
  font-family: var(--mono); font-size: 12px; line-height: 1.65;
  padding: 14px 18px;
  min-height: 260px; max-height: 400px;
  overflow-y: auto;
}
.cl-placeholder { color: #555; font-style: italic; }

.log-line { white-space: pre-wrap; word-break: break-all; }
.log-cmd  { color: #7dd3fc; }
.log-info { color: #a3a3a3; }
.log-ok   { color: #4ade80; font-weight: 500; }
.log-fail { color: #f87171; font-weight: 500; }
.log-err  { color: #f87171; }
.cursor   { display: inline-block; animation: blink 1s step-end infinite; color: #d4d4d4; }
@keyframes blink { 50% { opacity: 0; } }

.dot-pulse {
  width: 6px; height: 6px; border-radius: 50%; background: #f4c66a;
  display: inline-block; animation: pulse 1.2s ease-in-out infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s, transform 0.25s; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; transform: translateY(60px); }
</style>
