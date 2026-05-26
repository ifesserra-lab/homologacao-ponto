import { readTextFile, readDir, exists } from "@tauri-apps/plugin-fs";
import { join } from "@tauri-apps/api/path";
import type { EspelhoMesResume, ServidorResume, RawEspelho, AfastamentoPeriodo } from "@/types/dashboard";
import { aggregateMonth, countOcorrenciaCategorias, classifyOcorrencia, cleanOcorrenciaTexto, parseSignedHHMM } from "@/lib/aggregation";
import type { RegistroDia } from "@/types/dashboard";

function periodoToSlug(periodo: string): string {
  const nfkd = periodo.normalize("NFD");
  const ascii = nfkd.replace(/[̀-ͯ]/g, "");
  return ascii.toLowerCase().replace(/\//g, "-").replace(/[^a-z0-9-]+/g, "-").replace(/^-|-$/g, "");
}

const MONTH_ORDER: Record<string, number> = {
  janeiro: 1, fevereiro: 2, março: 3, abril: 4, maio: 5, junho: 6,
  julho: 7, agosto: 8, setembro: 9, outubro: 10, novembro: 11, dezembro: 12,
};

function periodoSortKey(periodo: string | null): number {
  if (!periodo) return 0;
  const [mes, ano] = periodo.toLowerCase().split("/");
  return (parseInt(ano, 10) || 0) * 100 + (MONTH_ORDER[mes.trim()] ?? 0);
}

async function loadEspelho(filePath: string): Promise<RawEspelho | null> {
  try {
    const text = await readTextFile(filePath);
    const raw = JSON.parse(text) as RawEspelho;
    if (!raw.captured_at) return null;
    return raw;
  } catch {
    console.warn(`[repository] Skipping invalid JSON: ${filePath}`);
    return null;
  }
}

function deduplicate(raws: RawEspelho[]): RawEspelho[] {
  const byPeriod = new Map<string, RawEspelho>();
  for (const raw of raws) {
    const key = raw.periodo_referencia ?? raw.run_id;
    const existing = byPeriod.get(key);
    if (!existing || raw.captured_at > existing.captured_at) {
      byPeriod.set(key, raw);
    }
  }
  return Array.from(byPeriod.values());
}

function toMesResume(raw: RawEspelho): EspelhoMesResume {
  const agg = raw.status === "completed"
    ? aggregateMonth(raw.registros, raw.resumo ?? null, raw.captured_at)
    : { daysWithMarcacoes: 0, somaCreditoMin: 0, somaHrMin: 0, somaDebitoMin: 0, somaHhMin: 0, cargaEsperadaMin: 0, dncFinalMin: null, balanceMin: null };

  const ocorrenciaDias = raw.status === "completed"
    ? countOcorrenciaCategorias(raw.registros)
    : { pit: 0, abono: 0, afastamento: 0, recesso: 0, sistema: 0 };

  const pitJustificadoPct: number | null = (() => {
    if (!raw.resumo) return null;
    const justMin = parseSignedHHMM(raw.resumo.total_horas_justificadas);
    const homMin = parseSignedHHMM(raw.resumo.total_horas_homologadas);
    if (justMin === null || homMin === null || homMin === 0) return null;
    return Math.round((justMin / homMin) * 100);
  })();

  const periodo = raw.periodo_referencia ?? null;
  return {
    periodoReferencia: periodo,
    periodoSlug: periodo ? periodoToSlug(periodo) : raw.run_id,
    status: raw.status,
    capturedAt: raw.captured_at,
    ...agg,
    ocorrenciaDias,
    pitJustificadoPct,
  };
}

function periodoRange(meses: EspelhoMesResume[]): string {
  const periods = meses.map((m) => m.periodoReferencia).filter((p): p is string => p !== null);
  if (periods.length === 0) return "—";
  if (periods.length === 1) return periods[0];
  return `${periods[0]} – ${periods[periods.length - 1]}`;
}

async function loadServerSlug(slug: string, dataDir: string): Promise<ServidorResume> {
  const serverDir = await join(dataDir, slug);
  const entries = await readDir(serverDir);
  const jsonFiles = entries.filter((e) => !e.isDirectory && e.name.endsWith(".json"));
  const raws: RawEspelho[] = [];
  for (const f of jsonFiles) {
    const fp = await join(serverDir, f.name);
    const raw = await loadEspelho(fp);
    if (raw) raws.push(raw);
  }
  const deduped = deduplicate(raws);
  deduped.sort((a, b) => periodoSortKey(a.periodo_referencia) - periodoSortKey(b.periodo_referencia));
  const meses = deduped.map(toMesResume);
  const nome = deduped[0]?.servidor?.nome ?? slug.toUpperCase();
  const siape = deduped[0]?.servidor?.identificador ?? null;
  return {
    slug,
    nome,
    siape,
    meses,
    totalMeses: meses.length,
    periodoRange: periodoRange(meses),
    statusIndicator: meses.some((m) => m.status === "empty") ? "com-vazios" : "completo",
  };
}

export async function listServers(dataDir: string): Promise<ServidorResume[]> {
  if (!(await exists(dataDir))) return [];
  const entries = await readDir(dataDir);
  const dirs = entries.filter((e) => e.isDirectory);
  return Promise.all(dirs.map((e) => loadServerSlug(e.name, dataDir)));
}

export async function serverDetail(slug: string, dataDir: string): Promise<ServidorResume | undefined> {
  const serverDir = await join(dataDir, slug);
  if (!(await exists(serverDir))) return undefined;
  return loadServerSlug(slug, dataDir);
}

export async function monthDetail(slug: string, periodoSlug: string, dataDir: string): Promise<RawEspelho | undefined> {
  const serverDir = await join(dataDir, slug);
  if (!(await exists(serverDir))) return undefined;
  const entries = await readDir(serverDir);
  const jsonFiles = entries.filter((e) => !e.isDirectory && e.name.endsWith(".json"));
  const raws: RawEspelho[] = [];
  for (const f of jsonFiles) {
    const fp = await join(serverDir, f.name);
    const raw = await loadEspelho(fp);
    if (raw) raws.push(raw);
  }
  const deduped = deduplicate(raws);
  return deduped.find((r) => {
    const s = r.periodo_referencia ? periodoToSlug(r.periodo_referencia) : r.run_id;
    return s === periodoSlug;
  });
}

function extractAfastamentoPeriods(slug: string, nome: string, registros: RegistroDia[], _periodoRef: string | null): AfastamentoPeriodo[] {
  const seen = new Set<string>();
  const periods: AfastamentoPeriodo[] = [];
  for (const r of registros) {
    const ocorrs = r.ocorrencias ?? [];
    if (!ocorrs.length) continue;
    const cat = classifyOcorrencia(ocorrs);
    if (!cat || cat === "pit" || cat === "abono") continue;
    const raw = ocorrs[0];
    const key = `${slug}::${raw}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const rangeMatch = raw.match(/\((\d{2})\/(\d{2})\/(\d{4})\s+a\s+(\d{2})\/(\d{2})\/(\d{4})\)/);
    let dataInicio: string, dataFim: string, dias: number;
    if (rangeMatch) {
      dataInicio = `${rangeMatch[3]}-${rangeMatch[2]}-${rangeMatch[1]}`;
      dataFim = `${rangeMatch[6]}-${rangeMatch[5]}-${rangeMatch[4]}`;
      const d1 = new Date(dataInicio + "T12:00:00Z");
      const d2 = new Date(dataFim + "T12:00:00Z");
      dias = Math.round((d2.getTime() - d1.getTime()) / 86400000) + 1;
    } else {
      dataInicio = r.data;
      dataFim = r.data;
      dias = 1;
    }
    const texto = cleanOcorrenciaTexto(raw);
    periods.push({ serverSlug: slug, serverNome: nome, categoria: cat as "afastamento" | "recesso" | "sistema", texto, dataInicio, dataFim, dias });
  }
  return periods;
}

export async function loadAllAfastamentos(dataDir: string): Promise<AfastamentoPeriodo[]> {
  if (!(await exists(dataDir))) return [];
  const entries = await readDir(dataDir);
  const dirs = entries.filter((e) => e.isDirectory);
  const all: AfastamentoPeriodo[] = [];
  for (const dir of dirs) {
    const serverDir = await join(dataDir, dir.name);
    const files = await readDir(serverDir);
    const jsonFiles = files.filter((e) => !e.isDirectory && e.name.endsWith(".json"));
    for (const f of jsonFiles) {
      const fp = await join(serverDir, f.name);
      const raw = await loadEspelho(fp);
      if (!raw || raw.status !== "completed") continue;
      const nome = raw.servidor?.nome ?? dir.name.toUpperCase();
      all.push(...extractAfastamentoPeriods(dir.name, nome, raw.registros, raw.periodo_referencia));
    }
  }
  return all.sort((a, b) => a.dataInicio.localeCompare(b.dataInicio));
}
