#!/usr/bin/env node
import { readFileSync, existsSync } from "fs";
import { resolve } from "path";
import { parseArgs } from "util";

// Load .env from crawler dir
const envPath = new URL("../.env", import.meta.url).pathname;
if (existsSync(envPath)) {
  for (const line of readFileSync(envPath, "utf-8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
    const [k, ...rest] = trimmed.split("=");
    process.env[k.trim()] ??= rest.join("=").trim();
  }
}

const { values: opts, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    file: { type: "string", short: "f" },
    "output-dir": { type: "string", default: "../data/runs" },
    "env-file": { type: "string" },
    headed: { type: "boolean", default: false },
    servidor: { type: "string" },
    siape: { type: "string" },
    mes: { type: "string" },
    ano: { type: "string" },
  },
});

const command = positionals[0] ?? "batch";
const outputDir = resolve(opts["output-dir"]);

const username = process.env.SIGRH_USERNAME;
const password = process.env.SIGRH_PASSWORD;
if (!username || !password) {
  console.error("Erro: SIGRH_USERNAME e SIGRH_PASSWORD são obrigatórios (.env ou variáveis de ambiente)");
  process.exit(1);
}

const { SigrhBrowser } = await import("./sigrh.js");
const browser = new SigrhBrowser({ headed: opts.headed });

try {
  await browser.start();
  console.log("Login no SIGRH…");
  await browser.login(username, password);
  console.log("Login OK");

  if (command === "batch") {
    if (!opts.file) { console.error("--file obrigatório para batch"); process.exit(1); }
    const { default: yaml } = await import("js-yaml");
    const { runBatch } = await import("./batch.js");
    const config = yaml.load(readFileSync(resolve(opts.file), "utf-8"));
    const entries = await runBatch({
      browser,
      config,
      outputDir,
      onProgress: (msg) => console.log(msg),
    });
    const ok = entries.filter(e => e.status !== "failed").length;
    const fail = entries.filter(e => e.status === "failed").length;
    console.log(`\nConcluído: ${ok} ok, ${fail} falhas`);
    process.exit(fail > 0 ? 1 : 0);
  }

  if (command === "espelho") {
    if (!opts.servidor) { console.error("--servidor obrigatório"); process.exit(1); }
    const { randomUUID } = await import("crypto");
    const { parseEspelho } = await import("./parser.js");
    const { writeEspelho } = await import("./writer.js");
    const mes = opts.mes ? parseInt(opts.mes) : new Date().getMonth() + 1;
    const ano = opts.ano ? parseInt(opts.ano) : new Date().getFullYear();
    await browser.navigateToEspelho();
    await browser.searchServer(opts.servidor, mes, ano, opts.siape ?? null);
    const rows = await browser.findServerRows();
    const match = rows.find(r => r.hasSelect);
    if (!match) { console.error("Servidor não encontrado"); process.exit(1); }
    await browser.selectServer(match);
    const html = await browser.getHtml();
    const url = await browser.getUrl();
    const runId = randomUUID().replace(/-/g, "");
    const espelho = parseEspelho({ html, url, capturedAt: new Date().toISOString(), runId, serverName: opts.servidor, identifier: opts.siape ?? null });
    const path = writeEspelho(espelho, outputDir);
    console.log(`Salvo: ${path}`);
    process.exit(0);
  }

  console.error(`Comando desconhecido: ${command}`);
  process.exit(1);
} finally {
  await browser.close();
}
