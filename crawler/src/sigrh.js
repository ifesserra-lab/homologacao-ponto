#!/usr/bin/env node
import { chromium } from "playwright";

const LOGIN_URL = "https://sigrh.ifes.edu.br/sigrh/login.jsf";

const MENU_LABELS = [
  ["Homologacao de Ponto Eletronico", "Homologação de Ponto Eletrônico"],
  ["Relatorio", "Relatório", "Relatórios"],
  ["Espelho do Ponto", "Espelho de Ponto"],
];

function normalizeText(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
}

export class SigrhBrowser {
  constructor({ headed = false } = {}) {
    this.headed = headed;
    this._browser = null;
    this._page = null;
  }

  async start() {
    this._browser = await chromium.launch({ headless: !this.headed });
    const ctx = await this._browser.newContext();
    this._page = await ctx.newPage();
  }

  async login(username, password) {
    if (!this._page) await this.start();
    await this._page.goto(LOGIN_URL);
    await this._fillFirst(["input[name='username']", "input[name='login']", "#username"], username);
    await this._fillFirst(["input[type='password']", "input[name='password']", "#password"], password);
    await this._clickFirst(["input[type='submit']", "button[type='submit']", "button:has-text('Entrar')"]);
    await this._page.waitForLoadState("domcontentloaded");
    const html = await this._page.content();
    if (this._isBlocked(html)) throw new Error("CAPTCHA ou bloqueio anti-automação detectado");
    if (this._isInvalidLogin(html)) throw new Error("Credenciais inválidas");
    if (this._isExpired(html)) throw new Error("Sessão expirada");
    return true;
  }

  async navigateToEspelho() {
    for (const variants of MENU_LABELS) {
      await this._clickMenuVariants(variants);
    }
  }

  async searchServer(name, mes, ano, siape = null) {
    const page = this._page;
    // Select period
    if (mes) {
      const monthSel = await this._firstVisible(["#form\\:mes", "select[name='form:mes']"]);
      if (monthSel) await monthSel.selectOption(String(mes));
    }
    if (ano) {
      const yearInput = await this._firstVisible(["#form\\:ano", "input[name='form:ano']"]);
      if (yearInput) await yearInput.fill(String(ano));
    }
    // Check "search by server" checkbox
    const cb = await this._firstVisible(["#form\\:checkServidor", "input[name='form:checkServidor']"]);
    if (cb) {
      try { await cb.check(); } catch { await cb.click(); }
    }
    // Type server name
    const field = await this._firstVisible(["#form\\:nomeServidor", "input[name='form:nomeServidor']", "input[title='Servidor']"]);
    if (!field) throw new Error("Campo de nome do servidor não encontrado");
    await field.click();
    await field.fill("");
    await field.type(name, { delay: 50 });
    await page.waitForTimeout(1200);
    // Pick suggestion
    await this._pickSuggestion(name, siape);
    // Click Buscar
    const buscar = await this._firstVisible(["#form\\:buscarServidores", "input[name='form:buscarServidores']", "input[value='Buscar']"]);
    if (buscar) await buscar.click({ force: true });
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(500);
  }

  async findServerRows() {
    const page = this._page;
    const rows = page.locator("table.listagem tr");
    const count = await rows.count();
    const results = [];
    for (let i = 0; i < count; i++) {
      const row = rows.nth(i);
      const text = (await row.innerText().catch(() => "")).trim();
      if (!text || /SIAPE/i.test(text)) continue;
      const hasSelect = (await row.locator("a[title*='Selecionar'], a:has-text('Selecionar Servidor'), input[title*='Selecionar']").count()) > 0;
      const siapeMatch = text.match(/\b\d{5,}\b/);
      results.push({ text, siape: siapeMatch?.[0] ?? null, hasSelect, row });
    }
    return results;
  }

  async selectServer(rowData) {
    const sel = rowData.row.locator("a[title*='Selecionar'], a:has-text('Selecionar Servidor'), input[title*='Selecionar']");
    await sel.first().click();
    await this._page.waitForLoadState("domcontentloaded");
    await this._page.waitForTimeout(500);
  }

