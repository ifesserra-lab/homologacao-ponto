<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useServidoresStore } from "@/stores/servidores";
import { useAuthStore } from "@/stores/auth";
import { crawlerRefreshKey } from "@/stores/crawler";
import { formatMin, pctCarga } from "@/lib/aggregation";
import MonthTable from "@/components/MonthTable.vue";
import ThemeToggle from "@/components/ThemeToggle.vue";
import Breadcrumb from "@/components/Breadcrumb.vue";
import type { ServidorResume } from "@/types/dashboard";

const route = useRoute();
const router = useRouter();
const store = useServidoresStore();
const auth = useAuthStore();
const slug = route.params.slug as string;
const activeTab = ref<"historico" | "indicadores">("historico");
const servidor = ref<ServidorResume | null>(null);

const completedMeses = computed(() => servidor.value?.meses.filter((m) => m.status === "completed") ?? []);
const latestBalance = computed(() => completedMeses.value[completedMeses.value.length - 1]?.balanceMin ?? null);
const overallPct = computed(() => {
  const totalCred = completedMeses.value.reduce((s, m) => s + m.somaCreditoMin, 0);
  const totalCarga = completedMeses.value.reduce((s, m) => s + m.cargaEsperadaMin, 0);
  return totalCarga > 0 ? Math.min(100, Math.round((totalCred / totalCarga) * 100)) : null;
});
const totalOcorr = computed(() => {
  const t = { pit: 0, abono: 0, afastamento: 0, recesso: 0, sistema: 0 };
  for (const m of completedMeses.value) {
    if (!m.ocorrenciaDias) continue;
    t.pit += m.ocorrenciaDias.pit; t.abono += m.ocorrenciaDias.abono;
    t.afastamento += m.ocorrenciaDias.afastamento; t.recesso += m.ocorrenciaDias.recesso;
    t.sistema += m.ocorrenciaDias.sistema;
  }
  return t;
});
const totalOcorrSum = computed(() => Object.values(totalOcorr.value).reduce((a, b) => a + b, 0));
const presencaByMonth = computed(() => completedMeses.value.map((m) => {
  const diasEsperados = m.cargaEsperadaMin > 0 ? Math.round(m.cargaEsperadaMin / 480) : 0;
  const pct = diasEsperados > 0 ? Math.round((m.daysWithMarcacoes / diasEsperados) * 100) : null;
  return { mes: m, diasEsperados, pct };
}));
const ocorrByMonth = computed(() => completedMeses.value.map((m) => {
  const o = m.ocorrenciaDias ?? { pit: 0, abono: 0, afastamento: 0, recesso: 0, sistema: 0 };
  return { mes: m, ocorr: o, total: Object.values(o).reduce((a, b) => a + b, 0) };
}));
const meuAfastamentos = computed(() => store.afastamentos.filter((a) => a.serverSlug === slug && a.categoria === "afastamento"));
const pitByMonth = computed(() => completedMeses.value.filter((m) => m.ocorrenciaDias && m.ocorrenciaDias.pit > 0).map((m) => ({ mes: m, diasPit: m.ocorrenciaDias!.pit, pitPct: m.pitJustificadoPct })));

function formatDate(iso: string): string {
  if (!iso) return "—";
  const p = iso.split("-");
  return p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : iso;
}

onMounted(async () => {
  if (store.servidores.length === 0) await store.load();
  const s = await store.getServidor(slug);
  if (!s) { router.push("/"); return; }
  servidor.value = s;
});
watch(crawlerRefreshKey, () => store.load());
</script>

