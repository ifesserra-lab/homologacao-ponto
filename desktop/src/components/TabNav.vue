<script setup lang="ts">
import { useCrawlerStore } from "@/stores/crawler";
import { useServidoresStore } from "@/stores/servidores";
const crawler = useCrawlerStore();
const servidores = useServidoresStore();
</script>

<template>
  <div class="tab-nav">
    <router-link class="tab-btn" to="/" active-class="active" exact>Servidores</router-link>
    <router-link class="tab-btn" to="/indicadores" active-class="active">Indicadores</router-link>
    <router-link class="tab-btn" to="/crawler" active-class="active">
      Crawler
      <span v-if="crawler.running" class="tab-badge tab-badge--running"></span>
    </router-link>
    <button
      class="tab-btn tab-btn--refresh"
      :class="{ 'tab-btn--spinning': servidores.loading }"
      :disabled="servidores.loading"
      title="Atualizar dados"
      type="button"
      @click="servidores.load()"
    >↻</button>
    <router-link class="tab-btn tab-btn--config" to="/config" active-class="active" title="Configurações">⚙</router-link>
  </div>
</template>

<style scoped>
.tab-nav { display: flex; gap: 4px; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); }
.tab-btn { position: relative; padding: 8px 20px; font-size: 13px; font-weight: 500; color: var(--muted); text-decoration: none; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: color 0.15s, border-color 0.15s; display: flex; align-items: center; gap: 6px; }
.tab-btn:hover { color: var(--text); background: transparent; }
.tab-btn.active, .router-link-active { color: var(--blue); background: transparent; border-color: transparent; border-bottom-color: var(--blue); font-weight: 600; }
.tab-btn--refresh { margin-left: auto; font-size: 16px; padding: 8px 10px; background: none; border: none; cursor: pointer; transition: transform 0.2s, color 0.15s; }
.tab-btn--refresh:hover { color: var(--blue); }
.tab-btn--refresh:disabled { opacity: 0.4; cursor: default; }
.tab-btn--spinning { animation: spin 0.8s linear infinite; }
.tab-btn--config { font-size: 15px; padding: 8px 12px; }
.tab-badge--running { width: 6px; height: 6px; border-radius: 50%; background: var(--amber, #f59e0b); animation: pulse 1.2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
