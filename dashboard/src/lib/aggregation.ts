import type { RegistroDia } from "../types/dashboard";

export const JORNADA_MIN = 480; // 8 horas

export interface MonthAggregate {
  daysWithMarcacoes: number;
  somaCreditoMin: number;   // sum(credito) = horas homologadas
  somaHrMin: number;        // sum(hr) = horas registradas
  somaDebitoMin: number;
  somaHhMin: number;
  cargaEsperadaMin: number; // weekdays in month × 8h, minus past holidays
  dncFinalMin: number | null;
  /** Last non-null credito_acumulado — authoritative balance from SIGRH. Negative = falta. */
  balanceMin: number | null;
}

/** True when weekday (Mon–Fri) with no punches and no credit entry (holiday/exempt). */
export function isAbsentWorkDay(r: RegistroDia): boolean {
  if (r.marcacoes.length > 0) return false;
  if (r.credito !== null && r.credito !== undefined) return false;
  if (r.debito !== null && r.debito !== undefined) return false;
  if (!r.data) return false;
  const dow = new Date(r.data + "T12:00:00Z").getUTCDay(); // 0=Sun, 6=Sat
  return dow >= 1 && dow <= 5;
}

/** Returns effective debito in minutes: explicit debito or implicit jornada for absent work days. */
export function effectiveDebitoMin(r: RegistroDia): number {
  const explicit = parseHHMM(r.debito);
  if (explicit !== null) return explicit;
  return isAbsentWorkDay(r) ? JORNADA_MIN : 0;
}

export function parseHHMM(s: string | null | undefined): number | null {
  if (!s) return null;
  const parts = s.split(":");
  if (parts.length !== 2) return null;
  const h = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  if (isNaN(h) || isNaN(m)) return null;
  return h * 60 + m;
}

/** Parses signed time strings like "-09:10" → -550, "01:30" → 90. */
export function parseSignedHHMM(s: string | null | undefined): number | null {
  if (!s) return null;
  const negative = s.startsWith("-");
  const abs = negative ? s.slice(1) : s;
  const parsed = parseHHMM(abs);
  if (parsed === null) return null;
  return negative ? -parsed : parsed;
}

export function formatMin(minutes: number | null): string {
  if (minutes === null) return "—";
  const neg = minutes < 0;
  const abs = Math.abs(minutes);
  const h = Math.floor(abs / 60).toString().padStart(2, "0");
  const m = (abs % 60).toString().padStart(2, "0");
  return `${neg ? "-" : ""}${h}:${m}`;
}

/** capturedAt: ISO date string (yyyy-mm-dd or full ISO). Used to exclude future weekdays from holiday detection. */
export function aggregateMonth(registros: RegistroDia[], capturedAt?: string): MonthAggregate {
  const empty = { daysWithMarcacoes: 0, somaCreditoMin: 0, somaHrMin: 0, somaDebitoMin: 0, somaHhMin: 0, cargaEsperadaMin: 0, dncFinalMin: null, balanceMin: null };
  if (registros.length === 0) return empty;

  let daysWithMarcacoes = 0;
  let somaCreditoMin = 0;
  let somaHrMin = 0;
  let somaDebitoMin = 0;
  let somaHhMin = 0;

  for (const r of registros) {
    if (r.marcacoes && r.marcacoes.length > 0) daysWithMarcacoes++;
    somaCreditoMin += parseHHMM(r.credito) ?? 0;
    somaHrMin += parseHHMM(r.hr) ?? 0;
    somaDebitoMin += effectiveDebitoMin(r);
    const h = parseHHMM(r.hh);
    if (h !== null) somaHhMin += h;
  }

  // Carga esperada: all weekdays in month minus past holidays (credito=00:00, no punches, day ≤ capturedAt)
  const capturedDate = capturedAt ? capturedAt.slice(0, 10) : "9999-12-31";
  let weekdays = 0;
  let pastHolidays = 0;
  for (const r of registros) {
    if (!r.data) continue;
    const dow = new Date(r.data + "T12:00:00Z").getUTCDay();
    if (dow === 0 || dow === 6) continue; // skip weekends
    weekdays++;
    if (r.data <= capturedDate && r.marcacoes.length === 0 && r.credito === "00:00") pastHolidays++;
  }
  const cargaEsperadaMin = (weekdays - pastHolidays) * JORNADA_MIN;

  const lastRecord = registros[registros.length - 1];
  const dncFinalMin = parseHHMM(lastRecord.dnc);

  let balanceMin: number | null = null;
  for (let i = registros.length - 1; i >= 0; i--) {
    const v = parseSignedHHMM(registros[i].credito_acumulado);
    if (v !== null) { balanceMin = v; break; }
  }

  return { daysWithMarcacoes, somaCreditoMin, somaHrMin, somaDebitoMin, somaHhMin, cargaEsperadaMin, dncFinalMin, balanceMin };
}
