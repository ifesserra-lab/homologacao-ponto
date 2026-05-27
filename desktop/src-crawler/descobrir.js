import { readFileSync, writeFileSync, existsSync } from "fs";
import yaml from "js-yaml";

const PORTAL_URL = "https://sigrh.ifes.edu.br/sigrh/servidor/portal/servidor.jsf";
const BUSCA_UNIDADE_URL = "https://sigrh.ifes.edu.br/sigrh/dap/busca_unidade.jsf";

function normalizeText(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
}

async function safeTimeout(ms) { return new Promise(r => setTimeout(r, ms)); }

// Navega pelo menu: Chefia da Unidade → Homologações → Controle de Frequência
async function navegarMenuChefia(browser) {
  const page = browser._page;

  // Strategy 1: JS evaluate click on leaf node (fires onclick without visibility requirement)
  // The leaf links are hidden inside Bootstrap dropdowns; .click() bypasses that.
  const clicked = await page.evaluate(() => {
    const norm = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
    const leafTargets = ["controle de frequencia", "controle de frequência", "ponto eletronico", "ponto eletrônico"];
    // Walk all anchors; skip those that are parent-dropdown openers (contain many children)
    for (const a of document.querySelectorAll("ul.dropdown-menu a, .dropdown-menu a, a")) {
      const txt = norm(a.textContent || "");
      // Must be exact leaf match, not a parent whose innerText contains many children
      if (leafTargets.some(t => txt === t)) {
        a.click();
        return true;
      }
    }
    return false;
  }).catch(() => false);

  if (clicked) {
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await safeTimeout(1500);
    const url = page.url();
    if (!url.includes("servidor.jsf")) return; // navigated away — success
    // Still on servidor.jsf; onclick may have been a sub-menu toggle, try again after delay
  }

  // Strategy 2: hover-chain then JS click
  console.log("  Tentando hover-chain...");
  const norm = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();

  const hoverTargets = [
    ["chefia da unidade", "chefia de unidade"],
    ["homologacoes", "homologações"],
  ];
  for (const labels of hoverTargets) {
    const deadline = Date.now() + 4000;
    let found = false;
    while (Date.now() < deadline && !found) {
      const els = page.locator("li.dropdown, li.menu-item, a");
      const n = await els.count().catch(() => 0);
      for (let i = 0; i < n && !found; i++) {
        const el = els.nth(i);
        const txt = norm(await el.innerText().catch(() => "")).split("\n")[0].trim();
        if (labels.some(l => txt === l || txt.startsWith(l))) {
          await el.hover({ force: true }).catch(() => {});
          await safeTimeout(400);
          found = true;
        }
      }
      if (!found) await safeTimeout(200);
    }
  }

  // After hover-chain, click the leaf
  const leafTargets2 = ["controle de frequencia", "controle de frequência", "ponto eletronico", "ponto eletrônico"];
  const deadline2 = Date.now() + 4000;
  while (Date.now() < deadline2) {
    const els = page.locator("a");
    const n = await els.count().catch(() => 0);
    for (let i = 0; i < n; i++) {
      const el = els.nth(i);
      const txt = norm(await el.innerText().catch(() => "")).trim();
      if (leafTargets2.some(t => txt === t)) {
        await el.click({ force: true }).catch(() => {});
        await page.waitForLoadState("domcontentloaded").catch(() => {});
        await safeTimeout(1000);
        const url = page.url();
        if (!url.includes("servidor.jsf")) return;
        break;
      }
    }
    await safeTimeout(300);
  }

  // Strategy 3: direct URL (last resort — works if session is fully initialized)
  console.log("  Fallback: URL direta busca_unidade.jsf");
  await page.goto(BUSCA_UNIDADE_URL);
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(1500);
}

