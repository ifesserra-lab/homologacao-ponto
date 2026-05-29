import { readdirSync, readFileSync, existsSync, statSync } from "fs";
import { join } from "path";

// ── helpers (JS port of homologacao.ts) ──────────────────────────────────────

const MONTH_MAP = {
  janeiro: 1, fevereiro: 2, março: 3, abril: 4, maio: 5, junho: 6,
  julho: 7, agosto: 8, setembro: 9, outubro: 10, novembro: 11, dezembro: 12,
};

export const MONTH_NAMES = [
  "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

function periodoToDate(periodo) {
  const [m, y] = periodo.toLowerCase().split("/");
  return new Date(parseInt(y, 10), (MONTH_MAP[m.trim()] ?? 1) - 1, 1);
}

function isCurrentMonth(periodo) {
  if (!periodo) return false;
  const now = new Date();
  const d = periodoToDate(periodo);
  return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
}

function parseHHMM(v) {
  if (!v || typeof v !== "string") return null;
  const m = v.match(/(\d+):(\d{2})/);
  if (!m) return null;
  return parseInt(m[1], 10) * 60 + parseInt(m[2], 10);
}

// JS port of checkHomologavel — respects politicaHe
function checkHomologavelJS(raw, politicaHe = "manual") {
  if (raw.status === "empty") return { status: "vazio", razoes: [] };
  if (isCurrentMonth(raw.periodo_referencia)) return { status: "mes_atual", razoes: [] };

  const razoes = new Set();

  for (const r of raw.registros ?? []) {
    if (r.situacao === "Pendente") razoes.add("dias_pendentes");

    if (
      (r.marcacoes?.length ?? 0) > 0 &&
      r.marcacoes.length % 2 !== 0 &&
      (r.ocorrencias?.length ?? 0) === 0 &&
      r.situacao !== "Homologado"
    ) {
      const dow = r.data ? new Date(r.data + "T12:00:00Z").getUTCDay() : -1;
      if (dow >= 1 && dow <= 5) razoes.add("marcacoes_incompletas");
    }
  }

  const debito = raw.resumo?.debito_mes_atual_nao_autorizado ?? null;
  if (debito && debito !== "00:00" && debito !== "-00:00") razoes.add("debito_nao_autorizado");

  return { status: razoes.size > 0 ? "bloqueado" : "liberado", razoes: Array.from(razoes) };
}

// ── scanLiberados ─────────────────────────────────────────────────────────────

export function scanLiberados(outputDir, politicaHe = "manual", slugFilter = null) {
  const servidoresDir = join(outputDir, "servidores");
  if (!existsSync(servidoresDir)) return [];

  const result = [];

  for (const slugDir of readdirSync(servidoresDir)) {
    if (slugFilter && !slugFilter.includes(slugDir)) continue;
    const slugPath = join(servidoresDir, slugDir);
    try { if (!statSync(slugPath).isDirectory()) continue; } catch { continue; }

    for (const file of readdirSync(slugPath)) {
      if (!file.endsWith(".json")) continue;
      try {
        const raw = JSON.parse(readFileSync(join(slugPath, file), "utf-8"));
        const check = checkHomologavelJS(raw, politicaHe);
        if (check.status !== "liberado") continue;
        const periodo = raw.periodo_referencia;
        if (!periodo) continue;
        const d = periodoToDate(periodo);
        result.push({
          slug: slugDir,
          nome: raw.servidor?.nome ?? slugDir,
          siape: raw.servidor?.siape ?? raw.servidor?.identificador ?? null,
          periodoReferencia: periodo,
          mes: d.getMonth() + 1,
          ano: d.getFullYear(),
          politicaHe,
          heEntries: (raw.registros ?? []).filter(r => {
            const he = parseHHMM(r.he);
            return he !== null && he > 0;
          }),
        });
      } catch { /* skip corrupt files */ }
    }
  }

  return result.sort((a, b) => {
    const byName = a.nome.localeCompare(b.nome, "pt-BR");
    if (byName !== 0) return byName;
    return periodoToDate(a.periodoReferencia).getTime() - periodoToDate(b.periodoReferencia).getTime();
  });
}

// ── Playwright homologação flow ───────────────────────────────────────────────

const PORTAL_URL       = "https://sigrh.ifes.edu.br/sigrh/servidor/portal/servidor.jsf";
const BUSCA_UNIDADE_URL = "https://sigrh.ifes.edu.br/sigrh/dap/busca_unidade.jsf";

async function safeTimeout(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function normStr(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
}

// Navigate via portal menu to "Homologar Ponto Eletrônico" (WF-006 path).
// Strategy 1: JS click leaf. Strategy 2: hover-chain. Strategy 3: direct URL.
// Mirrors descobrir.js navegarMenuChefia but targets the homologation leaf.
async function navegarMenuHomologacaoPonto(page) {
  await page.goto(PORTAL_URL);
  await page.waitForLoadState("networkidle").catch(() => {});
  await safeTimeout(2000);

  const leafTargets = [
    "homologar ponto eletronico", "homologar ponto eletrônico",
    "controle de frequencia", "controle de frequência",
    "ponto eletronico", "ponto eletrônico",
  ];

  // Strategy 1: JS click on leaf anchor (bypasses dropdown visibility)
  const clicked = await page.evaluate((leafTargets) => {
    const norm = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
    for (const a of document.querySelectorAll("ul.dropdown-menu a, .dropdown-menu a, a")) {
      const txt = norm(a.textContent || "").trim();
      if (leafTargets.some(t => txt === t)) { a.click(); return true; }
    }
    return false;
  }, leafTargets).catch(() => false);

  if (clicked) {
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await safeTimeout(1500);
    if (!page.url().includes("servidor.jsf")) return;
  }

  // Strategy 2: hover-chain (Chefia de Unidade → Homologação de Ponto Eletrônico → leaf)
  console.log("  Tentando hover-chain para homologação...");
  const parentChain = [
    ["chefia da unidade", "chefia de unidade"],
    ["homologacao de ponto eletronico", "homologação de ponto eletrônico", "homologacoes", "homologações"],
  ];
  for (const labels of parentChain) {
    const deadline = Date.now() + 4000;
    let found = false;
    while (Date.now() < deadline && !found) {
      const els = page.locator("li.dropdown, li.menu-item, a");
      const n = await els.count().catch(() => 0);
      for (let i = 0; i < n && !found; i++) {
        const el = els.nth(i);
        const txt = normStr(await el.innerText().catch(() => "")).split("\n")[0].trim();
        if (labels.some(l => txt === l || txt.startsWith(l))) {
          await el.hover({ force: true }).catch(() => {});
          await safeTimeout(400);
          found = true;
        }
      }
      if (!found) await safeTimeout(200);
    }
  }
  // Click leaf after hover-chain
  const deadline2 = Date.now() + 4000;
  while (Date.now() < deadline2) {
    const els = page.locator("a");
    const n = await els.count().catch(() => 0);
    for (let i = 0; i < n; i++) {
      const el = els.nth(i);
      const txt = normStr(await el.innerText().catch(() => "")).trim();
      if (leafTargets.some(t => txt === t)) {
        await el.click({ force: true }).catch(() => {});
        await page.waitForLoadState("domcontentloaded").catch(() => {});
        await safeTimeout(1000);
        if (!page.url().includes("servidor.jsf")) return;
        break;
      }
    }
    await safeTimeout(300);
  }

  // Strategy 3: direct URL fallback
  console.log("  Fallback: URL direta busca_unidade.jsf");
  await page.goto(BUSCA_UNIDADE_URL);
  await page.waitForLoadState("networkidle").catch(() => {});
  await safeTimeout(2000);
}

// Navigate via portal menu to "Homologar Frequência" (WF-007 path).
async function navegarMenuHomologacaoFrequencia(page) {
  await page.goto(PORTAL_URL);
  await page.waitForLoadState("networkidle").catch(() => {});
  await safeTimeout(2000);

  // Diagnóstico: dump links contendo "frequen" ou "homolog" para descobrir URL WF-007
  const diagLinks = await page.evaluate(() =>
    Array.from(document.querySelectorAll("a"))
      .filter(a => {
        const t = (a.textContent || "").toLowerCase();
        const h = (a.href || "").toLowerCase();
        return t.includes("frequen") || h.includes("frequen") || t.includes("homolog") || h.includes("homolog");
      })
      .slice(0, 20)
      .map(a => `[${a.href || "#"}] ${(a.textContent || "").trim().slice(0, 60)}`)
      .join("\n")
  ).catch(() => "");
  console.log(`  WF-007 links candidatos:\n${diagLinks}`);

  // Leaf only — "homologacao de frequencia" is the PARENT toggle, not the action leaf
  const leafTargets = [
    "homologar frequencia", "homologar frequência",
    "frequencia mensal", "frequência mensal",
    "homologar frequencia mensal", "homologar frequência mensal",
  ];

  // Helper: check if current page content looks like unit/period selection (not portal home)
  async function isOffPortal() {
    const b = await page.evaluate(() => document.body.innerText.slice(0, 800)).catch(() => "");
    return b.includes("Seleção da Unidade") || b.includes("Seleção do Período") ||
           b.includes("PERÍODO PARA HOMOLOGAÇÃO") || b.includes("Homologar Frequência") ||
           (b.includes("Homologação") && !b.includes("Portal do Servidor"));
  }

  const clicked = await page.evaluate((leafTargets) => {
    const norm = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
    for (const a of document.querySelectorAll("ul.dropdown-menu a, .dropdown-menu a, a")) {
      const txt = norm(a.textContent || "").trim();
      if (leafTargets.some(t => txt === t)) { a.click(); return txt; }
    }
    return null;
  }, leafTargets).catch(() => null);

  if (clicked) {
    console.log(`  WF-007 strategy 1: clicou "${clicked}"`);
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await safeTimeout(1500);
    const url1 = page.url();
    const offPortal = await isOffPortal();
    console.log(`  WF-007 strategy 1 pós-click → URL: ${url1}, offPortal: ${offPortal}`);
    if (!url1.includes("servidor.jsf") || offPortal) return;
  }

  // Hover-chain: Chefia de Unidade → Homologação de Frequência → leaf
  console.log("  WF-007: tentando hover-chain...");
  const parentChain = [
    ["chefia da unidade", "chefia de unidade"],
    ["homologacao de frequencia", "homologação de frequência", "homologacoes", "homologações"],
  ];
  for (const labels of parentChain) {
    const deadline = Date.now() + 4000;
    let found = false;
    while (Date.now() < deadline && !found) {
      const els = page.locator("li.dropdown, li.menu-item, a");
      const n = await els.count().catch(() => 0);
      for (let i = 0; i < n && !found; i++) {
        const el = els.nth(i);
        const txt = normStr(await el.innerText().catch(() => "")).split("\n")[0].trim();
        if (labels.some(l => txt === l || txt.startsWith(l))) {
          await el.hover({ force: true }).catch(() => {});
          await safeTimeout(400);
          found = true;
        }
      }
      if (!found) await safeTimeout(200);
    }
  }
  const deadline2 = Date.now() + 4000;
  while (Date.now() < deadline2) {
    const els = page.locator("a");
    const n = await els.count().catch(() => 0);
    for (let i = 0; i < n; i++) {
      const el = els.nth(i);
      const txt = normStr(await el.innerText().catch(() => "")).trim();
      if (leafTargets.some(t => txt === t)) {
        await el.click({ force: true }).catch(() => {});
        await page.waitForLoadState("domcontentloaded").catch(() => {});
        await safeTimeout(1000);
        if (!page.url().includes("servidor.jsf") || await isOffPortal()) return;
        break;
      }
    }
    await safeTimeout(300);
  }

  // Fallback: stay on portal — selecionarUnidadePeriodo will find nothing and skip;
  // selecionarServidor will dump links so we can find the right URL
  console.log("  Fallback WF-007: permanecendo no portal para diagnóstico...");
}

// Select unit in busca_unidade-style page
async function selecionarUnidade(page, setor) {
  const sel = page.locator("select").first();
  if ((await sel.count()) === 0) return; // unit selection may not be shown
  const codeMatch = setor.match(/\d+\.\d+\.\d+\.\d+/);
  const opts = await sel.evaluate(s => Array.from(s.options).map(o => ({ v: o.value, t: o.text })));
  console.log(`  Todas as opções (${opts.length}):`, opts.map(o => `[${o.v}] ${o.t}`).join(" | "));
  const real = opts.filter(o => o.v !== "-1" && o.v !== "");
  let found = null;
  for (const opt of real) {
    const hasCode = codeMatch && opt.t.includes(codeMatch[0]);
    if (hasCode || normStr(opt.t).includes(normStr(setor)) || normStr(setor).includes(normStr(opt.t))) {
      found = opt.v; break;
    }
  }
  if (!found && real.length === 1) found = real[0].v;
  if (!found) {
    console.error(`  Opções disponíveis: ${real.map(o => o.t).join(" | ")}`);
    throw new Error(`Unidade não encontrada. Setor: ${setor}`);
  }
  await sel.selectOption(found);
  await safeTimeout(500);
}

// Select period in the select dropdown
async function selecionarPeriodo(page, mes, ano) {
  const sel = page.locator("select").first();
  if ((await sel.count()) === 0) return;
  const mesesPT = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"];
  const target = normStr(`${mesesPT[mes - 1]} de ${ano}`);
  const opts = await sel.evaluate(s => Array.from(s.options).map(o => ({ v: o.value, t: o.text })));
  const real = opts.filter(o => o.v !== "-1" && o.v !== "");
  let found = null;
  for (const opt of real) {
    const t = normStr(opt.t);
    if (t.includes(target) || opt.t.includes(`${String(mes).padStart(2,"0")}/${ano}`) || opt.t.includes(`${mes}/${ano}`)) {
      found = opt.v; break;
    }
  }
  if (!found && real.length > 0) found = real[0].v; // fallback: first available
  if (!found) throw new Error(`Período ${mes}/${ano} não encontrado`);
  await sel.selectOption(found);
  await safeTimeout(500);
}

async function clicarContinuar(page) {
  const btn = page.locator("input[value='Continuar >>'], input[value*='Continuar'], button:has-text('Continuar')").first();
  if ((await btn.count()) === 0) throw new Error("Botão Continuar não encontrado");
  await btn.click({ force: true });
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(1500);
}

// After menu navigation: handle unit and period selection screens if shown.
async function selecionarUnidadePeriodo(page, mes, ano) {
  const setor = process.env.CHEFIA_SETOR ?? "";
  const body1 = await page.evaluate(() => document.body.innerText.slice(0, 1500));
  console.log("  Tela atual:", body1.slice(0, 120).replace(/\n/g, " "));

  if (body1.includes("Seleção da Unidade") || body1.includes("Selecionar Unidade")) {
    await selecionarUnidade(page, setor);
    await clicarContinuar(page);
  }

  const body2 = await page.evaluate(() => document.body.innerText.slice(0, 1500));
  if (body2.includes("Seleção do Período") || body2.includes("Selecionar Período") || body2.includes("Selecione o Período")) {
    await selecionarPeriodo(page, mes, ano);
    await clicarContinuar(page);
  }
}

// Click any actionable element inside a row
async function clickRowAction(row) {
  const selectors = [
    "a[href]:not([href='#'])",
    "input[type=image]",
    "a",
    "input[type=submit]",
    "input[type=button]",
  ];
  for (const sel of selectors) {
    const el = row.locator(sel).first();
    if ((await el.count()) > 0) { await el.click({ force: true }); return sel; }
  }
  return null;
}

// Find and click the action element for a specific server (by SIAPE or name)
async function selecionarServidor(page, wf, nome, siape) {
  await safeTimeout(500);

  // Strategy 1: row containing SIAPE
  if (siape) {
    const row = page.locator(`tr:has-text('${siape}')`).first();
    if ((await row.count()) > 0) {
      const sel = await clickRowAction(row);
      if (sel) { console.log(`  [${wf}] selecionarServidor: SIAPE row, clicked '${sel}'`); return; }
    }
  }

  // Strategy 2: row containing first name
  const primeiroNome = nome.split(" ")[0];
  const rowByNome = page.locator(`tr:has-text('${primeiroNome}')`).first();
  if ((await rowByNome.count()) > 0) {
    const sel = await clickRowAction(rowByNome);
    if (sel) { console.log(`  [${wf}] selecionarServidor: nome row, clicked '${sel}'`); return; }
  }

  // Strategy 3: generic "Selecionar" link/button anywhere
  const selectLink = page.locator(
    "a[title*='Selecionar'], a:has-text('Selecionar'), input[title*='Selecionar'], input[value*='Selecionar']"
  ).first();
  if ((await selectLink.count()) > 0) { await selectLink.click({ force: true }); return; }

  // Failure: full debug dump
  await page.screenshot({ path: `/tmp/${wf}-debug.png`, fullPage: true }).catch(() => {});
  const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 4000)).catch(() => "");
  const elements = await page.evaluate(() =>
    Array.from(document.querySelectorAll("a, input[type=image], input[type=submit], input[type=button], input[type=checkbox]"))
      .slice(0, 40)
      .map(el => `[${el.tagName}|type=${el.type || ""}|val=${el.value || ""}|title=${el.title || ""}] ${(el.textContent || "").trim().slice(0, 60)}`)
      .filter(t => t.length > 10)
      .join("\n")
  ).catch(() => "");
  throw new Error(`${wf}: servidor '${nome}' não encontrado\nURL: ${page.url()}\nBody:\n${bodyText}\n\nElements:\n${elements}`);
}

