import { randomUUID } from "crypto";
import { parseEspelho } from "./parser.js";
import { writeEspelho } from "./writer.js";

const MONTH_NAMES = [
  "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

function expandPeriodos(config) {
  const periodos = [];
  const anos = Array.isArray(config.anos) ? config.anos : [];
  if (anos.length > 0) {
    for (const ano of anos) {
      for (let mes = 1; mes <= 12; mes++) {
        periodos.push({ mes, ano });
      }
    }
  } else {
    const now = new Date();
    periodos.push({ mes: now.getMonth() + 1, ano: now.getFullYear() });
  }
  return periodos;
}

export async function runBatch({ browser, config, outputDir, onProgress = null }) {
  const entries = [];
  const periodos = expandPeriodos(config);
  const total = config.servidores.length * periodos.length;
  let done = 0;

  onProgress?.(`[batch:start] total=${total}`);

  for (const servidor of config.servidores) {
    for (const { mes, ano } of periodos) {
      const runId = randomUUID().replace(/-/g, "");
      const capturedAt = new Date().toISOString();
      try {
        onProgress?.(`→ ${servidor.nome} ${MONTH_NAMES[mes]}/${ano}`);

        await browser.navigateToEspelho();
        await browser.searchServer(servidor.nome, mes, ano, servidor.siape ?? null);

        const rows = await browser.findServerRows();
        const match = rows.find(r => r.hasSelect);
        if (!match) {
          done++;
          onProgress?.(`[batch:progress] ${done}/${total}`);
          entries.push({ nome: servidor.nome, siape: servidor.siape, mes, ano, status: "failed", error: "Servidor não encontrado nos resultados" });
          continue;
        }
        await browser.selectServer(match);

        const html = await browser.getHtml();
        const url = await browser.getUrl();
        const espelho = parseEspelho({ html, url, capturedAt, runId, serverName: servidor.nome, identifier: servidor.siape ?? null });
        const path = writeEspelho(espelho, outputDir);
        done++;
        onProgress?.(`  ✓ ${path}`);
        onProgress?.(`[batch:progress] ${done}/${total}`);
        entries.push({ nome: servidor.nome, siape: servidor.siape, mes, ano, status: espelho.status, path });
      } catch (err) {
        done++;
        onProgress?.(`  ✗ ${err.message}`);
        onProgress?.(`[batch:progress] ${done}/${total}`);
        entries.push({ nome: servidor.nome, siape: servidor.siape, mes, ano, status: "failed", error: err.message });
      }
    }
  }

  return entries;
}
