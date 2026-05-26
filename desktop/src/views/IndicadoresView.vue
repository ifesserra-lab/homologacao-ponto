<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useServidoresStore } from "@/stores/servidores";
import { useAuthStore } from "@/stores/auth";
import { formatMin, pctCarga, allPeriodos } from "@/lib/aggregation";
import ThemeToggle from "@/components/ThemeToggle.vue";

const store = useServidoresStore();
const auth = useAuthStore();

const servidores = computed(() => store.servidores);
const allMeses = computed(() => allPeriodos(servidores.value.map((s) => s.meses)));

const serverLatest = computed(() => servidores.value.map((s) => {
  const completed = s.meses.filter((m) => m.status === "completed");
  return { servidor: s, latest: completed[completed.length - 1] ?? null };
}));

const ranked = computed(() => [...serverLatest.value].sort((a, b) => (a.latest?.balanceMin ?? Infinity) - (b.latest?.balanceMin ?? Infinity)));

const heatmap = computed(() => servidores.value.map((s) => {
  const byPeriod = new Map(s.meses.map((m) => [m.periodoReferencia, m]));
  return { servidor: s, byPeriod };
}));

const ALERT_THRESH_MIN = -480;
const WARN_PCT = 60;
const alerts = computed(() => {
  const result: { serverName: string; slug: string; period: string | null; msg: string; level: "alert" | "warn" }[] = [];
  for (const { servidor, latest } of serverLatest.value) {
    if (!latest) continue;
    if (latest.balanceMin !== null && latest.balanceMin < ALERT_THRESH_MIN) {
      result.push({ serverName: servidor.nome, slug: servidor.slug, period: latest.periodoReferencia, msg: `Saldo ${formatMin(latest.balanceMin)} — abaixo de −08:00`, level: "alert" });
    }
    const pct = pctCarga(latest.somaCreditoMin, latest.cargaEsperadaMin);
    if (pct !== null && pct < WARN_PCT) {
      result.push({ serverName: servidor.nome, slug: servidor.slug, period: latest.periodoReferencia, msg: `Apenas ${pct}% da carga horária cumprida em ${latest.periodoReferencia}`, level: "warn" });
    }
  }
  return result;
});

const ocorrBreakdown = computed(() => servidores.value.map((s) => {
  const t = { pit: 0, abono: 0, afastamento: 0, recesso: 0, sistema: 0 };
  for (const m of s.meses) {
    if (!m.ocorrenciaDias) continue;
    t.pit += m.ocorrenciaDias.pit; t.abono += m.ocorrenciaDias.abono;
    t.afastamento += m.ocorrenciaDias.afastamento; t.recesso += m.ocorrenciaDias.recesso;
    t.sistema += m.ocorrenciaDias.sistema;
  }
  const total = Object.values(t).reduce((a, b) => a + b, 0);
  return { servidor: s, totals: t, total };
}).filter((x) => x.total > 0).sort((a, b) => b.total - a.total));

const presencaReal = computed(() => serverLatest.value.map(({ servidor, latest }) => {
  if (!latest) return { servidor, pct: null, diasMarcacoes: 0, diasEsperados: 0, periodo: null as string | null };
  const diasEsperados = latest.cargaEsperadaMin > 0 ? Math.round(latest.cargaEsperadaMin / 480) : 0;
  const pct = diasEsperados > 0 ? Math.round((latest.daysWithMarcacoes / diasEsperados) * 100) : null;
  return { servidor, pct, diasMarcacoes: latest.daysWithMarcacoes, diasEsperados, periodo: latest.periodoReferencia };
}).sort((a, b) => (b.pct ?? -1) - (a.pct ?? -1)));

function heatCell(mes: ReturnType<typeof heatmap.value[0]["byPeriod"]["get"]>) {
  if (!mes) return "cell-empty";
  if (mes.status === "empty") return "cell-sem-dados";
  const b = mes.balanceMin;
  if (b === null) return "cell-ok";
  if (b < -480) return "cell-alert";
  if (b < 0) return "cell-warn";
  return "cell-ok";
}