// Seleciona a unidade no select de busca_unidade.jsf
async function selecionarUnidade(page, setor) {
  const normSetor = normalizeText(setor);
  const codeMatch = setor.match(/\d+\.\d+\.\d+\.\d+/);

  const sel = page.locator("select").first();
  if ((await sel.count()) === 0) throw new Error("Select de unidade não encontrado");

  const opts = await sel.evaluate(s => Array.from(s.options).map(o => ({ val: o.value, txt: o.text })));
  console.log(`  Opções de unidade disponíveis: ${opts.length}`);

  let found = null;
  for (const opt of opts) {
    if (opt.val === "-1" || opt.val === "") continue;
    const normTxt = normalizeText(opt.txt);
    const hasCode = codeMatch && opt.txt.includes(codeMatch[0]);
    if (hasCode || normTxt.includes(normSetor) || normSetor.includes(normTxt)) {
      found = opt.val;
      console.log(`  Unidade selecionada: ${opt.txt}`);
      break;
    }
  }

  if (!found && opts.length > 1) {
    // Única unidade disponível (além do "--SELECIONE--")
    const real = opts.filter(o => o.val !== "-1" && o.val !== "");
    if (real.length === 1) {
      found = real[0].val;
      console.log(`  Única unidade disponível: ${real[0].txt}`);
    }
  }

  if (!found) throw new Error(`Unidade não encontrada no select. Setor: ${setor}`);

  await sel.selectOption(found);
  await safeTimeout(500);
}

// Seleciona o período (mês/ano corrente) no select de período
async function selecionarPeriodo(page, mes, ano) {
  const sel = page.locator("select").first();
  if ((await sel.count()) === 0) throw new Error("Select de período não encontrado");

  const opts = await sel.evaluate(s => Array.from(s.options).map(o => ({ val: o.value, txt: o.text })));
  console.log(`  Opções de período: ${opts.length}`);

  // Meses em português
  const mesesPT = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"];
  const mesTxt = mesesPT[mes - 1];
  const target = `${mesTxt} de ${ano}`;
  const normTarget = normalizeText(target);

  let found = null;
  for (const opt of opts) {
    if (opt.val === "-1" || opt.val === "") continue;
    const normTxt = normalizeText(opt.txt);
    if (normTxt.includes(normTarget) || normTxt.includes(normTarget.replace(" de ", " "))
        || opt.txt.includes(`${String(mes).padStart(2,"0")}/${ano}`)
        || opt.txt.includes(`${mes}/${ano}`)) {
      found = opt.val;
      console.log(`  Período selecionado: ${opt.txt}`);
      break;
    }
  }

  // Fallback: primeiro período disponível
  if (!found) {
    const real = opts.filter(o => o.val !== "-1" && o.val !== "");
    if (real.length > 0) {
      found = real[0].val;
      console.log(`  Período fallback (primeiro): ${real[0].txt}`);
    }
  }

  if (!found) throw new Error(`Período ${target} não encontrado`);

  await sel.selectOption(found);
  await safeTimeout(500);
}

// Clica no botão "Continuar >>" na página atual
async function clicarContinuar(page) {
  const btn = page.locator(
    "input[value='Continuar >>'], input[value*='Continuar'], button:has-text('Continuar')"
  ).first();
  if ((await btn.count()) === 0) throw new Error("Botão Continuar não encontrado");
  await btn.click({ force: true });
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(1500);
}

// Raspa a lista de servidores da página de folhas de ponto
// Padrão da célula: "NOME COMPLETO (SIAPE)" — ex: "CELIO PROLICIANO MAIOLI (1534589)"
function _rasparServidores(html) {
  const servidores = [];
  const seen = new Set();
  const pattern = /([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÀÈÌÒÙÇ][A-ZÁÉÍÓÚÂÊÎÔÛÃÕÀÈÌÒÙÇ\s]+?)\s+\((\d{6,8})\)/g;
  for (const m of html.matchAll(pattern)) {
    const nome = m[1].trim();
    const siape = m[2];
    if (nome.length > 5 && !seen.has(siape)) {
      seen.add(siape);
      servidores.push({ nome, siape });
    }
  }
  return servidores;
}

