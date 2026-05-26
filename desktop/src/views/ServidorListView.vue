<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useServidoresStore } from "@/stores/servidores";
import { useAuthStore } from "@/stores/auth";
import { crawlerRefreshKey } from "@/stores/crawler";
import ServerCard from "@/components/ServerCard.vue";
import ThemeToggle from "@/components/ThemeToggle.vue";
import TabNav from "@/components/TabNav.vue";

const store = useServidoresStore();
const auth = useAuthStore();
const query = ref("");

const filtered = computed(() =>
  query.value
    ? store.servidores.filter((s) => s.nome.toLowerCase().includes(query.value.toLowerCase()))
    : store.servidores
);

onMounted(() => {
  if (store.servidores.length === 0) store.load();
});
watch(crawlerRefreshKey, () => store.load());
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-row">
        <div>
          <h1 class="page-title">Espelhos de Ponto</h1>
          <p class="page-meta">SIGRH · {{ store.servidores.length }} {{ store.servidores.length === 1 ? "servidor" : "servidores" }}</p>
        </div>
        <div class="nav-actions">
          <ThemeToggle />
          <button class="logout-btn" type="button" @click="auth.logout(); $router.push('/login')">Sair</button>
        </div>
      </div>
    </header>

    <TabNav />

    <div v-if="store.loading" class="empty-state">
      <p>Carregando…</p>
    </div>
    <div v-else-if="store.error" class="empty-state">
      <p class="empty-title" style="color: var(--red)">Erro ao carregar dados</p>
      <p style="font-size:12px; font-family:var(--mono); margin-bottom:12px">{{ store.error }}</p>
      <code class="empty-hint">{{ store.dataDir }}</code>
    </div>
    <div v-else-if="store.isEmpty" class="empty-state">
      <div class="empty-icon">📂</div>
      <p class="empty-title">Nenhum espelho encontrado</p>
      <p>Execute o batch para exportar espelhos.</p>
      <code class="empty-hint">{{ store.dataDir }}</code>
    </div>
    <template v-else>
      <div class="filter-wrap">
        <svg class="filter-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input v-model="query" type="search" placeholder="Buscar servidor…" aria-label="Filtrar servidores" />
      </div>
      <div class="server-list">
        <ServerCard v-for="s in filtered" :key="s.slug" :servidor="s" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.server-list { display: flex; flex-direction: column; gap: 6px; }
.filter-wrap { position: relative; margin-bottom: 1rem; }
.filter-wrap input { width: 100%; padding: 8px 10px 8px 30px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); color: var(--text); font-size: 13px; outline: none; }
.filter-wrap input:focus { border-color: var(--blue); box-shadow: 0 0 0 3px var(--focus-ring); }
.filter-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--muted); pointer-events: none; }
.empty-state { text-align: center; padding: 3rem 1rem; color: var(--muted); }
.empty-icon { font-size: 2rem; margin-bottom: 0.5rem; }
.empty-title { font-size: 15px; font-weight: 500; color: var(--text); margin-bottom: 4px; }
.empty-hint { font-size: 12px; font-family: var(--mono); background: var(--surface-2); padding: 3px 8px; border-radius: 4px; margin-top: 8px; display: inline-block; }
</style>
