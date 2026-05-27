<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useServidoresStore } from "@/stores/servidores";
import { useAuthStore } from "@/stores/auth";
import { crawlerRefreshKey } from "@/stores/crawler";
import {
  checkHomologavel, gerarEmailServidor, periodoToDate,
  RAZAO_LABEL, STATUS_LABEL,
  type HomologacaoResult, type HomologacaoStatus, type BloqueioEntry,
} from "@/lib/homologacao";
import ThemeToggle from "@/components/ThemeToggle.vue";
import TabNav from "@/components/TabNav.vue";
import type { RawEspelho } from "@/types/dashboard";

const store = useServidoresStore();
const auth = useAuthStore();

interface HRow {
  slug: string;
  nome: string;
  periodoReferencia: string;
  periodoSlug: string;
  raw: RawEspelho | null;
  result: HomologacaoResult | null;
  loading: boolean;
}

const rows = ref<HRow[]>([]);
const loadingAll = ref(false);
const expandedKey = ref<string | null>(null);
const emailModal = ref({ show: false, text: "", titulo: "" });
const copied = ref(false);
const filterStatus = ref<"todos" | "bloqueado" | "liberado">("todos");
const filterMeses = ref<1 | 3 | 6 | 0>(3);

function rowKey(r: HRow) { return `${r.slug}::${r.periodoSlug}`; }

function isRecent(periodo: string): boolean {
  if (filterMeses.value === 0) return true;
  const d = periodoToDate(periodo);
  const cutoff = new Date();
  cutoff.setMonth(cutoff.getMonth() - filterMeses.value);
  return d >= cutoff;
}

async function loadRows() {
  loadingAll.value = true;
  if (store.servidores.length === 0) await store.load();

  const draft: HRow[] = [];
  for (const srv of store.servidores) {
    for (const mes of srv.meses) {
      if (!mes.periodoReferencia) continue;
      if (!isRecent(mes.periodoReferencia)) continue;
      draft.push({
        slug: srv.slug,
        nome: srv.nome,
        periodoReferencia: mes.periodoReferencia,
        periodoSlug: mes.periodoSlug,
        raw: null,
        result: null,
        loading: true,
      });
    }
  }
  rows.value = draft;
  loadingAll.value = false;

  await Promise.all(
    draft.map(async (_, idx) => {
      const r = rows.value[idx];
      const raw = await store.getMes(r.slug, r.periodoSlug);
      if (raw) {
        rows.value[idx].raw = raw;
        rows.value[idx].result = checkHomologavel(raw);
      }
      rows.value[idx].loading = false;
    })
  );
}

// Group by servidor (alphabetical), periods sorted descending within each group
const grouped = computed(() => {
  const map = new Map<string, { nome: string; slug: string; rows: HRow[] }>();
  for (const r of rows.value) {
    const show =
      filterStatus.value === "bloqueado" ? r.result?.status === "bloqueado" :
      filterStatus.value === "liberado"  ? r.result?.status === "liberado"  : true;
    if (!show) continue;
    if (!map.has(r.slug)) map.set(r.slug, { nome: r.nome, slug: r.slug, rows: [] });
    map.get(r.slug)!.rows.push(r);
  }
  return Array.from(map.values())
    .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"))
    .map((g) => ({
      ...g,
      rows: g.rows.sort((a, b) => periodoToDate(b.periodoReferencia).getTime() - periodoToDate(a.periodoReferencia).getTime()),
      blocked: g.rows.filter((r) => r.result?.status === "bloqueado"),
    }));
});

const counts = computed(() => {
  const c: Record<HomologacaoStatus | "loading", number> = { liberado: 0, bloqueado: 0, mes_atual: 0, vazio: 0, loading: 0 };
  for (const r of rows.value) {
    if (r.loading) c.loading++;
    else if (r.result) c[r.result.status]++;
  }
  return c;
});

function toggle(r: HRow) {
  const k = rowKey(r);
  expandedKey.value = expandedKey.value === k ? null : k;
}

