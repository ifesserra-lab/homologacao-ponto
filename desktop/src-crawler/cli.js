#!/usr/bin/env node
import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { parseArgs } from "util";
import yaml from "js-yaml";
import { SigrhBrowser } from "./sigrh.js";
import { runBatch, runEntries, MONTH_NAMES } from "./batch.js";
import { parseEspelho } from "./parser.js";
import { writeEspelho } from "./writer.js";
import { scanStaleMonths } from "./stale.js";
import { scanLiberados, homologarServidor } from "./homologar.js";
import { descobrirServidores, mergeServidoresYaml } from "./descobrir.js";
import { randomUUID } from "crypto";

// CJS bundle (esbuild): __dirname injected automatically.
// pkg binary: __dirname may be undefined in the entry module; use execPath fallback.
// ESM dev mode: __dirname undefined, use import.meta.url fallback.
// The ternary short-circuits so import.meta is never evaluated in CJS.
const _dir = (typeof __dirname !== "undefined" && __dirname)
  ? __dirname
  : (typeof process !== "undefined" && process.pkg)
    ? dirname(process.execPath)
    : dirname(new URL(import.meta.url).pathname);

function loadEnv(explicitPath) {
  const candidates = [];
  if (explicitPath) candidates.push(explicitPath);
  if (process.pkg) {
    const execDir = resolve(process.execPath, "..");
    candidates.push(resolve(execDir, ".env"));
    candidates.push(resolve(execDir, "../.env"));
  }
  candidates.push(resolve(_dir, "../.env"));
  for (const p of candidates) {
    if (!p || !existsSync(p)) continue;
    for (const line of readFileSync(p, "utf-8").split("\n")) {
      const t = line.trim();
      if (!t || t.startsWith("#") || !t.includes("=")) continue;
      const eq = t.indexOf("=");
      process.env[t.slice(0, eq).trim()] ??= t.slice(eq + 1).trim();
    }
    break;
  }
}

