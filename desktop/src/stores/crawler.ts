import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";

// lastRefreshed increments every time a successful batch completes.
// Views watch this to trigger reload without needing cross-store imports inside async callbacks.
export const crawlerRefreshKey = ref(0);

export const useCrawlerStore = defineStore("crawler", () => {
  const running = ref(false);
  const logs = ref<string[]>([]);
  const exitCode = ref<number | null>(null);
  const progressDone = ref(0);
  const progressTotal = ref(0);

  const progressPct = computed(() =>
    progressTotal.value > 0 ? Math.round((progressDone.value / progressTotal.value) * 100) : 0
  );

  let unlistenLog: UnlistenFn | null = null;
  let unlistenDone: UnlistenFn | null = null;

  function handleLine(line: string) {
    const startM = line.match(/^\[batch:start\] total=(\d+)$/);
    if (startM) { progressTotal.value = parseInt(startM[1]); progressDone.value = 0; return; }
    const progM = line.match(/^\[batch:progress\] (\d+)\/(\d+)$/);
    if (progM) { progressDone.value = parseInt(progM[1]); progressTotal.value = parseInt(progM[2]); return; }
    logs.value.push(line);
  }

  async function _start(cmd: string, label: string) {
    if (running.value) return;
    running.value = true;
    exitCode.value = null;
    progressDone.value = 0;
    progressTotal.value = 0;
    logs.value = [`$ crawler ${cmd}`, label];

    unlistenLog = await listen<string>("crawler-log", (e) => handleLine(e.payload));
    unlistenDone = await listen<number>("crawler-done", (e) => {
      exitCode.value = e.payload;
      logs.value.push(e.payload === 0 ? "✓ Concluído com sucesso" : `✗ Encerrado com código ${e.payload}`);
      running.value = false;
      unlistenLog?.(); unlistenLog = null;
      unlistenDone?.(); unlistenDone = null;
      if (e.payload === 0) crawlerRefreshKey.value += 1;
    });

    try {
      await invoke("run_crawler", { command: cmd, extraArgs: [] });
    } catch (e) {
      logs.value.push(`Erro: ${e}`);
      running.value = false;
      unlistenLog?.(); unlistenLog = null;
      unlistenDone?.(); unlistenDone = null;
    }
  }

  function startBatch()   { return _start("batch",   "Baixando todos os meses…"); }
  function startRefresh() { return _start("refresh", "Verificando meses pendentes…"); }

  function clearLogs() {
    if (!running.value) {
      logs.value = [];
      exitCode.value = null;
      progressDone.value = 0;
      progressTotal.value = 0;
    }
  }

  return { running, logs, exitCode, progressDone, progressTotal, progressPct, startBatch, startRefresh, clearLogs };
});