// WF-006: Homologar ponto eletrônico para um servidor/mês
async function wf006PontoEletronico(page, { nome, siape, mes, ano, politicaHe }) {
  await navegarMenuHomologacaoPonto(page);
  await selecionarUnidadePeriodo(page, mes, ano);
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  await selecionarServidor(page, "WF-006", nome, siape);
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(2000); // extra wait for AJAX calendar content

  const urlAposServidor = page.url();
  const bodyAposServidor = await page.evaluate(() => document.body.innerText.slice(0, 1200)).catch(() => "");
  console.log(`  [WF-006] Após seleção servidor → URL: ${urlAposServidor}`);
  console.log(`  [WF-006] Corpo: ${bodyAposServidor.slice(0, 400).replace(/\n/g, " ")}`);

  // Política HE: autorizar → preencher HA com valor de HE; zerar → preencher HA com 00:00
  if (politicaHe === "autorizar" || politicaHe === "zerar") {
    const haInputs = page.locator(
      "input[name*='ha'], input[id*='ha'], td.ha input, " +
      "input[name*='horaAutorizada'], input[id*='horaAutorizada'], " +
      "input[name*='autorizadas'], input[id*='autorizadas']"
    );
    const heInputs = page.locator(
      "input[name*='he'], input[id*='he'], td.he input, " +
      "input[name*='horaExcedente'], input[id*='horaExcedente'], " +
      "input[name*='excedentes'], input[id*='excedentes']"
    );
    const haCount = await haInputs.count();
    const heCount = await heInputs.count();

    // Diagnostic: dump all inputs to understand page structure
    const allInputs = await page.evaluate(() =>
      Array.from(document.querySelectorAll("input[type=text], input:not([type])"))
        .slice(0, 30)
        .map(e => `[name=${e.name||""}|id=${e.id||""}|val=${e.value||""}|cls=${e.className||""}]`)
        .join(" | ")
    ).catch(() => "");
    console.log(`  [WF-006] HA inputs: ${haCount}, HE inputs: ${heCount}`);
    console.log(`  [WF-006] All text inputs: ${allInputs}`);
    await page.screenshot({ path: `/tmp/wf006-he-${siape||nome.split(" ")[0]}.png`, fullPage: true }).catch(() => {});

    if (politicaHe === "autorizar" && haCount > 0 && heCount > 0) {
      for (let i = 0; i < haCount; i++) {
        const heVal = await heInputs.nth(i).inputValue().catch(() => "");
        if (heVal && heVal !== "00:00" && heVal !== "0") {
          await haInputs.nth(i).fill(heVal).catch(() => {});
        }
      }
    } else if (politicaHe === "zerar" && haCount > 0) {
      for (let i = 0; i < haCount; i++) {
        await haInputs.nth(i).fill("00:00").catch(() => {});
      }
    }
    await safeTimeout(400);
  }

  // Clicar em Homologar — use input/button only; a:has-text matches nav menu items
  const homBtn = page.locator(
    "input[value='Homologar'], input[value*='omologar'], button:has-text('Homologar'), " +
    "a:not([class*='menu']):not([id*='menu']):not([class*='item']):has-text('Homologar')"
  ).first();
  if ((await homBtn.count()) === 0) throw new Error(`WF-006: botão Homologar não encontrado para ${nome}`);
  await homBtn.click({ force: true });
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  // Confirmar popup se houver
  const confirmBtn = page.locator("input[value='Confirmar'], button:has-text('Confirmar'), input[value='Sim']").first();
  if ((await confirmBtn.count()) > 0) {
    await confirmBtn.click({ force: true }).catch(() => {});
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await safeTimeout(500);
  }

  const urlFinal006 = page.url();
  const bodyFinal006 = await page.evaluate(() => document.body.innerText.slice(0, 800)).catch(() => "");
  console.log(`  [WF-006] Pós-homologar → URL: ${urlFinal006}`);
  console.log(`  [WF-006] Corpo final: ${bodyFinal006.replace(/\n/g, " ").slice(0, 600)}`);

  // Detect SIGRH error messages in body after clicking Homologar
  const erroSigrh = bodyFinal006.match(/Não é possível[^.]+\./i)
    ?? bodyFinal006.match(/não foi realizada[^.]*\./i)
    ?? bodyFinal006.match(/Erro[^.]+\./i);
  if (erroSigrh) throw new Error(`WF-006: SIGRH bloqueou — ${erroSigrh[0].trim()}`);
}

