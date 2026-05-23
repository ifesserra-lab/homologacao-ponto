import { readFileSync, readdirSync, existsSync, statSync } from "fs";
import { join, resolve } from "path";
import type { EspelhoMesResume, ServidorResume, RawEspelho } from "../types/dashboard";
import { aggregateMonth } from "./aggregation";

const DEFAULT_DATA_DIR = resolve(process.cwd(), "..", "data", "runs", "servidores");

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

function loadEspelho(filePath: string): RawEspelho | null {
  try {
    const raw = JSON.parse(readFileSync(filePath, "utf-8")) as RawEspelho;
    if (!raw.captured_at) return null;
    return raw;
  } catch {
    console.warn(`[dashboard] Skipping invalid JSON: ${filePath}`);
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
  const agg = raw.status === "completed" ? aggregateMonth(raw.registros) : {
    daysWithMarcacoes: 0,
    somaCreditoMin: 0,
    somaDebitoMin: 0,
    somaHhMin: 0,
    dncFinalMin: null,
  };
  const periodo = raw.periodo_referencia ?? null;
  return {
    periodoReferencia: periodo,
    periodoSlug: periodo ? periodoToSlug(periodo) : raw.run_id,
    status: raw.status,
    capturedAt: raw.captured_at,
    ...agg,
  };
}

function periodoRange(meses: EspelhoMesResume[]): string {
  const periods = meses.map((m) => m.periodoReferencia).filter((p): p is string => p !== null);
  if (periods.length === 0) return "—";
  if (periods.length === 1) return periods[0];
  return `${periods[0]} – ${periods[periods.length - 1]}`;
}

function buildServidor(slug: string, meses: EspelhoMesResume[], nome: string, siape: string | null): ServidorResume {
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

function loadServerSlug(slug: string, dataDir: string): ServidorResume {
  const serverDir = join(dataDir, slug);
  const files = readdirSync(serverDir).filter((f) => f.endsWith(".json"));
  const raws = files.map((f) => loadEspelho(join(serverDir, f))).filter((r): r is RawEspelho => r !== null);
  const deduped = deduplicate(raws);
  deduped.sort((a, b) => periodoSortKey(a.periodo_referencia) - periodoSortKey(b.periodo_referencia));
  const meses = deduped.map(toMesResume);
  const nome = deduped[0]?.servidor?.nome ?? slug.toUpperCase();
  const siape = deduped[0]?.servidor?.identificador ?? null;
  return buildServidor(slug, meses, nome, siape);
}

export function listServers(dataDir: string = DEFAULT_DATA_DIR): ServidorResume[] {
  if (!existsSync(dataDir)) return [];
  const entries = readdirSync(dataDir).filter((e) => {
    try {
      return statSync(join(dataDir, e)).isDirectory();
    } catch {
      return false;
    }
  });
  return entries.map((slug) => loadServerSlug(slug, dataDir));
}

export function serverDetail(slug: string, dataDir: string = DEFAULT_DATA_DIR): ServidorResume | undefined {
  const serverDir = join(dataDir, slug);
  if (!existsSync(serverDir)) return undefined;
  return loadServerSlug(slug, dataDir);
}

export function monthDetail(slug: string, periodoSlug: string, dataDir: string = DEFAULT_DATA_DIR): RawEspelho | undefined {
  const serverDir = join(dataDir, slug);
  if (!existsSync(serverDir)) return undefined;
  const files = readdirSync(serverDir).filter((f) => f.endsWith(".json"));
  const raws = files.map((f) => loadEspelho(join(serverDir, f))).filter((r): r is RawEspelho => r !== null);
  const deduped = deduplicate(raws);
  return deduped.find((r) => {
    const s = r.periodo_referencia ? periodoToSlug(r.periodo_referencia) : r.run_id;
    return s === periodoSlug;
  });
}
