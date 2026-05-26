#!/usr/bin/env node
import { chromium } from "playwright";

const LOGIN_URL = "https://sigrh.ifes.edu.br/sigrh/login.jsf";
const ESPELHO_URL = "https://sigrh.ifes.edu.br/sigrh/frequencia/ponto_eletronico/consulta/consulta_ponto_eletronico.jsf";

function normalizeText(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
}

export class SigrhBrowser {
  constructor({ headed = false } = {}) {
    this.headed = headed;
    this._browser = null;
    this._ctx = null;
    this._page = null;
  }

  async start() {
    this._browser = await this._launchBrowser();
    this._ctx = await this._browser.newContext();
    // Track new pages opened by SIGRH (popups/new tabs)
    this._ctx.on("page", (newPage) => {
      this._page = newPage;
    });
    this._page = await this._ctx.newPage();
  }

  async _launchBrowser() {
    const opts = { headless: !this.headed };
    // Try system browsers first (no download needed), then fall back to bundled Chromium
    const channels = process.platform === "win32"
      ? ["msedge", "chrome"]
      : ["chrome", "msedge"];
    for (const channel of channels) {
      try {
        return await chromium.launch({ ...opts, channel });
      } catch {}
    }
    return await chromium.launch(opts);
  }

  async login(username, password) {
    if (!this._page) await this.start();
    await this._page.goto(LOGIN_URL);
    await this._fillFirst(["input[name='username']", "input[name='login']", "#username"], username);
    await this._fillFirst(["input[type='password']", "input[name='password']", "#password"], password);
    await this._clickFirst(["input[type='submit']", "button[type='submit']", "button:has-text('Entrar')"]);
    await this._page.waitForLoadState("domcontentloaded").catch(() => {});
    // Dismiss "bater ponto" popup if present
    await this._dismissPontoPopup();
    const html = await this._page.content();
    if (this._isBlocked(html)) throw new Error("CAPTCHA ou bloqueio anti-automação detectado");
    if (this._isInvalidLogin(html)) throw new Error("Credenciais inválidas");
    if (this._isExpired(html)) throw new Error("Sessão expirada");
    return true;
  }

  async _dismissPontoPopup() {
    // SIGRH shows a popup asking to register attendance — click "Entrar sem bater ponto"
    const selectors = [
      "a:has-text('Entrar sem bater ponto')",
      "button:has-text('Entrar sem bater ponto')",
      "input[value*='sem bater']",
      "a:has-text('sem bater')",
      "a:has-text('Não registrar')",
    ];
    for (const s of selectors) {
      try {
        const loc = this._page.locator(s);
        if ((await loc.count()) > 0) {
          await loc.first().click({ force: true });
          await this._page.waitForLoadState("domcontentloaded").catch(() => {});
          await this._safeTimeout(500);
          return;
        }
      } catch {}
    }
  }

  async navigateToEspelho() {
    // Direct URL — portal menu uses JSF AJAX that doesn't change URL; goto is reliable
    await this._page.goto(ESPELHO_URL);
    await this._page.waitForLoadState("domcontentloaded").catch(() => {});
    await this._safeTimeout(500);
  }

  async searchServer(name, mes, ano, siape = null) {
    const page = this._page;
    if (mes) {
      const monthSel = await this._firstVisible(["#form\\:mes", "select[name='form:mes']"]);
      if (monthSel) await monthSel.selectOption(String(mes)).catch(() => {});
    }
    if (ano) {
      const yearInput = await this._firstVisible(["#form\\:ano", "input[name='form:ano']"]);
      if (yearInput) await yearInput.fill(String(ano)).catch(() => {});
    }
    const cb = await this._firstVisible(["#form\\:checkServidor", "input[name='form:checkServidor']"]);
    if (cb) {
      try { await cb.check(); } catch { try { await cb.click(); } catch {} }
    }
    const field = await this._firstVisible(["#form\\:nomeServidor", "input[name='form:nomeServidor']", "input[title='Servidor']"]);
    if (!field) throw new Error("Campo de nome do servidor não encontrado");
    await field.click().catch(() => {});
    await field.fill("").catch(() => {});
    await field.type(name, { delay: 50 }).catch(() => {});
    await this._safeTimeout(1200);
    await this._pickSuggestion(name, siape);
    const buscar = await this._firstVisible(["#form\\:buscarServidores", "input[name='form:buscarServidores']", "input[value='Buscar']"]);
    if (buscar) await buscar.click({ force: true }).catch(() => {});
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await this._safeTimeout(500);
  }

  async findServerRows() {
    const page = this._page;
    const rows = page.locator("table.listagem tr");
    const count = await rows.count().catch(() => 0);
    const results = [];
    for (let i = 0; i < count; i++) {
      const row = rows.nth(i);
      const text = (await row.innerText().catch(() => "")).trim();
      if (!text || /SIAPE/i.test(text)) continue;
      const hasSelect = (await row.locator("a[title*='Selecionar'], a:has-text('Selecionar Servidor'), input[title*='Selecionar']").count().catch(() => 0)) > 0;
      const siapeMatch = text.match(/\b\d{5,}\b/);
      results.push({ text, siape: siapeMatch?.[0] ?? null, hasSelect, row });
    }
    return results;
  }