onMounted(() => {
  if (store.servidores.length === 0) store.load();
});
</script>

<template>
  <div class="page-wide">
    <header class="page-header">
      <div class="page-header-row">
        <div>
          <h1 class="page-title">Indicadores</h1>
          <p class="page-meta">SIGRH · {{ servidores.length }} servidores</p>
        </div>
        <div class="nav-actions">
          <ThemeToggle />
          <button class="logout-btn" type="button" @click="auth.logout(); $router.push('/login')">Sair</button>
        </div>
      </div>
    </header>

    <div class="tab-nav">
      <router-link class="tab-btn" to="/" active-class="active" exact>Servidores</router-link>
      <router-link class="tab-btn" to="/indicadores" active-class="active">Indicadores</router-link>
    </div>

    <!-- Alertas -->
    <div v-if="alerts.length > 0" class="section">
      <div class="section-title">Alertas</div>
      <div class="alerts">
        <div v-for="a in alerts" :key="`${a.slug}${a.period}`" :class="['alert-item', `alert-${a.level}`]">
          <router-link :to="`/servidor/${a.slug}`" class="alert-name">{{ a.serverName }}</router-link>
          <span class="alert-msg">{{ a.msg }}</span>
        </div>
      </div>
    </div>

    <!-- Ranking Saldo -->
    <div class="section">
      <div class="section-title">Ranking por Saldo (último mês)</div>
      <div class="table-box">
        <table class="history-table">
          <thead><tr><th>#</th><th>Servidor</th><th>Período</th><th class="num">Saldo</th><th>% Carga</th></tr></thead>
          <tbody>
            <tr v-for="(item, i) in ranked" :key="item.servidor.slug">
              <td class="rank-cell">
                <span :class="['rank-badge', i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '']">{{ i + 1 }}</span>
              </td>
              <td><router-link :to="`/servidor/${item.servidor.slug}`">{{ item.servidor.nome }}</router-link></td>
              <td class="muted">{{ item.latest?.periodoReferencia ?? "—" }}</td>
              <td class="num">
                <span v-if="item.latest?.balanceMin !== null && item.latest?.balanceMin !== undefined"
                  :class="['saldo-chip', item.latest.balanceMin > 0 ? 'pos' : item.latest.balanceMin === 0 ? 'zero' : item.latest.balanceMin >= -240 ? 'neg-mild' : 'neg-severe']">
                  {{ item.latest.balanceMin >= 0 ? "+" : "" }}{{ formatMin(item.latest.balanceMin) }}
                </span>
                <span v-else>—</span>
              </td>
              <td>
                <template v-if="item.latest">
                  <div class="progress-bar-wrap">
                    <div class="progress-bar-track"><div :class="['progress-bar-fill', (pctCarga(item.latest.somaCreditoMin, item.latest.cargaEsperadaMin) ?? 100) < 60 ? 'bad' : (pctCarga(item.latest.somaCreditoMin, item.latest.cargaEsperadaMin) ?? 100) < 85 ? 'warn' : '']" :style="`width: ${pctCarga(item.latest.somaCreditoMin, item.latest.cargaEsperadaMin) ?? 0}%`"></div></div>
                    <span class="progress-pct">{{ pctCarga(item.latest.somaCreditoMin, item.latest.cargaEsperadaMin) ?? "—" }}%</span>
                  </div>
                </template>
                <span v-else>—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Taxa de Presença -->
    <div class="section">
      <div class="section-title">Taxa de Presença (último mês completo)</div>
      <div class="table-box">
        <table class="history-table">
          <thead><tr><th>Servidor</th><th>Período</th><th class="num">Dias c/ Batida</th><th class="num">Esperados</th><th>Taxa</th></tr></thead>
          <tbody>
            <tr v-for="p in presencaReal" :key="p.servidor.slug">
              <td><router-link :to="`/servidor/${p.servidor.slug}`">{{ p.servidor.nome }}</router-link></td>
              <td class="muted">{{ p.periodo ?? "—" }}</td>
              <td class="num mono">{{ p.diasMarcacoes }}</td>
              <td class="num mono">{{ p.diasEsperados }}</td>
              <td>
                <div v-if="p.pct !== null" class="progress-bar-wrap">
                  <div class="progress-bar-track"><div :class="['progress-bar-fill', p.pct < 60 ? 'bad' : p.pct < 85 ? 'warn' : '']" :style="`width: ${Math.min(p.pct, 100)}%`"></div></div>
                  <span class="progress-pct">{{ p.pct }}%</span>
                </div>
                <span v-else class="muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Ocorrências -->
    <div v-if="ocorrBreakdown.length > 0" class="section">
      <div class="section-title">Ocorrências por Servidor</div>
      <div class="table-box">
        <table class="history-table">
          <thead><tr><th>Servidor</th><th class="num">Total</th><th>Distribuição</th><th class="num" style="color:#3b82f6">PIT</th><th class="num" style="color:#16a34a">Abono</th><th class="num" style="color:#b45309">Afas.</th><th class="num" style="color:#7c3aed">Recesso</th><th class="num" style="color:#64748b">Sist.</th></tr></thead>
          <tbody>
            <tr v-for="o in ocorrBreakdown" :key="o.servidor.slug">
              <td><router-link :to="`/servidor/${o.servidor.slug}`">{{ o.servidor.nome }}</router-link></td>
              <td class="num mono" style="font-weight:600">{{ o.total }}</td>
              <td>
                <div class="occ-bar">
                  <div v-if="o.totals.pit > 0" class="occ-seg occ-seg-pit" :style="`flex: ${o.totals.pit}`"></div>
                  <div v-if="o.totals.abono > 0" class="occ-seg occ-seg-abono" :style="`flex: ${o.totals.abono}`"></div>
                  <div v-if="o.totals.afastamento > 0" class="occ-seg occ-seg-afas" :style="`flex: ${o.totals.afastamento}`"></div>
                  <div v-if="o.totals.recesso > 0" class="occ-seg occ-seg-recesso" :style="`flex: ${o.totals.recesso}`"></div>
                  <div v-if="o.totals.sistema > 0" class="occ-seg occ-seg-sistema" :style="`flex: ${o.totals.sistema}`"></div>
                </div>
              </td>
              <td class="num mono">{{ o.totals.pit || "—" }}</td>
              <td class="num mono">{{ o.totals.abono || "—" }}</td>
              <td class="num mono">{{ o.totals.afastamento || "—" }}</td>
              <td class="num mono">{{ o.totals.recesso || "—" }}</td>
              <td class="num mono">{{ o.totals.sistema || "—" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Heatmap -->
    <div v-if="allMeses.length > 0" class="section">
      <div class="section-title">Heatmap de Saldo</div>
      <div class="heatmap-scroll">
        <table class="heatmap-table">
          <thead>
            <tr>
              <th class="server-col">Servidor</th>
              <th v-for="p in allMeses" :key="p" class="period-col">{{ p }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="{ servidor, byPeriod } in heatmap" :key="servidor.slug">
              <td class="server-name-cell"><router-link :to="`/servidor/${servidor.slug}`">{{ servidor.nome }}</router-link></td>
              <td v-for="p in allMeses" :key="p" :class="['heat-cell', heatCell(byPeriod.get(p))]" :title="p">
                <span v-if="byPeriod.get(p) && byPeriod.get(p)?.balanceMin !== null" class="heat-val">{{ formatMin(byPeriod.get(p)!.balanceMin) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tab-nav { display: flex; gap: 4px; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); }
.tab-btn { padding: 8px 20px; font-size: 13px; font-weight: 500; color: var(--muted); text-decoration: none; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: color 0.15s, border-color 0.15s; }
.tab-btn:hover, .tab-btn.active { color: var(--text); border-bottom-color: var(--blue); font-weight: 600; }
.section { margin-bottom: 2rem; }
.section-title { font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px; }
.table-box { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow-sm); }
.history-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.history-table th { text-align: left; padding: 10px 16px; background: var(--surface-2); border-bottom: 1px solid var(--border); font-size: 11px; font-weight: 500; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.history-table td { padding: 10px 16px; border-bottom: 1px solid var(--border); }
.history-table tbody tr:last-child td { border-bottom: none; }
.history-table tbody tr:hover td { background: var(--table-row-hover); }
.history-table a { color: var(--blue); text-decoration: none; }
.history-table a:hover { text-decoration: underline; }
.num { text-align: right; }
.mono { font-family: var(--mono); font-size: 12px; }
.muted { color: var(--muted); }
.rank-cell { width: 40px; }
.rank-badge { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; font-size: 11px; font-weight: 700; background: var(--surface-2); color: var(--muted); }
.rank-badge.gold { background: var(--rank-gold-bg); color: var(--rank-gold-text); }
.rank-badge.silver { background: var(--rank-silver-bg); color: var(--rank-silver-text); }
.rank-badge.bronze { background: var(--rank-bronze-bg); color: var(--rank-bronze-text); }
.progress-bar-wrap { display: flex; align-items: center; gap: 6px; }
.progress-bar-track { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; min-width: 60px; }
.progress-bar-fill { height: 100%; background: var(--green); border-radius: 3px; }
.progress-bar-fill.warn { background: var(--amber); }
.progress-bar-fill.bad { background: var(--red); }
.progress-pct { font-size: 11px; font-family: var(--mono); color: var(--muted); min-width: 30px; }
.saldo-chip { font-size: 12px; font-family: var(--mono); font-weight: 500; padding: 2px 8px; border-radius: 20px; }
.saldo-chip.pos { background: var(--green-light); color: var(--green); }
.saldo-chip.zero { background: var(--surface-2); color: var(--muted); }
.saldo-chip.neg-mild { background: var(--amber-light); color: var(--amber); }
.saldo-chip.neg-severe { background: var(--red-light); color: var(--red); }
.alerts { display: flex; flex-direction: column; gap: 6px; }
.alert-item { display: flex; gap: 10px; align-items: baseline; padding: 10px 14px; border-radius: var(--radius-sm); border: 1px solid; font-size: 13px; }
.alert-alert { background: var(--danger-surface); border-color: var(--danger-border); }
.alert-warn { background: var(--notice-border); border-color: var(--notice-border); opacity: 0.9; }
.alert-name { font-weight: 600; color: var(--text); text-decoration: none; }
.alert-msg { color: var(--text-2); }
.occ-bar { display: flex; height: 10px; border-radius: 3px; overflow: hidden; gap: 1px; min-width: 100px; }
.occ-seg { min-width: 3px; height: 100%; border-radius: 2px; }
.occ-seg-pit { background: #3b82f6; } .occ-seg-abono { background: #22c55e; } .occ-seg-afas { background: #f59e0b; } .occ-seg-recesso { background: #a78bfa; } .occ-seg-sistema { background: #94a3b8; }
.heatmap-scroll { overflow-x: auto; }
.heatmap-table { border-collapse: collapse; font-size: 11.5px; white-space: nowrap; }
.heatmap-table th { padding: 8px 10px; background: var(--surface-2); border-bottom: 1px solid var(--border); font-size: 10px; font-weight: 500; color: var(--muted); text-transform: uppercase; }
.server-col { min-width: 160px; text-align: left; }
.period-col { min-width: 80px; text-align: center; }
.server-name-cell { padding: 7px 10px; border-bottom: 1px solid var(--table-border-soft); }
.server-name-cell a { color: var(--text); text-decoration: none; font-size: 12px; }
.heat-cell { padding: 5px 4px; border-bottom: 1px solid var(--table-border-soft); text-align: center; }
.heat-val { font-family: var(--mono); font-size: 10px; }
.cell-empty { background: var(--surface-2); }
.cell-sem-dados { background: var(--amber-light); }
.cell-ok { background: color-mix(in srgb, var(--green) 10%, transparent); }
.cell-warn { background: color-mix(in srgb, var(--amber) 15%, transparent); }
.cell-alert { background: color-mix(in srgb, var(--red) 15%, transparent); }
</style>
