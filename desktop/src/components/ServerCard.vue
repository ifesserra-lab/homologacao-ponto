<script setup lang="ts">
import type { ServidorResume } from "@/types/dashboard";

defineProps<{ servidor: ServidorResume }>();
</script>

<template>
  <div class="card-wrap">
    <router-link class="server-card" :to="`/servidor/${servidor.slug}`">
      <div class="card-body">
        <div class="card-left">
          <span class="server-name">{{ servidor.nome }}</span>
          <div class="card-tags">
            <span v-if="servidor.siape" class="tag">SIAPE {{ servidor.siape }}</span>
            <span class="tag">{{ servidor.totalMeses }} {{ servidor.totalMeses === 1 ? "mês" : "meses" }}</span>
            <span v-if="servidor.totalMeses > 0" class="tag">{{ servidor.periodoRange }}</span>
          </div>
        </div>
        <div class="card-right">
          <span :class="['status-chip', servidor.statusIndicator === 'com-vazios' ? 'chip-amber' : 'chip-green']">
            {{ servidor.statusIndicator === "com-vazios" ? "Com vazios" : "Completo" }}
          </span>
          <svg class="chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m9 18 6-6-6-6"/></svg>
        </div>
      </div>
    </router-link>
  </div>
</template>

<style scoped>
.server-card {
  display: block;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  text-decoration: none; color: inherit;
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.15s, border-color 0.15s, transform 0.1s;
}
.server-card:hover { border-color: var(--border-mid); box-shadow: var(--shadow); transform: translateY(-1px); }
.server-card:active { transform: translateY(0); }
.card-body { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; gap: 12px; }
.card-left { flex: 1; min-width: 0; }
.server-name { display: block; font-size: 14px; font-weight: 500; letter-spacing: -0.01em; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.tag { font-size: 11px; font-weight: 450; padding: 2px 7px; background: var(--bg); color: var(--text-2); border: 1px solid var(--border); border-radius: 20px; }
.card-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.status-chip { font-size: 11px; font-weight: 500; padding: 3px 9px; border-radius: 20px; }
.chip-green { background: var(--green-light); color: var(--green); }
.chip-amber { background: var(--amber-light); color: var(--amber); }
.chevron { color: var(--muted); }
</style>
