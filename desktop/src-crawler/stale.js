import { readdirSync, readFileSync, existsSync } from "fs";
import { join } from "path";

const STALE_DAYS = 30;
const RECENT_MONTHS = 2; // only recheck "empty" files within last N months

const MONTH_NAMES = [
  "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

function slug(name) {
  return name
    .normalize("NFD").replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function isBeforeOrCurrentMonth(mes, ano) {
  const now = new Date();
  if (ano < now.getFullYear()) return true;
  if (ano > now.getFullYear()) return false;
  return mes <= now.getMonth() + 1;
}

function isCurrentMonth(mes, ano) {
  const now = new Date();
  return mes === now.getMonth() + 1 && ano === now.getFullYear();
}

function isWithinRecentMonths(mes, ano) {
  const now = new Date();
  const threshold = new Date(now.getFullYear(), now.getMonth() - RECENT_MONTHS, 1);
  const fileDate = new Date(ano, mes - 1, 1);
  return fileDate >= threshold;
}

function checkStale(espelho, mes, ano) {
  const reasons = [];

  // Current month always needs refresh (records still being added)
  if (isCurrentMonth(mes, ano)) {
    reasons.push("mes_atual");
    return reasons;
  }

  // Empty: only re-check recent months (old empties are legitimately empty)
  if (espelho.status === "empty") {
    if (isWithinRecentMonths(mes, ano)) {
      reasons.push("vazio");
    }
    return reasons;
  }

  // Days not yet approved by manager
  if (Array.isArray(espelho.registros)) {
    if (espelho.registros.some(r => r.situacao === "Pendente")) {
      reasons.push("dias_pendentes");
    }
  }

  // Unauthorized debit
  const resumo = espelho.resumo;
  if (resumo) {
    const debito = resumo.debito_mes_atual_nao_autorizado;
    if (debito && debito !== "00:00" && debito !== "-00:00") {
      reasons.push("debito_nao_autorizado");
    }
  }

  // Old capture with negative balance (might have been corrected)
  if (espelho.captured_at && resumo) {
    const saldo = resumo.saldo_horas_mes;
    if (saldo && saldo.startsWith("-") && saldo !== "-00:00") {
      const ageDays = (Date.now() - new Date(espelho.captured_at).getTime()) / 86400000;
      if (ageDays > STALE_DAYS) {
        reasons.push("saldo_negativo_antigo");
      }
    }
  }

  return reasons;
}

/**
 * Scans outputDir against config and returns stale months to re-download.
 * @param {string} outputDir  - root output dir (contains servidores/ subdir)
 * @param {{ anos: number[], servidores: Array<{nome: string, siape?: string}> }} config
 * @returns {Array<{nome, siape, mes, ano, reasons, filePath}>}
 */
export function scanStaleMonths(outputDir, config) {
  const stale = [];
  const anos = Array.isArray(config.anos) && config.anos.length > 0
    ? config.anos
    : [new Date().getFullYear()];

  for (const servidor of config.servidores) {
    const serverSlug = slug(servidor.nome);
    const serverDir = join(outputDir, "servidores", serverSlug);

    for (const ano of anos) {
      for (let mes = 1; mes <= 12; mes++) {
        if (!isBeforeOrCurrentMonth(mes, ano)) continue;

        const mesName = MONTH_NAMES[mes];
        const filePath = join(serverDir, `espelho-${mesName}-${ano}.json`);

        if (!existsSync(filePath)) {
          stale.push({
            nome: servidor.nome,
            siape: servidor.siape ?? null,
            mes, ano,
            reasons: ["arquivo_ausente"],
            filePath: null,
          });
          continue;
        }

        let espelho;
        try {
          espelho = JSON.parse(readFileSync(filePath, "utf-8"));
        } catch {
          stale.push({
            nome: servidor.nome,
            siape: servidor.siape ?? null,
            mes, ano,
            reasons: ["leitura_falhou"],
            filePath,
          });
          continue;
        }

        const reasons = checkStale(espelho, mes, ano);
        if (reasons.length > 0) {
          stale.push({
            nome: servidor.nome,
            siape: servidor.siape ?? null,
            mes, ano,
            reasons,
            filePath,
          });
        }
      }
    }
  }

  return stale;
}