function openEmailServidor(slug: string) {
  const entries: BloqueioEntry[] = rows.value
    .filter((r) => r.slug === slug && r.result?.status === "bloqueado" && r.raw && r.result)
    .sort((a, b) => periodoToDate(b.periodoReferencia).getTime() - periodoToDate(a.periodoReferencia).getTime())
    .map((r) => ({ nome: r.nome, periodoReferencia: r.periodoReferencia, raw: r.raw!, result: r.result! }));
  if (entries.length === 0) return;
  const primeiroNome = entries[0].nome.split(" ").slice(0, 2).join(" ");
  emailModal.value = {
    show: true,
    text: gerarEmailServidor(entries),
    titulo: `E-mail — ${primeiroNome} (${entries.length} mês${entries.length > 1 ? "es" : ""} bloqueado${entries.length > 1 ? "s" : ""})`,
  };
}

async function copyEmail() {
  await navigator.clipboard.writeText(emailModal.value.text);
  copied.value = true;
  setTimeout(() => { copied.value = false; }, 2000);
}

function buildCSVLines(source: HRow[]): string[] {
  const lines = ["Servidor,Período,Data,Dia da Semana,Tipo de Pendência,Detalhe"];
  for (const r of source.filter((r) => r.result?.status === "bloqueado" && r.result)) {
    for (const dia of r.result!.diasProblema) {
      for (const razao of dia.razoes) {
        lines.push([
          `"${r.nome}"`,
          `"${r.periodoReferencia}"`,
          `"${dia.dataFormatada}"`,
          `"${dia.diaSemana ?? ""}"`,
          `"${RAZAO_LABEL[razao.tipo] ?? razao.tipo}"`,
          `"${razao.detalhe.replace(/"/g, '""')}"`,
        ].join(","));
      }
    }
    if (r.result!.debitoNaoAutorizado) {
      lines.push([
        `"${r.nome}"`, `"${r.periodoReferencia}"`, `""`, `""`,
        `"débito não autorizado"`,
        `"Débito não autorizado no mês: ${r.result!.debitoNaoAutorizado}"`,
      ].join(","));
    }
  }
  return lines;
}