  async getHtml() {
    const page = this._page;
    const base = await page.content();
    const server = await this._inputValue(["#form\\:nomeServidor", "input[name='form:nomeServidor']"]);
    const year = await this._inputValue(["#form\\:ano", "input[name='form:ano']"]);
    const month = await this._inputValue(["#form\\:mes", "select[name='form:mes']"]);
    let ctx = "";
    if (server) ctx += `<div class="servidor">Servidor: ${server}</div>`;
    if (month && year) ctx += `<div class="periodo">Periodo: ${month}/${year}</div>`;
    return base + ctx;
  }

  async getUrl() { return this._page?.url() ?? ""; }
  async getTitle() { return this._page?.title() ?? ""; }

  async close() {
    if (this._browser) await this._browser.close();
    this._browser = null;
    this._page = null;
  }

  // ── private ────────────────────────────────────────────────────────────────

  async _fillFirst(selectors, value) {
    for (const s of selectors) {
      const loc = this._page.locator(s);
      if ((await loc.count()) > 0) { await loc.first().fill(value); return; }
    }
  }

  async _clickFirst(selectors) {
    for (const s of selectors) {
      const loc = this._page.locator(s);
      if ((await loc.count()) > 0) { await loc.first().click(); return; }
    }
  }

  async _firstVisible(selectors) {
    for (const s of selectors) {
      const loc = this._page.locator(s);
      if ((await loc.count()) > 0) return loc.first();
    }
    return null;
  }

  async _inputValue(selectors) {
    for (const s of selectors) {
      const loc = this._page.locator(s);
      if ((await loc.count()) > 0) {
        try { return (await loc.first().inputValue()).trim(); } catch { return ""; }
      }
    }
    return "";
  }

  async _clickMenuVariants(variants) {
    const deadline = Date.now() + 15000;
    while (Date.now() < deadline) {
      for (const label of variants) {
        const norm = normalizeText(label);
        const patterns = [
          `a:visible:has-text("${label}")`,
          `span:visible:has-text("${label}")`,
          `td:visible:has-text("${label}")`,
          `li:visible:has-text("${label}")`,
        ];
        for (const pat of patterns) {
          const loc = this._page.locator(pat);
          const n = await loc.count();
          for (let i = 0; i < n; i++) {
            const el = loc.nth(i);
            const txt = normalizeText(await el.innerText().catch(() => ""));
            if (txt.includes(norm)) {
              await el.click();
              await this._page.waitForLoadState("domcontentloaded").catch(() => {});
              await this._page.waitForTimeout(500);
              return;
            }
          }
        }
      }
      await this._page.waitForTimeout(300);
    }
    throw new Error(`Menu não encontrado: ${variants[0]}`);
  }

  async _pickSuggestion(name, siape) {
    const page = this._page;
    const normName = normalizeText(name);
    const deadline = Date.now() + 8000;
    const selectors = [
      "td.richfaces_suggestionSelectValue:visible",
      "tr.richfaces_suggestionEntry:visible td",
      "#form\\:suggestionServidor\\:suggest tr td",
      "[id='form:suggestionServidor:suggest'] tr td",
    ];
    while (Date.now() < deadline) {
      for (const s of selectors) {
        const items = page.locator(s);
        const n = await items.count();
        for (let i = 0; i < n; i++) {
          const item = items.nth(i);
          const text = (await item.innerText().catch(() => "")).trim();
          if (!text) continue;
          if (normalizeText(text).includes(normName)) {
            if (!siape || text.includes(siape)) {
              await item.click({ force: true });
              await page.waitForTimeout(1500);
              return;
            }
          }
        }
      }
      await page.waitForTimeout(300);
    }
    // Fallback: ArrowDown + Enter
    const field = await this._firstVisible(["#form\\:nomeServidor", "input[name='form:nomeServidor']"]);
    if (field) {
      await field.press("ArrowDown");
      await page.waitForTimeout(800);
      await field.press("Enter");
      await page.waitForTimeout(1500);
    }
  }

  _isBlocked(html) { return /captcha|mfa|anti-autom|bloqueio de autom/i.test(html); }
  _isInvalidLogin(html) { return /senha inval|senha invál|usuario ou senha|usuário ou senha/i.test(html); }
  _isExpired(html) { return /sess[aã]o expirada/i.test(html); }
}
