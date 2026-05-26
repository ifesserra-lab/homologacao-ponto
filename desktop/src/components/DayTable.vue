<script setup lang="ts">
import type { RegistroDia } from "@/types/dashboard";
import type { OcorrenciaCategoria } from "@/lib/aggregation";
import { formatMin, parseHHMM, isAbsentWorkDay, JORNADA_MIN, classifyOcorrencia, cleanOcorrenciaTexto } from "@/lib/aggregation";

defineProps<{ registros: RegistroDia[] }>();

interface BadgeInfo { symbol: string; label: string; cls: string }
const BADGE: Record<NonNullable<OcorrenciaCategoria>, BadgeInfo> = {
  pit:         { symbol: "✎", label: "PIT",     cls: "badge-pit" },
  abono:       { symbol: "◎", label: "Abono",   cls: "badge-abono" },
  afastamento: { symbol: "⊘", label: "Afas.",   cls: "badge-afastamento" },
  recesso:     { symbol: "◷", label: "Recesso", cls: "badge-recesso" },
  sistema:     { symbol: "⚠", label: "Sist.",   cls: "badge-sistema" },
};

const DIA_SEMANA: Record<number, string> = { 0:"Domingo",1:"Segunda",2:"Terça",3:"Quarta",4:"Quinta",5:"Sexta",6:"Sábado" };

function cat(r: RegistroDia): OcorrenciaCategoria | null { return classifyOcorrencia(r.ocorrencias ?? []); }

function isIncompleta(r: RegistroDia): boolean {
  if (cat(r) !== null) return false;
  const d = parseHHMM(r.debito);
  return (d !== null && d > 0) || isAbsentWorkDay(r);
}

function displayDate(v: string | null | undefined): string {
  if (!v) return "—";
  const p = v.split("-");
  return p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : v;
}

function displayHHMM(v: string | null | undefined): string {
  if (v === null || v === undefined) return "—";
  const m = parseHHMM(v);
  return m !== null ? formatMin(m) : v;
}

function displayDebito(r: RegistroDia): { value: string; implicit: boolean } {
  if (r.debito !== null && r.debito !== undefined) {
    const m = parseHHMM(r.debito);
    if (m !== null && m > 0) return { value: `-${formatMin(m)}`, implicit: false };
    if (m === 0) return { value: "—", implicit: false };
    return { value: r.debito, implicit: false };
  }
  if (isAbsentWorkDay(r)) return { value: `-${formatMin(JORNADA_MIN)}`, implicit: true };
  return { value: "—", implicit: false };
}

function displayDiaSemana(r: RegistroDia): string {
  if (r.dia_semana) return r.dia_semana;
  if (!r.data) return "—";
  return DIA_SEMANA[new Date(r.data + "T12:00:00Z").getUTCDay()] ?? "—";
}

function rowClass(r: RegistroDia): string {
  const c = cat(r);
  if (c) return `row-ocorr row-${c}`;
  if (isIncompleta(r)) return "row-incomplete";
  return "";
}
</script>