function downloadCSV(lines: string[], filename: string) {
  const blob = new Blob(["﻿" + lines.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

function exportCSV() {
  const sorted = [...rows.value].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  downloadCSV(buildCSVLines(sorted), `pendencias-homologacao-${new Date().toISOString().slice(0, 10)}.csv`);
}

function exportCSVServidor(slug: string, nome: string) {
  const srvRows = rows.value.filter((r) => r.slug === slug);
  const slugNome = nome.split(" ").slice(0, 2).join("-").toLowerCase().replace(/[^a-z0-9-]/g, "");
  downloadCSV(buildCSVLines(srvRows), `pendencias-${slugNome}-${new Date().toISOString().slice(0, 10)}.csv`);
}

function razaoSummary(result: HomologacaoResult): string {
  const parts = result.razoes.map((r) => RAZAO_LABEL[r] ?? r);
  if (result.debitoNaoAutorizado) parts.push(`débito ${result.debitoNaoAutorizado}`);
  return parts.join(" · ") || "—";
}

onMounted(() => loadRows());
watch(crawlerRefreshKey, () => loadRows());
watch(filterMeses, () => loadRows());
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-row">
        <div>
          <h1 class="page-title">Homologação</h1>
          <p class="page-meta">Pré-requisitos por espelho · AX-006 AX-007 AX-008</p>
        </div>
        <div class="nav-actions">
          <ThemeToggle />
          <button class="logout-btn" type="button" @click="auth.logout(); $router.push('/login')">Sair</button>
        </div>
      </div>
    </header>

    <TabNav />

    <!-- Filtros + ações globais -->
    <div class="toolbar">
      <div class="filter-group">
        <span class="filter-label">Período</span>
        <div class="btn-group">
          <button :class="['btn-seg', filterMeses === 1 && 'active']" @click="filterMeses = 1">1 mês</button>
          <button :class="['btn-seg', filterMeses === 3 && 'active']" @click="filterMeses = 3">3 meses</button>
          <button :class="['btn-seg', filterMeses === 6 && 'active']" @click="filterMeses = 6">6 meses</button>
          <button :class="['btn-seg', filterMeses === 0 && 'active']" @click="filterMeses = 0">Todos</button>
        </div>
      </div>
      <div class="filter-group">
        <span class="filter-label">Status</span>
        <div class="btn-group">
          <button :class="['btn-seg', filterStatus === 'todos' && 'active']" @click="filterStatus = 'todos'">Todos</button>
          <button :class="['btn-seg', filterStatus === 'bloqueado' && 'active']" @click="filterStatus = 'bloqueado'">Bloqueados</button>
          <button :class="['btn-seg', filterStatus === 'liberado' && 'active']" @click="filterStatus = 'liberado'">Liberados</button>
        </div>
      </div>

      <div class="counts">
        <span v-if="counts.loading > 0"  class="count-chip loading">{{ counts.loading }} carregando</span>
        <span v-if="counts.bloqueado > 0" class="count-chip bloqueado">{{ counts.bloqueado }} bloqueado{{ counts.bloqueado > 1 ? 's' : '' }}</span>
        <span v-if="counts.liberado > 0"  class="count-chip liberado">{{ counts.liberado }} liberado{{ counts.liberado > 1 ? 's' : '' }}</span>
        <span v-if="counts.mes_atual > 0" class="count-chip mes-atual">{{ counts.mes_atual }} em aberto</span>
        <button
          v-if="counts.bloqueado > 0"
          class="btn-csv"
          :disabled="counts.loading > 0"
          @click="exportCSV"
        >↓ Exportar CSV</button>
      </div>
    </div>

    <div v-if="loadingAll" class="empty-state">Carregando espelhos…</div>
    <div v-else-if="grouped.length === 0" class="empty-state">Nenhum espelho encontrado para os filtros selecionados.</div>

    <!-- Tabela agrupada por servidor -->
    <div v-else class="hom-table">
      <template v-for="group in grouped" :key="group.slug">

        <!-- Cabeçalho do servidor -->
        <div class="srv-header">
          <span class="srv-nome">{{ group.nome }}</span>
          <div class="srv-meta">
            <span v-if="group.blocked.length > 0" class="srv-blocked-count">
              {{ group.blocked.length }} bloqueado{{ group.blocked.length > 1 ? 's' : '' }}
            </span>
          </div>
          <button
            v-if="group.blocked.length > 0 && counts.loading === 0"
            class="btn-csv-srv"
            @click="exportCSVServidor(group.slug, group.nome)"
          >↓ CSV</button>
          <button
            v-if="group.blocked.length > 0 && counts.loading === 0"
            class="btn-email-srv"
            @click="openEmailServidor(group.slug)"
          >✉ E-mail</button>
        </div>

        <!-- Linhas de período -->
        <template v-for="row in group.rows" :key="rowKey(row)">
          <div
            :class="['hom-row', row.result?.status, { expanded: expandedKey === rowKey(row) }]"
            @click="row.result?.status === 'bloqueado' && toggle(row)"
          >
            <div class="hom-periodo">{{ row.periodoReferencia }}</div>

            <div class="hom-status">
              <span v-if="row.loading" class="badge badge--loading">…</span>
              <span v-else-if="row.result" :class="['badge', `badge--${row.result.status}`]">
                {{ STATUS_LABEL[row.result.status] }}
              </span>
            </div>

            <div class="hom-razao">
              <span v-if="row.loading" class="razao-text muted">verificando…</span>
              <span v-else-if="row.result?.status === 'bloqueado'" class="razao-text warn">
                {{ razaoSummary(row.result) }}
              </span>
              <span v-else class="razao-text muted">—</span>
            </div>

            <div class="hom-actions" @click.stop>
              <button
                v-if="row.result?.status === 'bloqueado'"
                :class="['btn-icon', expandedKey === rowKey(row) && 'active']"
                title="Ver detalhes"
                @click="toggle(row)"
              >{{ expandedKey === rowKey(row) ? '▲' : '▼' }}</button>
            </div>
          </div>

          <!-- Detalhes expandidos -->
          <div v-if="expandedKey === rowKey(row) && row.result" class="hom-detail">
            <template v-if="row.result.diasProblema.length > 0">
              <div class="detail-section-title">Dias com pendência</div>
              <div v-for="dia in row.result.diasProblema" :key="dia.data" class="detail-dia">
                <span class="detail-dia-data">
                  {{ dia.dataFormatada }}<span v-if="dia.diaSemana" class="muted"> ({{ dia.diaSemana }})</span>
                </span>
                <div class="detail-dia-razoes">
                  <span
                    v-for="(r, i) in dia.razoes" :key="i"
                    :class="['razao-pill', `razao-pill--${r.tipo}`]"
                  >{{ r.detalhe }}</span>
                </div>
              </div>
            </template>
            <div v-if="row.result.debitoNaoAutorizado" class="detail-debito">
              <span class="detail-section-title">Débito não autorizado</span>
              <span class="debito-val">{{ row.result.debitoNaoAutorizado }}</span>
              <span class="muted"> — há horas de débito não compensadas neste mês</span>
            </div>
          </div>
        </template>

      </template>
    </div>

    <!-- Modal de e-mail -->
    <Teleport to="body">
      <div v-if="emailModal.show" class="modal-overlay" @click.self="emailModal.show = false">
        <div class="modal">
          <div class="modal-header">
            <span class="modal-title">{{ emailModal.titulo }}</span>
            <button class="modal-close" @click="emailModal.show = false">✕</button>
          </div>
          <pre class="email-body">{{ emailModal.text }}</pre>
          <div class="modal-footer">
            <button class="btn-copy" :class="{ copied }" @click="copyEmail">
              {{ copied ? '✓ Copiado!' : '⎘ Copiar' }}
            </button>
            <button class="btn-close-modal" @click="emailModal.show = false">Fechar</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* ── Toolbar ── */
.toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; margin-bottom: 1.5rem; }
.filter-group { display: flex; align-items: center; gap: 8px; }
.filter-label { font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
.btn-group { display: flex; border: 1px solid var(--border-mid); border-radius: var(--radius-sm); overflow: hidden; }
.btn-seg { padding: 5px 12px; font-size: 12px; font-weight: 500; background: var(--surface); color: var(--text-2); border: none; border-right: 1px solid var(--border); cursor: pointer; transition: background 0.15s, color 0.15s; }
.btn-seg:last-child { border-right: none; }
.btn-seg.active { background: var(--blue); color: #fff; }
.btn-seg:hover:not(.active) { background: var(--surface-2); }

.counts { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-left: auto; }
.count-chip { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 20px; }
.count-chip.bloqueado { background: #fde8e8; color: #b91c1c; }
.count-chip.liberado { background: var(--green-light, #ddedea); color: var(--green, #0f7b6c); }
.count-chip.mes-atual { background: #fef3c7; color: #92400e; }
.count-chip.loading { background: var(--surface-2); color: var(--muted); }

.btn-csv { padding: 5px 13px; background: var(--surface); color: var(--text-2); border: 1px solid var(--border-mid); border-radius: var(--radius-sm); font-size: 12px; font-weight: 500; cursor: pointer; transition: background 0.15s; }
.btn-csv:hover { background: var(--surface-2); color: var(--text); }
.btn-csv:disabled { opacity: 0.4; cursor: default; }

/* ── Table ── */
.hom-table { border: 1px solid var(--border); border-radius: var(--radius-lg); overflow: hidden; }

/* Servidor group header */
.srv-header {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 16px;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border);
}
.srv-nome { font-size: 13px; font-weight: 700; color: var(--text); flex: 1; }
.srv-meta { display: flex; align-items: center; gap: 6px; }
.srv-blocked-count { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 20px; background: #fde8e8; color: #b91c1c; }
.btn-csv-srv { padding: 4px 10px; background: var(--surface); color: var(--text-2); border: 1px solid var(--border-mid); border-radius: var(--radius-sm); font-size: 11px; font-weight: 500; cursor: pointer; white-space: nowrap; transition: background 0.15s; }
.btn-csv-srv:hover { background: var(--surface-2); color: var(--text); }
.btn-email-srv { padding: 4px 12px; background: var(--blue-light, #e8f2fc); color: var(--blue); border: 1px solid transparent; border-radius: var(--radius-sm); font-size: 11px; font-weight: 600; cursor: pointer; white-space: nowrap; transition: background 0.15s, color 0.15s; }
.btn-email-srv:hover { background: var(--blue); color: #fff; }

/* Period rows */
.hom-row {
  display: grid;
  grid-template-columns: 140px 110px 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 9px 16px 9px 28px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  transition: background 0.1s;
}
.hom-row:last-child { border-bottom: none; }
.hom-row.bloqueado { cursor: pointer; }
.hom-row.bloqueado:hover, .hom-row.expanded { background: var(--surface-2); }

.hom-periodo { font-size: 12px; font-weight: 500; color: var(--text-2); font-family: var(--mono); }
.hom-status { display: flex; }
.hom-razao { font-size: 12px; }
.hom-actions { display: flex; align-items: center; gap: 6px; }

/* Badges */
.badge { font-size: 11px; font-weight: 600; padding: 2px 9px; border-radius: 20px; }
.badge--liberado { background: var(--green-light, #ddedea); color: var(--green, #0f7b6c); }
.badge--bloqueado { background: #fde8e8; color: #b91c1c; }
.badge--mes_atual { background: #fef3c7; color: #92400e; }
.badge--vazio { background: var(--surface-2); color: var(--muted); }
.badge--loading { background: var(--surface-2); color: var(--muted); }

.razao-text.warn { color: #b91c1c; }
.razao-text.muted { color: var(--muted); }

.btn-icon { padding: 3px 8px; background: transparent; color: var(--muted); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 11px; cursor: pointer; }
.btn-icon:hover, .btn-icon.active { color: var(--text); }

/* ── Detail panel ── */
.hom-detail {
  background: var(--surface-2); border-bottom: 1px solid var(--border);
  padding: 12px 20px 16px 36px;
  display: flex; flex-direction: column; gap: 10px;
}
.detail-section-title { font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.detail-dia { display: flex; align-items: flex-start; gap: 12px; padding: 6px 0; border-bottom: 1px solid var(--border); }
.detail-dia:last-child { border-bottom: none; }
.detail-dia-data { font-size: 12px; font-weight: 600; font-family: var(--mono); white-space: nowrap; min-width: 130px; color: var(--text); }
.detail-dia-razoes { display: flex; flex-wrap: wrap; gap: 6px; }
.razao-pill { font-size: 11px; padding: 2px 8px; border-radius: 4px; color: var(--text-2); background: var(--surface); border: 1px solid var(--border-mid); }
.razao-pill--dias_pendentes { background: #fef3c7; color: #92400e; border-color: #f59e0b44; }
.razao-pill--he_nao_autorizado { background: #fde8e8; color: #b91c1c; border-color: #f8717144; }
.razao-pill--debito_nao_autorizado { background: #fde8e8; color: #b91c1c; border-color: #f8717144; }
.razao-pill--marcacoes_incompletas { background: #fffbeb; color: #78350f; border-color: #fbbf2444; }
.detail-debito { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.debito-val { font-family: var(--mono); font-weight: 700; color: #b91c1c; }

/* ── Email Modal ── */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 9999; }
.modal { background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border-mid); box-shadow: 0 20px 60px rgba(0,0,0,0.25); width: min(680px, calc(100vw - 32px)); max-height: calc(100vh - 64px); display: flex; flex-direction: column; overflow: hidden; }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; border-bottom: 1px solid var(--border); flex-shrink: 0; }
.modal-title { font-size: 13px; font-weight: 600; color: var(--text); }
.modal-close { background: none; border: none; color: var(--muted); font-size: 14px; cursor: pointer; padding: 2px 6px; border-radius: 4px; }
.modal-close:hover { color: var(--text); background: var(--surface-2); }
.email-body { font-family: var(--mono); font-size: 12px; line-height: 1.7; color: var(--text); background: var(--surface-2); padding: 20px; margin: 0; overflow-y: auto; flex: 1; white-space: pre-wrap; word-break: break-word; border-bottom: 1px solid var(--border); }
.modal-footer { display: flex; gap: 8px; justify-content: flex-end; padding: 12px 20px; flex-shrink: 0; }
.btn-copy { padding: 6px 16px; background: var(--blue); color: #fff; border: none; border-radius: var(--radius-sm); font-size: 12px; font-weight: 600; cursor: pointer; }
.btn-copy:hover { background: #1a6ec0; }
.btn-copy.copied { background: var(--green, #0f7b6c); }
.btn-close-modal { padding: 6px 14px; background: transparent; color: var(--muted); border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 12px; cursor: pointer; }
.btn-close-modal:hover { color: var(--text); }

.empty-state { text-align: center; padding: 3rem; color: var(--muted); }
.muted { color: var(--muted); }
</style>