export async function descobrirServidores(browser, setor) {
  if (!browser._page) throw new Error("Browser não inicializado");

  const page = browser._page;
  const mes = new Date().getMonth() + 1;
  const ano = new Date().getFullYear();

  // ── 1. Navegar para o portal do servidor (carrega a sessão/menu corretamente)
  console.log("  Navegando para portal do servidor...");
  await page.goto(PORTAL_URL);
  await page.waitForLoadState("networkidle").catch(() => {});
  await safeTimeout(2000);

  // ── 2. Navegar via menu: Chefia de Unidade → Homologações → Ponto Eletrônico
  console.log("  Navegando menu: Chefia → Homologações → Ponto Eletrônico...");
  try {
    await navegarMenuChefia(browser);
    console.log("  Menu navegado com sucesso");
  } catch (e) {
    // Fallback direto para busca_unidade.jsf
    console.warn(`  AVISO: falha no menu (${e.message}), tentando URL direta...`);
    await page.goto(BUSCA_UNIDADE_URL);
    await page.waitForLoadState("networkidle").catch(() => {});
    await safeTimeout(1500);
  }

  // ── 3. Verificar em qual tela estamos
  const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 500));
  console.log("  Tela atual:", bodyText.substring(0, 100).replace(/\n/g, " "));

  // ── 4. Se mostrar "Seleção da Unidade", selecionar o setor
  if (bodyText.includes("Seleção da Unidade") || bodyText.includes("Selecionar Unidade")) {
    console.log("  Selecionando unidade...");
    await selecionarUnidade(page, setor);
    await clicarContinuar(page);
    await safeTimeout(1000);
  }

  // ── 5. Se mostrar "Seleção do Período", selecionar mês/ano corrente
  const bodyText2 = await page.evaluate(() => document.body.innerText.substring(0, 500));
  console.log("  Tela após unidade:", bodyText2.substring(0, 100).replace(/\n/g, " "));

  if (bodyText2.includes("Seleção do Período") || bodyText2.includes("Período")) {
    console.log(`  Selecionando período ${mes}/${ano}...`);
    await selecionarPeriodo(page, mes, ano);
    await clicarContinuar(page);
    await safeTimeout(1500);
  }

  // ── 6. Raspar a lista de servidores
  const html = await page.content();
  const servidores = _rasparServidores(html);
  console.log(`  Servidores encontrados: ${servidores.length}`);

  // Fallback: tentar raspar de células td com padrão "NOME (SIAPE)"
  if (servidores.length === 0) {
    const cells = page.locator("td");
    const n = await cells.count();
    const seen = new Set();
    for (let i = 0; i < n; i++) {
      const txt = (await cells.nth(i).innerText().catch(() => "")).trim();
      const m = txt.match(/^([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÀÈÌÒÙÇ][A-ZÁÉÍÓÚÂÊÎÔÛÃÕÀÈÌÒÙÇ\s]+?)\s+\((\d{6,8})\)$/);
      if (!m) continue;
      const nome = m[1].trim();
      const siape = m[2];
      if (!seen.has(siape)) {
        seen.add(siape);
        servidores.push({ nome, siape });
      }
    }
    console.log(`  Servidores via td scan: ${servidores.length}`);
  }

  return servidores;
}

// Merge conservador: adiciona novos, atualiza SIAPE de existentes, preserva manuais
export function mergeServidoresYaml(yamlPath, encontrados) {
  let existing = { servidores: [], anos: [new Date().getFullYear()] };
  if (existsSync(yamlPath)) {
    try { existing = yaml.load(readFileSync(yamlPath, "utf-8")) ?? existing; } catch {}
  }

  const existentes = existing.servidores ?? [];
  const byNome  = new Map(existentes.map(s => [s.nome?.toUpperCase(), s]));
  const bySiape = new Map(existentes.filter(s => s.siape).map(s => [String(s.siape), s]));

  let adicionados = 0, atualizados = 0;

  for (const novo of encontrados) {
    const key = novo.nome.toUpperCase();
    if (novo.siape && bySiape.has(novo.siape)) {
      const ex = bySiape.get(novo.siape);
      if (ex.nome !== novo.nome) { ex.nome = novo.nome; atualizados++; }
    } else if (byNome.has(key)) {
      const ex = byNome.get(key);
      if (!ex.siape && novo.siape) { ex.siape = novo.siape; atualizados++; }
    } else {
      existentes.push({ nome: novo.nome, siape: novo.siape });
      adicionados++;
    }
  }

  existing.servidores = existentes.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  return { data: existing, adicionados, atualizados };
}