  async selectServer(rowData) {
    const sel = rowData.row.locator("a[title*='Selecionar'], a:has-text('Selecionar Servidor'), input[title*='Selecionar']");
    await sel.first().click();
    await this._page.waitForLoadState("domcontentloaded").catch(() => {});
    await this._safeTimeout(500);
  }

  async getHtml() {
    const page = this._page;
    const base = await page.content().catch(() => "");
    const server = await this._inputValue(["#form\\:nomeServidor", "input[name='form:nomeServidor']"]);
    const year = await this._inputValue(["#form\\:ano", "input[name='form:ano']"]);
    const month = await this._inputValue(["#form\\:mes", "select[name='form:mes']"]);
    let ctx = "";
    if (server) ctx += `<div class="servidor">Servidor: ${server}</div>`;
    if (month && year) ctx += `<div class="periodo">Periodo: ${month}/${year}</div>`;
    return base + ctx;
  }

  async getUrl() { return this._page?.url() ?? ""; }
  async getTitle() { return this._page?.title().catch(() => "") ?? ""; }

  async close() {
    if (this._browser) await this._browser.close().catch(() => {});
    this._browser = null;
    this._ctx = null;
    this._page = null;
  }

  // ── private ─────────────────────────────────────────────────────────────

  async _safeTimeout(ms) {
    try {
      if (this._page && !this._page.isClosed()) {
        await this._page.waitForTimeout(ms);
      } else {
        await new Promise(r => setTimeout(r, ms));
      }
    } catch {
      await new Promise(r => setTimeout(r, ms));
    }
  }

  async _fillFirst(selectors, value) {
    for (const s of selectors) {
      try {
        const loc = this._page.locator(s);
        if ((await loc.count()) > 0) { await loc.first().fill(value); return; }
      } catch {}
    }
  }

  async _clickFirst(selectors) {
    for (const s of selectors) {
      try {
        const loc = this._page.locator(s);
        if ((await loc.count()) > 0) { await loc.first().click(); return; }
      } catch {}
    }
  }

  async _firstVisible(selectors) {
    for (const s of selectors) {
      try {
        const loc = this._page.locator(s);
        if ((await loc.count()) > 0) return loc.first();
      } catch {}
    }
    return null;
  }

  async _inputValue(selectors) {
    for (const s of selectors) {
      try {
        const loc = this._page.locator(s);
        if ((await loc.count()) > 0) return (await loc.first().inputValue()).trim();
      } catch {}
    }
    return "";
  }

  async _clickMenuVariants(variants) {
    const deadline = Date.now() + 15000;
    while (Date.now() < deadline) {
      for (const label of variants) {
        const norm = normalizeText(label);
        // Try visible first, then all (hidden menu nodes need force click)
        const patternSets = [
          [`a:visible`, `span:visible`, `td:visible`, `li:visible`],
          [`a`, `span`, `td`, `li`],
        ];
        for (const tags of patternSets) {
          for (const tag of tags) {
            try {
              const loc = this._page.locator(tag);
              const n = await loc.count();
              for (let i = 0; i < n; i++) {
                const el = loc.nth(i);
                const txt = normalizeText(await el.innerText().catch(() => ""));
                if (txt === norm || txt.startsWith(norm)) {
                  const pagePromise = this._ctx.waitForEvent("page", { timeout: 3000 }).catch(() => null);
                  await el.click({ force: true }).catch(() => {});
                  const newPage = await pagePromise;
                  if (newPage) {
                    this._page = newPage;
                    await newPage.waitForLoadState("domcontentloaded").catch(() => {});
                  } else {
                    await this._page.waitForLoadState("domcontentloaded").catch(() => {});
                  }
                  await this._safeTimeout(800);
                  return;
                }
              }
            } catch {}
          }
        }
      }
      await this._safeTimeout(300);
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
        try {
          const items = page.locator(s);
          const n = await items.count();
          for (let i = 0; i < n; i++) {
            const item = items.nth(i);
            const text = (await item.innerText().catch(() => "")).trim();
            if (!text) continue;
            if (normalizeText(text).includes(normName)) {
              if (!siape || text.includes(siape)) {
                await item.click({ force: true }).catch(() => {});
                await this._safeTimeout(1500);
                return;
              }
            }
          }
        } catch {}
      }
      await this._safeTimeout(300);
    }
    // Fallback: arrow + enter
    try {
      const field = await this._firstVisible(["#form\\:nomeServidor", "input[name='form:nomeServidor']"]);
      if (field) {
        await field.press("ArrowDown");
        await this._safeTimeout(800);
        await field.press("Enter");
        await this._safeTimeout(1500);
      }
    } catch {}
  }

  _isBlocked(html) { return /captcha|mfa|anti-autom|bloqueio de autom/i.test(html); }
  _isInvalidLogin(html) { return /senha inval|senha invál|usuario ou senha|usuário ou senha/i.test(html); }
  _isExpired(html) { return /sess[aã]o expirada/i.test(html); }
}