async function main() {
  const { values: opts, positionals } = parseArgs({
    allowPositionals: true,
    options: {
      file:         { type: "string", short: "f" },
      "output-dir": { type: "string" },
      "env-file":   { type: "string" },
      headed:       { type: "boolean", default: false },
      servidor:     { type: "string" },
      siape:        { type: "string" },
      mes:          { type: "string" },
      ano:          { type: "string" },
      slug:         { type: "string" },
      "dry-run":    { type: "boolean", default: false },
      "he-policy":  { type: "string", default: "manual" },
    },
  });

  loadEnv(opts["env-file"]);

  const command   = positionals[0] ?? "batch";
  const outputDir = resolve(opts["output-dir"] ?? resolve(_dir, "../data/runs"));
  const username  = process.env.SIGRH_USERNAME;
  const password  = process.env.SIGRH_PASSWORD;

  if (!username || !password) {
    console.error("Erro: SIGRH_USERNAME e SIGRH_PASSWORD são obrigatórios (.env ou variáveis de ambiente)");
    process.exit(1);
  }

  const browser = new SigrhBrowser({ headed: opts.headed });

  try {
    await browser.start();
    console.log("Login no SIGRH…");
    await browser.login(username, password);
    console.log("Login OK");

    if (command === "batch") {
      if (!opts.file) { console.error("--file obrigatório para batch"); process.exit(1); }
      const config  = yaml.load(readFileSync(resolve(opts.file), "utf-8"));
      const entries = await runBatch({ browser, config, outputDir, onProgress: (msg) => console.log(msg) });
      const ok   = entries.filter(e => e.status !== "failed").length;
      const fail = entries.filter(e => e.status === "failed").length;
      console.log(`\nConcluído: ${ok} ok, ${fail} falhas`);
      process.exit(fail > 0 ? 1 : 0);
    }

    if (command === "refresh") {
      if (!opts.file) { console.error("--file obrigatório para refresh"); process.exit(1); }
      const config = yaml.load(readFileSync(resolve(opts.file), "utf-8"));

      const stale = scanStaleMonths(outputDir, config);

      if (stale.length === 0) {
        console.log("Nenhum mês desatualizado. Tudo em dia.");
        process.exit(0);
      }

      console.log(`\n[refresh] ${stale.length} mês(es) para atualizar:\n`);
      for (const s of stale) {
        console.log(`  ${s.nome} ${MONTH_NAMES[s.mes]}/${s.ano}  [${s.reasons.join(", ")}]`);
      }
      console.log();

      const results = await runEntries({ browser, entries: stale, outputDir, onProgress: (msg) => console.log(msg) });
      const ok   = results.filter(e => e.status !== "failed").length;
      const fail = results.filter(e => e.status === "failed").length;
      console.log(`\nConcluído: ${ok} ok, ${fail} falhas`);
      process.exit(fail > 0 ? 1 : 0);
    }

    if (command === "espelho") {
      if (!opts.servidor) { console.error("--servidor obrigatório"); process.exit(1); }
      const mes = opts.mes ? parseInt(opts.mes) : new Date().getMonth() + 1;
      const ano = opts.ano ? parseInt(opts.ano) : new Date().getFullYear();
      await browser.navigateToEspelho();
      await browser.searchServer(opts.servidor, mes, ano, opts.siape ?? null);
      const rows  = await browser.findServerRows();
      const match = rows.find(r => r.hasSelect);
      if (!match) { console.error("Servidor não encontrado"); process.exit(1); }
      await browser.selectServer(match);
      const html   = await browser.getHtml();
      const url    = await browser.getUrl();
      const runId  = randomUUID().replace(/-/g, "");
      const espelho = parseEspelho({ html, url, capturedAt: new Date().toISOString(), runId, serverName: opts.servidor, identifier: opts.siape ?? null });
      const path    = writeEspelho(espelho, outputDir);
      console.log(`Salvo: ${path}`);
      process.exit(0);
    }

    if (command === "homologar") {
      const politicaHe = opts["he-policy"] ?? process.env.POLITICA_HE ?? "manual";
      const slugFilter = opts.slug ? opts.slug.split(",").map(s => s.trim()).filter(Boolean) : null;

      let liberados = scanLiberados(outputDir, politicaHe, slugFilter);

      if (opts.mes || opts.ano) {
        const mesFilter = opts.mes ? parseInt(opts.mes) : null;
        const anoFilter = opts.ano ? parseInt(opts.ano) : null;
        liberados = liberados.filter(e =>
          (!mesFilter || e.mes === mesFilter) &&
          (!anoFilter || e.ano === anoFilter)
        );
      }

      if (liberados.length === 0) {
        console.log("Nenhum espelho liberado para homologar.");
        process.exit(0);
      }

      console.log(`\n[homologar] ${liberados.length} espelho(s) liberado(s) | politica_he=${politicaHe}:\n`);
      for (const e of liberados) {
        console.log(`  ${e.nome}  ${e.periodoReferencia}`);
      }
      console.log();

      if (opts["dry-run"]) {
        console.log("[dry-run] Nenhuma ação executada.");
        process.exit(0);
      }

      let ok = 0, fail = 0;
      for (const entry of liberados) {
        try {
          console.log(`→ ${entry.nome}  ${entry.periodoReferencia}`);
          await homologarServidor(browser, entry);
          console.log(`  ✓ Homologado`);
          ok++;
        } catch (e) {
          console.log(`  ✗ Erro: ${e.message}`);
          fail++;
        }
      }

      console.log(`\nConcluído: ${ok} ok, ${fail} falhas`);
      process.exit(fail > 0 ? 1 : 0);
    }

    if (command === "descobrir") {
      const setor = process.env.CHEFIA_SETOR ?? "";
      if (!setor) { console.error("CHEFIA_SETOR não definido (configuration.yaml → chefia.setor)"); process.exit(1); }

      console.log(`\n[descobrir] Buscando servidores da unidade:\n  ${setor}\n`);

      const encontrados = await descobrirServidores(browser, setor);

      if (encontrados.length === 0) {
        console.log("Nenhum servidor encontrado na tela de homologação.");
        process.exit(0);
      }

      console.log(`\n${encontrados.length} servidor(es) encontrado(s):`);
      for (const s of encontrados) console.log(`  ${s.siape || "???????"}  ${s.nome}`);

      if (opts["dry-run"]) {
        console.log("\n[dry-run] servidores.yaml não alterado.");
        process.exit(0);
      }

      const yamlPath = resolve(opts.file ?? resolve(_dir, "../../servidores.yaml"));
      const { data, adicionados, atualizados } = mergeServidoresYaml(yamlPath, encontrados);
      writeFileSync(yamlPath, yaml.dump(data, { indent: 2, lineWidth: -1 }), "utf-8");
      console.log(`\n✓ servidores.yaml atualizado — ${adicionados} adicionado(s), ${atualizados} atualizado(s)`);
      process.exit(0);
    }

    console.error(`Comando desconhecido: ${command}`);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

main().catch(e => { console.error(e); process.exit(1); });