<template>
  <div class="page">
    <div class="nav-row">
      <Breadcrumb :items="[{ label: 'Servidores', to: '/' }, { label: servidor?.nome ?? slug }]" />
      <div class="nav-actions">
        <ThemeToggle />
        <button class="logout-btn" type="button" @click="auth.logout(); $router.push('/login')">Sair</button>
      </div>
    </div>

    <div v-if="!servidor" class="empty-state"><p>Carregando…</p></div>
    <template v-else>
      <header class="page-header">
        <h1 class="page-title">{{ servidor.nome }}</h1>
        <p class="page-meta">
          <template v-if="servidor.siape">SIAPE {{ servidor.siape }} · </template>
          {{ servidor.periodoRange }}
        </p>
      </header>

      <div class="stats">
        <div class="stat"><div class="stat-label">Total</div><div class="stat-value">{{ servidor.totalMeses }}</div></div>
        <div class="stat"><div class="stat-label">Completos</div><div class="stat-value">{{ completedMeses.length }}</div></div>
        <div v-if="servidor.meses.filter(m => m.status === 'empty').length > 0" class="stat">
          <div class="stat-label">Sem registros</div>
          <div class="stat-value warn">{{ servidor.meses.filter(m => m.status === 'empty').length }}</div>
        </div>
        <div v-if="latestBalance !== null" :class="['stat', latestBalance < -480 ? 'stat-falta' : latestBalance >= 0 ? 'stat-ok' : '']">
          <div class="stat-label">Saldo atual</div>
          <div :class="['stat-value', 'mono', latestBalance < 0 ? 'warn' : 'ok']">{{ latestBalance >= 0 ? "+" : "" }}{{ formatMin(latestBalance) }}</div>
        </div>
        <div v-if="overallPct !== null" class="stat">
          <div class="stat-label">% Carga cumprida</div>
          <div :class="['stat-value', overallPct < 60 ? 'warn' : overallPct >= 90 ? 'ok' : '']">{{ overallPct }}%</div>
        </div>
      </div>

      <div class="tab-bar">
        <button :class="['tab-btn', activeTab === 'historico' ? 'active' : '']" @click="activeTab = 'historico'">Histórico</button>
        <button :class="['tab-btn', activeTab === 'indicadores' ? 'active' : '']" @click="activeTab = 'indicadores'">Indicadores</button>
      </div>

      <!-- Histórico -->
      <div v-show="activeTab === 'historico'">
        <div v-if="completedMeses.length > 0" class="section">
          <div class="section-title">Série histórica</div>
          <div class="table-box">
            <table class="history-table">
              <thead>
                <tr>
                  <th>Período</th><th>Horas Registradas</th><th>Horas Homologadas</th><th>Carga Esperada</th><th>% Carga</th><th>Saldo do Mês</th><th>Dias com Marcação</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in completedMeses" :key="m.periodoSlug">
                  <td><router-link :to="`/servidor/${slug}/${m.periodoSlug}`">{{ m.periodoReferencia }}</router-link></td>
                  <td class="mono">{{ formatMin(m.somaHrMin) }}</td>
                  <td class="mono">{{ formatMin(m.somaCreditoMin) }}</td>
                  <td class="mono">{{ formatMin(m.cargaEsperadaMin) }}</td>
                  <td>
                    <div v-if="pctCarga(m.somaCreditoMin, m.cargaEsperadaMin) !== null" class="progress-bar-wrap">
                      <div class="progress-bar-track">
                        <div :class="['progress-bar-fill', pctCarga(m.somaCreditoMin, m.cargaEsperadaMin)! < 60 ? 'bad' : pctCarga(m.somaCreditoMin, m.cargaEsperadaMin)! < 85 ? 'warn' : '']" :style="`width: ${pctCarga(m.somaCreditoMin, m.cargaEsperadaMin)}%`"></div>
                      </div>
                      <span class="progress-pct">{{ pctCarga(m.somaCreditoMin, m.cargaEsperadaMin) }}%</span>
                    </div>
                    <span v-else>—</span>
                  </td>
                  <td>
                    <span v-if="m.balanceMin !== null" :class="['saldo-chip', m.balanceMin > 0 ? 'pos' : m.balanceMin === 0 ? 'zero' : m.balanceMin >= -240 ? 'neg-mild' : 'neg-severe']">
                      {{ m.balanceMin >= 0 ? "+" : "" }}{{ formatMin(m.balanceMin) }}
                    </span>
                    <span v-else>—</span>
                  </td>
                  <td>{{ m.daysWithMarcacoes }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <MonthTable :meses="servidor.meses" :slug="slug" />
      </div>

      <!-- Indicadores -->
      <div v-show="activeTab === 'indicadores'">
        <div v-if="completedMeses.length > 0" class="section" style="margin-top: 8px;">

          <!-- KPIs -->
          <div v-if="totalOcorrSum > 0 || meuAfastamentos.length > 0" class="stats" style="margin-bottom: 20px;">
            <div v-if="totalOcorrSum > 0" class="stat"><div class="stat-label">Ocorrências Total</div><div class="stat-value">{{ totalOcorrSum }}</div></div>
            <div v-if="totalOcorr.abono > 0" class="stat stat-abono"><div class="stat-label">Dias Abono</div><div class="stat-value kpi-green-val">{{ totalOcorr.abono }}</div></div>
            <div v-if="totalOcorr.afastamento > 0" class="stat stat-afas"><div class="stat-label">Dias Afastamento</div><div class="stat-value kpi-amber-val">{{ totalOcorr.afastamento }}</div></div>
            <div v-if="totalOcorr.pit > 0" class="stat stat-pit"><div class="stat-label">Dias PIT</div><div class="stat-value kpi-blue-val">{{ totalOcorr.pit }}</div></div>
            <div v-if="totalOcorr.recesso > 0" class="stat stat-recesso"><div class="stat-label">Dias Recesso</div><div class="stat-value kpi-purple-val">{{ totalOcorr.recesso }}</div></div>
            <div v-if="meuAfastamentos.length > 0" class="stat stat-falta"><div class="stat-label">Afastamentos</div><div class="stat-value warn">{{ meuAfastamentos.length }}</div></div>
          </div>

          <!-- Presença -->
          <div class="section-sub-title">Taxa de Presença por Batida Real</div>
          <div class="table-box" style="margin-bottom: 20px;">
            <table class="history-table">
              <thead><tr><th>Período</th><th style="text-align:right">Dias c/ Batida</th><th style="text-align:right">Dias Esperados</th><th>Taxa</th></tr></thead>
              <tbody>
                <tr v-for="{ mes, diasEsperados, pct } in presencaByMonth" :key="mes.periodoSlug">
                  <td><router-link :to="`/servidor/${slug}/${mes.periodoSlug}`">{{ mes.periodoReferencia }}</router-link></td>
                  <td class="mono" style="text-align:right">{{ mes.daysWithMarcacoes }}</td>
                  <td class="mono" style="text-align:right">{{ diasEsperados }}</td>
                  <td>
                    <div v-if="pct !== null" class="progress-bar-wrap">
                      <div class="progress-bar-track"><div :class="['progress-bar-fill', pct < 60 ? 'bad' : pct < 85 ? 'warn' : '']" :style="`width: ${Math.min(pct, 100)}%`"></div></div>
                      <span class="progress-pct">{{ pct }}%</span>
                    </div>
                    <span v-else style="color: var(--muted)">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Ocorrências por Mês -->
          <template v-if="ocorrByMonth.some(x => x.total > 0)">
            <div class="section-sub-title">Ocorrências por Mês</div>
            <div class="table-box" style="margin-bottom: 20px;">
              <table class="history-table">
                <thead>
                  <tr>
                    <th>Período</th><th>Total</th><th>Distribuição</th>
                    <th style="text-align:right; color:#3b82f6">PIT</th>
                    <th style="text-align:right; color:#16a34a">Abono</th>
                    <th style="text-align:right; color:#b45309">Afas.</th>
                    <th style="text-align:right; color:#7c3aed">Recesso</th>
                    <th style="text-align:right; color:#64748b">Sist.</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="{ mes, ocorr, total } in ocorrByMonth" :key="mes.periodoSlug">
                    <td><router-link :to="`/servidor/${slug}/${mes.periodoSlug}`">{{ mes.periodoReferencia }}</router-link></td>
                    <td class="mono" style="font-weight:600">{{ total || "—" }}</td>
                    <td style="min-width:120px">
                      <div v-if="total > 0" class="occ-bar">
                        <div v-if="ocorr.pit > 0" class="occ-seg occ-seg-pit" :style="`flex: ${ocorr.pit}`" :title="`PIT: ${ocorr.pit}`"></div>
                        <div v-if="ocorr.abono > 0" class="occ-seg occ-seg-abono" :style="`flex: ${ocorr.abono}`"></div>
                        <div v-if="ocorr.afastamento > 0" class="occ-seg occ-seg-afas" :style="`flex: ${ocorr.afastamento}`"></div>
                        <div v-if="ocorr.recesso > 0" class="occ-seg occ-seg-recesso" :style="`flex: ${ocorr.recesso}`"></div>
                        <div v-if="ocorr.sistema > 0" class="occ-seg occ-seg-sistema" :style="`flex: ${ocorr.sistema}`"></div>
                      </div>
                      <span v-else style="color: var(--muted)">—</span>
                    </td>
                    <td class="mono" style="text-align:right">{{ ocorr.pit || "—" }}</td>
                    <td class="mono" style="text-align:right">{{ ocorr.abono || "—" }}</td>
                    <td class="mono" style="text-align:right">{{ ocorr.afastamento || "—" }}</td>
                    <td class="mono" style="text-align:right">{{ ocorr.recesso || "—" }}</td>
                    <td class="mono" style="text-align:right">{{ ocorr.sistema || "—" }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>

          <!-- PIT vs Real -->
          <template v-if="pitByMonth.length > 0">
            <div class="section-sub-title">Carga PIT vs. Real</div>
            <div class="table-box" style="margin-bottom: 20px;">
              <table class="history-table">
                <thead><tr><th>Período</th><th style="text-align:right">Dias PIT</th><th style="text-align:right">Dias c/ Batida</th><th>% Justificado</th></tr></thead>
                <tbody>
                  <tr v-for="{ mes, diasPit, pitPct } in pitByMonth" :key="mes.periodoSlug">
                    <td><router-link :to="`/servidor/${slug}/${mes.periodoSlug}`">{{ mes.periodoReferencia }}</router-link></td>
                    <td class="mono" style="text-align:right">{{ diasPit }}</td>
                    <td class="mono" style="text-align:right">{{ mes.daysWithMarcacoes }}</td>
                    <td>
                      <div v-if="pitPct !== null" class="progress-bar-wrap">
                        <div class="progress-bar-track"><div class="progress-bar-fill occ-fill-pit" :style="`width: ${Math.min(pitPct, 100)}%`"></div></div>
                        <span class="progress-pct">{{ pitPct }}%</span>
                      </div>
                      <span v-else style="color: var(--muted)">—</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>

          <!-- Afastamentos -->
          <template v-if="meuAfastamentos.length > 0">
            <div class="section-sub-title">Afastamentos Registrados</div>
            <div class="table-box" style="margin-bottom: 20px;">
              <table class="history-table">
                <thead><tr><th>Tipo</th><th>Início</th><th>Fim</th><th style="text-align:right">Dias</th></tr></thead>
                <tbody>
                  <tr v-for="af in meuAfastamentos" :key="`${af.dataInicio}${af.texto}`">
                    <td style="font-size: 12px; max-width: 280px; white-space: normal;">{{ af.texto }}</td>
                    <td class="mono" style="font-size:12px">{{ formatDate(af.dataInicio) }}</td>
                    <td class="mono" style="font-size:12px">{{ formatDate(af.dataFim) }}</td>
                    <td class="mono" style="text-align:right">{{ af.dias }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.empty-state { text-align: center; padding: 3rem 1rem; color: var(--muted); }
.tab-bar { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 1px solid var(--border); }
.tab-btn { padding: 8px 20px; font-size: 13px; font-weight: 500; border: none; background: none; color: var(--muted); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: color 0.15s, border-color 0.15s; }
.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--text); border-bottom-color: var(--blue); font-weight: 600; }
.section { margin-bottom: 1.5rem; }
.section-title { font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px; }
.section-sub-title { font-size: 13px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin: 16px 0 8px; }
.table-box { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow-sm); }
.history-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.history-table th { text-align: left; padding: 10px 16px; background: var(--surface-2); border-bottom: 1px solid var(--border); font-size: 11px; font-weight: 500; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.history-table td { padding: 10px 16px; border-bottom: 1px solid var(--border); }
.history-table tbody tr:last-child td { border-bottom: none; }
.history-table tbody tr:hover td { background: var(--table-row-hover); }
.history-table a { color: var(--blue); text-decoration: none; }
.history-table a:hover { text-decoration: underline; }
.mono { font-family: var(--mono); font-size: 12px; }
.progress-bar-wrap { display: flex; align-items: center; gap: 6px; }
.progress-bar-track { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; min-width: 60px; }
.progress-bar-fill { height: 100%; background: var(--green); border-radius: 3px; transition: width 0.3s; }
.progress-bar-fill.warn { background: var(--amber); }
.progress-bar-fill.bad { background: var(--red); }
.progress-pct { font-size: 11px; font-family: var(--mono); color: var(--muted); min-width: 30px; }
.saldo-chip { font-size: 12px; font-family: var(--mono); font-weight: 500; padding: 2px 8px; border-radius: 20px; }
.saldo-chip.pos { background: var(--green-light); color: var(--green); }
.saldo-chip.zero { background: var(--surface-2); color: var(--muted); }
.saldo-chip.neg-mild { background: var(--amber-light); color: var(--amber); }
.saldo-chip.neg-severe { background: var(--red-light); color: var(--red); }
.occ-bar { display: flex; height: 10px; border-radius: 3px; overflow: hidden; gap: 1px; min-width: 100px; }
.occ-seg { min-width: 3px; height: 100%; border-radius: 2px; }
.occ-seg-pit { background: #3b82f6; } .occ-seg-abono { background: #22c55e; } .occ-seg-afas { background: #f59e0b; } .occ-seg-recesso { background: #a78bfa; } .occ-seg-sistema { background: #94a3b8; }
.occ-fill-pit { background: #3b82f6 !important; }
.stat-abono { border-color: color-mix(in srgb, #22c55e 40%, transparent); }
.stat-afas { border-color: color-mix(in srgb, #f59e0b 40%, transparent); }
.stat-pit { border-color: color-mix(in srgb, #3b82f6 40%, transparent); }
.stat-recesso { border-color: color-mix(in srgb, #a78bfa 40%, transparent); }
.kpi-green-val { color: #16a34a; } .kpi-amber-val { color: #b45309; } .kpi-blue-val { color: #3b82f6; } .kpi-purple-val { color: #7c3aed; }
</style>