<template>
  <div class="table-wrap">
    <table class="day-table">
      <thead>
        <tr>
          <th title="Data">Data</th>
          <th title="Dia da semana">Dia</th>
          <th title="Marcações de ponto">Marcações</th>
          <th class="num" title="Hora Regular">HR</th>
          <th class="num" title="Hora Compensatória">HC</th>
          <th class="num" title="Hora Extra">HE</th>
          <th class="num" title="Hora Abono/Afastamento">HA</th>
          <th class="num" title="Horas Habituais">HH</th>
          <th class="num" title="Crédito">Crédito</th>
          <th class="num" title="Débito">Débito</th>
          <th class="num" title="Saldo no mês">Saldo</th>
          <th class="num" title="Crédito Acumulado">C.Acum.</th>
          <th class="num" title="Diferença Não Compensada">DNC</th>
          <th title="Situação">Situação</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in registros" :key="r.data" :class="rowClass(r)">
          <td class="date">{{ displayDate(r.data) }}</td>
          <td class="muted sm">{{ displayDiaSemana(r) }}</td>
          <td class="marcacoes">
            <template v-if="cat(r)">
              <span :class="BADGE[cat(r)!].cls" :title="(r.ocorrencias ?? []).join('\n')">
                {{ BADGE[cat(r)!].symbol }}&nbsp;{{ cleanOcorrenciaTexto((r.ocorrencias ?? [])[0] ?? "") }}
              </span>
            </template>
            <template v-else-if="r.marcacoes.length > 0">{{ r.marcacoes.join("  ") }}</template>
            <span v-else class="muted">—</span>
          </td>
          <td class="num mono">{{ displayHHMM(r.hr) }}</td>
          <td class="num mono">{{ displayHHMM(r.hc) }}</td>
          <td class="num mono">{{ displayHHMM(r.he) }}</td>
          <td class="num mono">{{ displayHHMM(r.ha) }}</td>
          <td class="num mono">{{ displayHHMM(r.hh) }}</td>
          <td class="num mono">{{ displayHHMM(r.credito) }}</td>
          <td :class="['num', 'mono', isIncompleta(r) ? 'val-warn' : '', displayDebito(r).implicit ? 'val-implicit' : '']">{{ displayDebito(r).value }}</td>
          <td class="num mono muted">{{ displayHHMM(r.saldo_no_mes) }}</td>
          <td class="num mono muted">{{ displayHHMM(r.credito_acumulado) }}</td>
          <td class="num mono">{{ r.dnc ?? "—" }}</td>
          <td class="muted sm">{{ r.situacao ?? "—" }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.day-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.day-table th { text-align: left; padding: 9px 12px; background: var(--surface-2); border-bottom: 1px solid var(--border); font-size: 10.5px; font-weight: 500; color: var(--muted); text-transform: uppercase; letter-spacing: 0.07em; white-space: nowrap; }
.day-table td { padding: 9px 12px; border-bottom: 1px solid var(--table-border-soft); white-space: nowrap; }
.day-table tbody tr:last-child td { border-bottom: none; }
.day-table tbody tr:hover td { background: var(--table-row-hover); }
.row-incomplete td { background: var(--row-incomplete); }
.row-incomplete:hover td { background: var(--row-incomplete-hover); }
.row-pit td { background: color-mix(in srgb, #3b82f6 5%, transparent); }
.row-abono td { background: color-mix(in srgb, #22c55e 6%, transparent); }
.row-afastamento td { background: color-mix(in srgb, #f59e0b 7%, transparent); }
.row-recesso td { background: color-mix(in srgb, #a78bfa 7%, transparent); }
.row-sistema td { background: color-mix(in srgb, #94a3b8 6%, transparent); }
.badge-pit, .badge-abono, .badge-afastamento, .badge-recesso, .badge-sistema { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10.5px; font-weight: 600; letter-spacing: 0.04em; cursor: default; white-space: normal; max-width: 260px; line-height: 1.4; }
.badge-pit { background: color-mix(in srgb, #3b82f6 12%, transparent); color: #3b82f6; border: 1px solid color-mix(in srgb, #3b82f6 30%, transparent); }
.badge-abono { background: color-mix(in srgb, #22c55e 12%, transparent); color: #16a34a; border: 1px solid color-mix(in srgb, #22c55e 35%, transparent); }
.badge-afastamento { background: color-mix(in srgb, #f59e0b 12%, transparent); color: #b45309; border: 1px solid color-mix(in srgb, #f59e0b 35%, transparent); }
.badge-recesso { background: color-mix(in srgb, #a78bfa 12%, transparent); color: #7c3aed; border: 1px solid color-mix(in srgb, #a78bfa 35%, transparent); }
.badge-sistema { background: color-mix(in srgb, #94a3b8 12%, transparent); color: #64748b; border: 1px solid color-mix(in srgb, #94a3b8 35%, transparent); }
.num { text-align: right; }
.mono { font-family: var(--mono); font-size: 11.5px; font-variant-numeric: tabular-nums; }
.muted { color: var(--muted); }
.sm { font-size: 11.5px; }
.date { font-weight: 500; font-variant-numeric: tabular-nums; }
.marcacoes { font-family: var(--mono); font-size: 11.5px; letter-spacing: 0.01em; }
.val-warn { color: var(--red); font-weight: 600; }
.val-implicit { font-style: italic; opacity: 0.75; }
</style>
