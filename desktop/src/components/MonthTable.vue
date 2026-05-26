<script setup lang="ts">
import type { EspelhoMesResume } from "@/types/dashboard";
import { formatMin, pctCarga } from "@/lib/aggregation";

defineProps<{ meses: EspelhoMesResume[]; slug: string }>();
</script>

<template>
  <div class="table-wrap">
    <table class="month-table">
      <thead>
        <tr>
          <th>Período</th>
          <th class="num">Horas Registradas</th>
          <th class="num">Horas Homologadas</th>
          <th class="num">Carga Esperada</th>
          <th class="num pct-col">% Carga</th>
          <th class="num">Saldo</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="mes in meses" :key="mes.periodoSlug">
          <td>
            <router-link :to="`/servidor/${slug}/${mes.periodoSlug}`" class="period-link">
              {{ mes.periodoReferencia ?? "—" }}
            </router-link>
            <span v-if="mes.status === 'empty'" class="badge-empty">Sem registros</span>
          </td>
          <template v-if="mes.status === 'empty'">
            <td class="num muted">—</td>
            <td class="num muted">—</td>
            <td class="num muted">—</td>
            <td class="num muted">—</td>
            <td class="num muted">—</td>
          </template>
          <template v-else>
            <td class="num mono">{{ formatMin(mes.somaHrMin) }}</td>
            <td class="num mono">{{ formatMin(mes.somaCreditoMin) }}</td>
            <td class="num mono">{{ formatMin(mes.cargaEsperadaMin) }}</td>
            <td class="num pct-col">
              <template v-if="pctCarga(mes.somaCreditoMin, mes.cargaEsperadaMin) !== null">
                <div class="pct-wrap">
                  <div class="pbar"><div class="pbar-fill" :class="pctCarga(mes.somaCreditoMin, mes.cargaEsperadaMin)! < 60 ? 'pbar-warn' : ''" :style="{ width: Math.min(100, pctCarga(mes.somaCreditoMin, mes.cargaEsperadaMin)!) + '%' }"></div></div>
                  <span :class="['pct-num', pctCarga(mes.somaCreditoMin, mes.cargaEsperadaMin)! < 60 ? 'val-warn' : '']">{{ pctCarga(mes.somaCreditoMin, mes.cargaEsperadaMin) }}%</span>
                </div>
              </template>
              <span v-else class="muted">—</span>
            </td>
            <td :class="['num', 'mono', mes.balanceMin !== null && mes.balanceMin < 0 ? 'val-warn' : mes.balanceMin !== null && mes.balanceMin > 0 ? 'val-ok' : '']">
              {{ mes.balanceMin !== null ? (mes.balanceMin >= 0 ? '+' : '') + formatMin(mes.balanceMin) : '—' }}
            </td>
          </template>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-wrap { overflow-x: auto; border-radius: var(--radius); border: 1px solid var(--border); }
.month-table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 620px; }
.month-table th { text-align: left; padding: 10px 16px; background: var(--surface-2); border-bottom: 1px solid var(--border); font-size: 11px; font-weight: 500; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; white-space: nowrap; }
.month-table td { padding: 12px 16px; border-bottom: 1px solid var(--border); white-space: nowrap; }
.month-table tbody tr:last-child td { border-bottom: none; }
.month-table tbody tr:hover td { background: var(--table-row-hover); }
.num { text-align: right; }
.pct-col { min-width: 140px; }
.mono { font-family: var(--mono); font-size: 12px; }
.muted { color: var(--muted); }
.period-link { color: var(--blue); text-decoration: none; font-weight: 450; }
.period-link:hover { text-decoration: underline; }
.badge-empty { margin-left: 8px; font-size: 10px; font-weight: 500; padding: 2px 7px; border-radius: 20px; background: var(--amber-light); color: var(--amber); }
.val-warn { color: var(--red); font-weight: 500; }
.val-ok { color: var(--green); }
.pct-wrap { display: flex; align-items: center; gap: 8px; justify-content: flex-end; }
.pbar { width: 72px; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; flex-shrink: 0; }
.pbar-fill { height: 100%; background: var(--green); border-radius: 3px; transition: width 0.3s; }
.pbar-warn { background: var(--red); }
.pct-num { font-size: 12px; font-family: var(--mono); min-width: 36px; text-align: right; }
</style>
