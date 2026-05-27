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
  const m = v.match(/^(\d+):(\d{2})$/);
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

    // he_nao_autorizado only blocks when policy is manual
    if (politicaHe === "manual") {
      const he = parseHHMM(r.he);
      const ha = parseHHMM(r.ha);
      if (he !== null && he > 0 && (ha === null || ha === 0)) razoes.add("he_nao_autorizado");
    }

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
          siape: raw.servidor?.siape ?? null,
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

// These URLs are for IFES SIGRH. Adjust if your instance differs.
const PONTO_HOMOLOG_URL = "https://sigrh.ifes.edu.br/sigrh/frequencia/ponto_eletronico/homologacao/busca_homologacao.jsf";
const FREQ_HOMOLOG_URL  = "https://sigrh.ifes.edu.br/sigrh/frequencia/homologacao/busca_frequencia.jsf";

async function safeTimeout(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// WF-006: Homologar ponto eletrônico para um servidor/mês
async function wf006PontoEletronico(page, { nome, siape, mes, ano, politicaHe }) {
  await page.goto(PONTO_HOMOLOG_URL);
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  // Preencher mês e ano
  const monthSel = page.locator("select[name*='mes'], #form\\:mes").first();
  if ((await monthSel.count()) > 0) await monthSel.selectOption(String(mes)).catch(() => {});

  const yearInput = page.locator("input[name*='ano'], #form\\:ano").first();
  if ((await yearInput.count()) > 0) await yearInput.fill(String(ano)).catch(() => {});

  // Buscar servidor
  const nomeField = page.locator("input[name*='nomeServidor'], input[title='Servidor'], #form\\:nomeServidor").first();
  if ((await nomeField.count()) > 0) {
    await nomeField.fill("").catch(() => {});
    await nomeField.type(nome, { delay: 50 }).catch(() => {});
    await safeTimeout(1200);
    // pick autocomplete suggestion matching siape or nome
    const suggestion = page.locator(`li:has-text('${siape ?? nome}'), .ui-autocomplete-item:has-text('${nome.split(" ")[0]}')`).first();
    if ((await suggestion.count()) > 0) await suggestion.click().catch(() => {});
  }

  const buscar = page.locator("input[value='Buscar'], button:has-text('Buscar'), #form\\:buscarServidores").first();
  if ((await buscar.count()) > 0) await buscar.click({ force: true }).catch(() => {});
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  // Abrir espelho do servidor
  const selectLink = page.locator("a[title*='Selecionar'], a:has-text('Selecionar'), input[title*='Selecionar']").first();
  if ((await selectLink.count()) === 0) throw new Error(`WF-006: servidor '${nome}' não encontrado na lista para ${MONTH_NAMES[mes]}/${ano}`);
  await selectLink.click();
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  // Política HE: autorizar → preencher HA com valor de HE; zerar → zerar HE
  if (politicaHe === "autorizar" || politicaHe === "zerar") {
    const haInputs = page.locator("input[name*='ha'], input[id*='ha'], td.ha input");
    const heInputs = page.locator("input[name*='he'], input[id*='he'], td.he input");
    const haCount = await haInputs.count();
    const heCount = await heInputs.count();
    if (politicaHe === "autorizar" && haCount > 0 && heCount > 0) {
      for (let i = 0; i < haCount; i++) {
        const heVal = await heInputs.nth(i).inputValue().catch(() => "");
        if (heVal && heVal !== "00:00" && heVal !== "0") {
          await haInputs.nth(i).fill(heVal).catch(() => {});
        }
      }
    } else if (politicaHe === "zerar" && heCount > 0) {
      for (let i = 0; i < heCount; i++) {
        await heInputs.nth(i).fill("00:00").catch(() => {});
      }
    }
    await safeTimeout(400);
  }

  // Clicar em Homologar
  const homBtn = page.locator("input[value='Homologar'], button:has-text('Homologar'), a:has-text('Homologar')").first();
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
}

// WF-007: Homologar frequência mensal para um servidor/mês
async function wf007Frequencia(page, { nome, siape, mes, ano }) {
  await page.goto(FREQ_HOMOLOG_URL);
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  const monthSel = page.locator("select[name*='mes'], #form\\:mes").first();
  if ((await monthSel.count()) > 0) await monthSel.selectOption(String(mes)).catch(() => {});

  const yearInput = page.locator("input[name*='ano'], #form\\:ano").first();
  if ((await yearInput.count()) > 0) await yearInput.fill(String(ano)).catch(() => {});

  const nomeField = page.locator("input[name*='nomeServidor'], input[title='Servidor'], #form\\:nomeServidor").first();
  if ((await nomeField.count()) > 0) {
    await nomeField.fill("").catch(() => {});
    await nomeField.type(nome, { delay: 50 }).catch(() => {});
    await safeTimeout(1200);
    const suggestion = page.locator(`li:has-text('${siape ?? nome}'), .ui-autocomplete-item:has-text('${nome.split(" ")[0]}')`).first();
    if ((await suggestion.count()) > 0) await suggestion.click().catch(() => {});
  }

  const buscar = page.locator("input[value='Buscar'], button:has-text('Buscar'), #form\\:buscarServidores").first();
  if ((await buscar.count()) > 0) await buscar.click({ force: true }).catch(() => {});
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  const selectLink = page.locator("a[title*='Selecionar'], a:has-text('Selecionar'), input[title*='Selecionar']").first();
  if ((await selectLink.count()) === 0) throw new Error(`WF-007: servidor '${nome}' não encontrado na frequência para ${MONTH_NAMES[mes]}/${ano}`);
  await selectLink.click();
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  const homBtn = page.locator("input[value='Homologar'], button:has-text('Homologar'), a:has-text('Homologar')").first();
  if ((await homBtn.count()) === 0) throw new Error(`WF-007: botão Homologar não encontrado para ${nome}`);
  await homBtn.click({ force: true });
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await safeTimeout(800);

  const confirmBtn = page.locator("input[value='Confirmar'], button:has-text('Confirmar'), input[value='Sim']").first();
  if ((await confirmBtn.count()) > 0) {
    await confirmBtn.click({ force: true }).catch(() => {});
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await safeTimeout(500);
  }
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