// WF-007: Homologar frequência mensal para um servidor/mês
async function wf007Frequencia(page, { nome, siape, mes, ano }) {
  await navegarMenuHomologacaoFrequencia(page);
  await selecionarUnidadePeriodo(page, mes, ano);
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  // Diagnóstico: dump corpo + elementos interativos da lista antes de selecionar servidor
  const bodyList007 = await page.evaluate(() => document.body.innerText.slice(0, 3000)).catch(() => "");
  const rowEls007 = await page.evaluate((siape) => {
    // Find row containing the SIAPE string (no pseudo-selectors in browser)
    const rows = Array.from(document.querySelectorAll("tr"));
    const row = siape
      ? rows.find(r => r.innerText.includes(siape))
      : (rows.find(r => r.querySelectorAll("td").length > 2) || rows[1]);
    if (!row) return "row not found";
    return Array.from(row.querySelectorAll("a, input, button, img"))
      .map(e => `[${e.tagName}|type=${e.type||""}|val=${e.value||""}|alt=${e.alt||""}|txt=${(e.textContent||"").trim().slice(0,30)}|cls=${e.className||""}]`)
      .join(" | ");
  }, siape).catch(() => "err");
  // Also dump ALL non-menu submit/button/a-homologar elements on the page
  const pageActionEls = await page.evaluate(() =>
    Array.from(document.querySelectorAll("input[type=submit], input[type=button], button, input[type=image]"))
      .map(e => `[${e.tagName}|type=${e.type||""}|val=${e.value||""}|name=${e.name||""}|id=${e.id||""}]`)
      .join(" | ")
  ).catch(() => "");
  console.log(`  [WF-007] Lista body (3000): ${bodyList007.replace(/\n/g, " ").slice(0, 1500)}`);
  console.log(`  [WF-007] Row elements: ${rowEls007}`);
  console.log(`  [WF-007] Page action elements: ${pageActionEls}`);

  // Skip if frequency already homologated (img alt="Homologado" in server row)
  const jaHomologado = await page.evaluate((siape, nome) => {
    const rows = Array.from(document.querySelectorAll("tr"));
    const row = rows.find(r => siape ? r.innerText.includes(siape) : r.innerText.toLowerCase().includes(nome.toLowerCase().split(" ")[0]));
    if (!row) return false;
    return Array.from(row.querySelectorAll("img")).some(img => /homologad/i.test(img.alt || ""));
  }, siape, nome).catch(() => false);

  if (jaHomologado) {
    console.log(`  [WF-007] Frequência já homologada para ${nome} — skip`);
    return;
  }

  // Se servidor não aparece na lista WF-007 → ponto provavelmente não homologado → skip
  const servidorNaLista = await page.evaluate((siape, nome) => {
    const norm = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
    const rows = Array.from(document.querySelectorAll("tr"));
    return rows.some(r => siape ? r.innerText.includes(siape) : norm(r.innerText).includes(norm(nome.split(" ")[0])));
  }, siape, nome).catch(() => false);

  if (!servidorNaLista) {
    console.log(`  [WF-007] ${nome} não aparece na lista de frequência — ponto pode não estar homologado ou servidor está em outra unidade. Skip.`);
    return;
  }

  // Step 1: click server row link (navigates to individual frequency form)
  await selecionarServidor(page, "WF-007", nome, siape);
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  const url007 = page.url();
  const body007 = await page.evaluate(() => document.body.innerText.slice(0, 1500)).catch(() => "");
  const allBtns = await page.evaluate(() =>
    Array.from(document.querySelectorAll("input[type=submit], input[type=button], button, a[onclick]"))
      .map(el => `[${el.tagName}|type=${el.type||""}|val=${el.value||""}|txt=${(el.textContent||"").trim().slice(0,30)}|id=${el.id||""}]`)
      .filter(t => t.length > 15)
      .slice(0, 30)
      .join(" | ")
  ).catch(() => "");
  console.log(`  [WF-007] Após seleção → URL: ${url007}`);
  console.log(`  [WF-007] Btns: ${allBtns}`);
  console.log(`  [WF-007] Corpo: ${body007.replace(/\n/g, " ").slice(0, 600)}`);

  // Step 2: find and click Homologar button on individual frequency form
  const homBtnSel =
    "input[value='Homologar'], input[value*='omologar'], " +
    "button:has-text('Homologar'), " +
    "a:not([class*='menu']):not([id*='menu']):not([class*='item']):has-text('Homologar')";
  const homBtn = page.locator(homBtnSel).first();
  if ((await homBtn.count()) === 0) {
    // Read-only page (frequency already done) or navigation issue — skip gracefully
    if (body007.includes("Ponto Associado ao Mês") || body007.includes("já homologad") || body007.includes("Homologação de Frequência")) {
      console.log(`  [WF-007] Frequência já homologada (read-only) para ${nome} — skip`);
      return;
    }
    throw new Error(`WF-007: botão Homologar não encontrado para ${nome}\nURL: ${url007}\nBtns: ${allBtns}\nBody: ${body007.slice(0, 400)}`);
  }
  await homBtn.click({ force: true });
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  const confirmBtn = page.locator("input[value='Confirmar'], button:has-text('Confirmar'), input[value='Sim']").first();
  if ((await confirmBtn.count()) > 0) {
    await confirmBtn.click({ force: true }).catch(() => {});
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await safeTimeout(500);
  }

  const urlFinal007 = page.url();
  const bodyFinal007 = await page.evaluate(() => document.body.innerText.slice(0, 800)).catch(() => "");
  console.log(`  [WF-007] Pós-homologar → URL: ${urlFinal007}`);
  console.log(`  [WF-007] Corpo: ${bodyFinal007.replace(/\n/g, " ").slice(0, 400)}`);

  const erroSigrh007 = bodyFinal007.match(/Não é possível[^.]+\./i)
    ?? bodyFinal007.match(/não foi realizada[^.]*\./i);
  if (erroSigrh007) throw new Error(`WF-007: SIGRH bloqueou — ${erroSigrh007[0].trim()}`);
}

// Homologa ponto (WF-006) + frequência (WF-007) para um servidor/mês
export async function homologarServidor(browser, entry) {
  const page = browser._page;
  if (!page) throw new Error("Browser não inicializado");

  console.log(`  [WF-006] Homologando ponto eletrônico…`);
  await wf006PontoEletronico(page, entry);

  console.log(`  [WF-007] Homologando frequência…`);
  await wf007Frequencia(page, entry);
}
