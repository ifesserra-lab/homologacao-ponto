<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useServidoresStore } from "@/stores/servidores";
import { useAuthStore } from "@/stores/auth";
import { crawlerRefreshKey } from "@/stores/crawler";
import { aggregateMonth, formatMin, pctCarga, countOcorrencias } from "@/lib/aggregation";
import { dedupRegistros } from "@/lib/dedupRegistros";
import DayTable from "@/components/DayTable.vue";
import ThemeToggle from "@/components/ThemeToggle.vue";
import Breadcrumb from "@/components/Breadcrumb.vue";
import type { RawEspelho } from "@/types/dashboard";

const route = useRoute();
const router = useRouter();
const store = useServidoresStore();
const auth = useAuthStore();
const slug = route.params.slug as string;
const periodo = route.params.periodo as string;
const espelho = ref<RawEspelho | null>(null);

const registros = computed(() =>
  espelho.value ? dedupRegistros(espelho.value.registros) : []
);

const agg = computed(() => espelho.value ? aggregateMonth(registros.value, espelho.value.resumo ?? null, espelho.value.captured_at) : null);
const pct = computed(() => agg.value ? pctCarga(agg.value.somaCreditoMin, agg.value.cargaEsperadaMin) : null);
const ocorrencias = computed(() => espelho.value ? countOcorrencias(registros.value) : []);
const faltaMin = computed(() => agg.value?.balanceMin !== null && agg.value?.balanceMin! < 0 ? -agg.value!.balanceMin! : 0);

onMounted(async () => {
  if (store.servidores.length === 0) await store.load();
  const e = await store.getMes(slug, periodo);
  if (!e) { router.push(`/servidor/${slug}`); return; }
  espelho.value = e;
});
watch(crawlerRefreshKey, () => store.load());
</script>

<template>
  <div class="page-wide">
    <div class="nav-row">
      <Breadcrumb :items="[
        { label: 'Servidores', to: '/' },
        { label: espelho?.servidor?.nome ?? slug, to: `/servidor/${slug}` },
        { label: espelho?.periodo_referencia ?? periodo }
      ]" />
      <div class="nav-actions">
        <ThemeToggle />
        <button class="logout-btn" type="button" @click="auth.logout(); $router.push('/login')">Sair</button>
      </div>
    </div>

    <div v-if="!espelho || !agg" class="empty-state"><p>Carregando…</p></div>
    <template v-else>
      <header class="page-header">
        <h1 class="page-title">{{ espelho.periodo_referencia }}</h1>
        <p class="page-meta">{{ espelho.servidor.nome }}</p>
      </header>

      <div class="stats">
        <div class="stat"><div class="stat-label">Dias c/ Marcação</div><div class="stat-value">{{ agg.daysWithMarcacoes }}</div></div>
        <div class="stat"><div class="stat-label">Horas Homologadas</div><div class="stat-value mono">{{ formatMin(agg.somaCreditoMin) }}</div></div>
        <div class="stat"><div class="stat-label">Carga Esperada</div><div class="stat-value mono">{{ formatMin(agg.cargaEsperadaMin) }}</div></div>
        <div v-if="pct !== null" class="stat"><div class="stat-label">% Carga</div><div :class="['stat-value', pct < 60 ? 'warn' : pct >= 90 ? 'ok' : '']">{{ pct }}%</div></div>
        <div v-if="agg.balanceMin !== null" :class="['stat', agg.balanceMin < -480 ? 'stat-falta' : agg.balanceMin >= 0 ? 'stat-ok' : '']">
          <div class="stat-label">Saldo do Mês</div>
          <div :class="['stat-value', 'mono', agg.balanceMin < 0 ? 'warn' : 'ok']">{{ agg.balanceMin >= 0 ? "+" : "" }}{{ formatMin(agg.balanceMin) }}</div>
        </div>
        <div v-if="faltaMin > 0" class="stat stat-falta">
          <div class="stat-label">Falta</div>
          <div class="stat-value mono warn">{{ formatMin(faltaMin) }}</div>
        </div>
      </div>

      <div v-if="ocorrencias.length > 0" class="section">
        <div class="section-title">Ocorrências</div>
        <div class="occ-list">
          <span v-for="o in ocorrencias" :key="o.type" class="occ-tag">{{ o.type }} <strong>×{{ o.count }}</strong></span>
        </div>
      </div>

      <div class="section">
        <DayTable :registros="registros" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.empty-state { text-align: center; padding: 3rem; color: var(--muted); }
.section { margin-bottom: 1.5rem; }
.section-title { font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px; }
.occ-list { display: flex; flex-wrap: wrap; gap: 6px; }
.occ-tag { font-size: 12px; padding: 3px 10px; background: var(--surface); border: 1px solid var(--border); border-radius: 20px; color: var(--text-2); }
.mono { font-family: var(--mono); }
</style>
