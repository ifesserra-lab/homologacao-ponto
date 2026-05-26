import type { RegistroDia, ResumoHorasApuradas, EspelhoMesResume } from "@/types/dashboard";

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
export function aggregateMonth(registros: RegistroDia[], resumo?: ResumoHorasApuradas | null, capturedAt?: string): MonthAggregate {
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

  const lastRecord = registros[registros.length - 1];
  const dncFinalMin = parseHHMM(lastRecord.dnc);

  if (resumo) {
    const somaCreditoMinR = parseSignedHHMM(resumo.total_horas_homologadas);
    const somaHrMinR = parseSignedHHMM(resumo.total_horas_registradas);
    const cargaEsperadaMinR = parseSignedHHMM(resumo.carga_horaria_esperada_mes);
    const balanceMinR = parseSignedHHMM(resumo.saldo_horas_mes);
    return {
      daysWithMarcacoes,
      somaCreditoMin: somaCreditoMinR ?? somaCreditoMin,
      somaHrMin: somaHrMinR ?? somaHrMin,
      somaDebitoMin,
      somaHhMin,
      cargaEsperadaMin: cargaEsperadaMinR ?? (weekdays - pastHolidays) * JORNADA_MIN,
      dncFinalMin,
      balanceMin: balanceMinR !== undefined ? balanceMinR : null,
    };
  }

  const cargaEsperadaMin = (weekdays - pastHolidays) * JORNADA_MIN;

  let balanceMin: number | null = null;
  for (let i = registros.length - 1; i >= 0; i--) {
    const v = parseSignedHHMM(registros[i].credito_acumulado);
    if (v !== null) { balanceMin = v; break; }
  }

  return { daysWithMarcacoes, somaCreditoMin, somaHrMin, somaDebitoMin, somaHhMin, cargaEsperadaMin, dncFinalMin, balanceMin };
}

/** Counts absent workdays (weekday, no punches, no credit/debit = holiday-like excluded). */
export function countAbsentWorkdays(registros: RegistroDia[]): number {
  return registros.filter(isAbsentWorkDay).length;
}

/** Groups occurrences by normalized type (strips date in parentheses). */
export function countOcorrencias(registros: RegistroDia[]): { type: string; count: number }[] {
  const counts: Record<string, number> = {};
  for (const r of registros) {
    for (const occ of r.ocorrencias ?? []) {
      const type = occ.replace(/\s*\([^)]*\)/g, "").trim();
      counts[type] = (counts[type] ?? 0) + 1;
    }
  }
  return Object.entries(counts)
    .map(([type, count]) => ({ type, count }))
    .sort((a, b) => b.count - a.count);
}

/** % of carga completed (0–100, capped at 100). Returns null if cargaEsperadaMin = 0. */
export function pctCarga(somaCreditoMin: number, cargaEsperadaMin: number): number | null {
  if (!cargaEsperadaMin) return null;
  return Math.min(100, Math.round((somaCreditoMin / cargaEsperadaMin) * 100));
}

/** Collect all unique sorted periodo labels across servers. */
export function allPeriodos(servers: EspelhoMesResume[][]): string[] {
  const set = new Set<string>();
  for (const meses of servers) for (const m of meses) if (m.periodoReferencia) set.add(m.periodoReferencia);
  return Array.from(set).sort((a, b) => {
    const [ma, ya] = a.split("/"); const [mb, yb] = b.split("/");
    const MONTHS: Record<string,number> = { Janeiro:1,Fevereiro:2,"Março":3,Abril:4,Maio:5,Junho:6,Julho:7,Agosto:8,Setembro:9,Outubro:10,Novembro:11,Dezembro:12 };
    return (+ya * 100 + (MONTHS[ma] ?? 0)) - (+yb * 100 + (MONTHS[mb] ?? 0));
  });
}

export type OcorrenciaCategoria = "pit" | "abono" | "afastamento" | "recesso" | "sistema";

export interface OcorrenciaDias {
  pit: number;
  abono: number;
  afastamento: number;
  recesso: number;
  sistema: number;
}

export function classifyOcorrencia(ocorrs: string[]): OcorrenciaCategoria | null {
  if (!ocorrs.length) return null;
  const joined = ocorrs.join(" ").toUpperCase();
  if (joined.includes("PIT") || joined.includes("PLANO DE TRABALHO - DOCENTE") || joined.includes("DIA SEM ATIVIDADES LETIVAS")) return "pit";
  if (joined.includes("ABONO DE HORAS") || joined.includes("HORÁRIO ESPECIAL") || joined.includes("ATIVIDADE EXTERNA")) return "abono";
  if (joined.includes("LICENÇA PARA TRATAMENTO") || joined.includes("LIC. PATERNIDADE") || joined.includes("LICENÇA PATERNIDADE") || joined.includes("PRORROGAÇÃO LICENÇA") || joined.includes("AFAS. ESTUDO") || joined.includes("FALTA JUSTIFICADA")) return "afastamento";
  if (joined.includes("RECESSO") || joined.includes("COMPENSAÇÃO DE RECESSO") || joined.includes("QUARTA-FEIRA DE CINZAS") || joined.includes("CINZAS")) return "recesso";
  if (joined.includes("INDISPONIBILIDADE DO SISTEMA")) return "sistema";
  return null;
}

export function countOcorrenciaCategorias(registros: RegistroDia[]): OcorrenciaDias {
  const counts: OcorrenciaDias = { pit: 0, abono: 0, afastamento: 0, recesso: 0, sistema: 0 };
  for (const r of registros) {
    const cat = classifyOcorrencia(r.ocorrencias ?? []);
    if (cat) counts[cat]++;
  }
  return counts;
}

export function cleanOcorrenciaTexto(text: string): string {
  return text
    .replace(/\s*\(\d{2}\/\d{2}\/\d{4}(?:\s+a\s+\d{2}\/\d{2}\/\d{4})?\)/g, "")
    .replace(/\s*Duração:.*/, "")
    .replace(/\s*Período de Compensação:.*/, "")
    .trim();
}
