/**
 * Testes para scanLiberados usando dados reais do Celio Proliciano Maioli.
 *
 * Descoberta importante: os campos `he` nos espelhos do Celio contêm strings
 * malformadas ("08:00Horas", "04:02Total") resultantes de um bug do parser
 * que concatena o valor HH:MM com o rótulo da coluna adjacente.
 * parseHHMM("08:00Horas") → null, portanto he_nao_autorizado nunca dispara
 * para o Celio e politica_he não tem efeito diferencial nos dados atuais.
 */
import { describe, it, expect } from "vitest";
import { mkdirSync, writeFileSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { scanLiberados } from "./homologar.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REAL_DATA_DIR = resolve(__dirname, "../../data/runs");
const SLUG = "celio-proliciano-maioli";

// ── Integração: dados reais ───────────────────────────────────────────────────

describe("Celio — dados reais (integração)", () => {
  it("politica_he zerar: retorna 8 meses liberados", () => {
    const result = scanLiberados(REAL_DATA_DIR, "zerar", [SLUG]);
    expect(result.length).toBe(8);
  });

  it("politica_he manual: retorna os mesmos 8 meses (HE malformado não bloqueia)", () => {
    const zerar  = scanLiberados(REAL_DATA_DIR, "zerar",  [SLUG]);
    const manual = scanLiberados(REAL_DATA_DIR, "manual", [SLUG]);
    // Datas e nomes devem ser iguais — politica_he não tem efeito real nos dados atuais
    expect(manual.map(e => e.periodoReferencia)).toEqual(zerar.map(e => e.periodoReferencia));
  });

  it("fevereiro/2026 está liberado apesar de todos os dias terem he='08:00Horas'", () => {
    const result = scanLiberados(REAL_DATA_DIR, "manual", [SLUG]);
    const fev2026 = result.find(e => e.periodoReferencia === "Fevereiro/2026");
    expect(fev2026).toBeDefined();
    // he malformado → parseHHMM null → heEntries vazio → politica_he irrelevante
    expect(fev2026.heEntries.length).toBe(0);
  });

  it("meses liberados estão ordenados por período", () => {
    const result = scanLiberados(REAL_DATA_DIR, "zerar", [SLUG]);
    const periodos = result.map(e => e.periodoReferencia);
    // Fevereiro/2025 deve ser o primeiro, Fevereiro/2026 o último
    expect(periodos[0]).toBe("Fevereiro/2025");
    expect(periodos[periodos.length - 1]).toBe("Fevereiro/2026");
  });

  it("março/2026 não está liberado (bloqueado por marcacoes_incompletas)", () => {
    const result = scanLiberados(REAL_DATA_DIR, "zerar", [SLUG]);
    const marco2026 = result.find(e => e.periodoReferencia === "Março/2026");
    expect(marco2026).toBeUndefined();
  });

  it("abril/2026 não está liberado (marcacoes_incompletas + debito_nao_autorizado)", () => {
    const result = scanLiberados(REAL_DATA_DIR, "zerar", [SLUG]);
    const abril2026 = result.find(e => e.periodoReferencia === "Abril/2026");
    expect(abril2026).toBeUndefined();
  });

  it("entrada retornada tem slug e nome do Celio", () => {
    const result = scanLiberados(REAL_DATA_DIR, "zerar", [SLUG]);
    expect(result[0].slug).toBe(SLUG);
    expect(result[0].nome).toBe("CELIO PROLICIANO MAIOLI");
  });
});

// ── Sintético: Celio com HE limpo (HH:MM) ────────────────────────────────────
//
// Testa o comportamento ESPERADO quando o parser gerar HE em formato correto.
// Esses testes documentam como politica_he deveria funcionar para o Celio.

let tmpDir;
function setup() {
  tmpDir = join(tmpdir(), `celio-he-${Date.now()}`);
  mkdirSync(tmpDir, { recursive: true });
}
function teardown() {
  rmSync(tmpDir, { recursive: true, force: true });
}

function writeEspelhoCelio(politicaDir, overrideRegistros, overrideResumo = {}) {
  const slugPath = join(politicaDir, "servidores", SLUG);
  mkdirSync(slugPath, { recursive: true });
  const espelho = {
    periodo_referencia: "fevereiro/2026",
    status: "completed",
    servidor: { nome: "CELIO PROLICIANO MAIOLI", identificador: "1534589" },
    registros: overrideRegistros,
    resumo: { debito_mes_atual_nao_autorizado: "00:00", saldo_horas_mes: "00:00", ...overrideResumo },
  };
  writeFileSync(join(slugPath, "espelho-fevereiro-2026.json"), JSON.stringify(espelho));
}

// Dias do Celio com HE limpo (sem sufixo "Horas" — formato que deveria vir do parser)
const diasComHELimpo = [
  { data: "2026-02-09", dia_semana: "Segunda", situacao: null, marcacoes: ["08:00"], ocorrencias: ["REGISTRO DO PIT - DOCENTE (09/02/2026)"], he: "08:00", ha: null },
  { data: "2026-02-10", dia_semana: "Terça",   situacao: null, marcacoes: ["08:00"], ocorrencias: ["REGISTRO DO PIT - DOCENTE (10/02/2026)"], he: "08:00", ha: null },
  { data: "2026-02-11", dia_semana: "Quarta",  situacao: null, marcacoes: ["08:00"], ocorrencias: ["REGISTRO DO PIT - DOCENTE (11/02/2026)"], he: "08:00", ha: null },
];

const diasHEAutorizado = diasComHELimpo.map(r => ({ ...r, ha: "08:00" }));

describe("Celio — HE sintético limpo (politica_he diferencial)", () => {
  it("politica_he manual + HE limpo: bloqueia por he_nao_autorizado", () => {
    setup();
    try {
      writeEspelhoCelio(tmpDir, diasComHELimpo);
      const result = scanLiberados(tmpDir, "manual");
      expect(result.length).toBe(0);
    } finally { teardown(); }
  });

  it("politica_he zerar + HE limpo: libera (HE não bloqueia)", () => {
    setup();
    try {
      writeEspelhoCelio(tmpDir, diasComHELimpo);
      const result = scanLiberados(tmpDir, "zerar");
      expect(result.length).toBe(1);
      expect(result[0].periodoReferencia).toBe("fevereiro/2026");
    } finally { teardown(); }
  });

  it("politica_he autorizar + HE limpo: libera (HE não bloqueia)", () => {
    setup();
    try {
      writeEspelhoCelio(tmpDir, diasComHELimpo);
      const result = scanLiberados(tmpDir, "autorizar");
      expect(result.length).toBe(1);
    } finally { teardown(); }
  });

  it("politica_he zerar + HE limpo: heEntries preenchido com 3 dias", () => {
    setup();
    try {
      writeEspelhoCelio(tmpDir, diasComHELimpo);
      const result = scanLiberados(tmpDir, "zerar");
      expect(result[0].heEntries.length).toBe(3);
      expect(result[0].heEntries.every(r => r.he === "08:00")).toBe(true);
    } finally { teardown(); }
  });

  it("politica_he manual + HE limpo + HA preenchido: libera", () => {
    setup();
    try {
      writeEspelhoCelio(tmpDir, diasHEAutorizado);
      const result = scanLiberados(tmpDir, "manual");
      expect(result.length).toBe(1);
    } finally { teardown(); }
  });

  it("politica_he zerar + HE limpo + debito: ainda bloqueia por debito_nao_autorizado", () => {
    setup();
    try {
      writeEspelhoCelio(tmpDir, diasComHELimpo, { debito_mes_atual_nao_autorizado: "-66:19" });
      const result = scanLiberados(tmpDir, "zerar");
      expect(result.length).toBe(0);
    } finally { teardown(); }
  });

  it("politica_he zerar + HE limpo + dia Pendente: ainda bloqueia por dias_pendentes (AX-006)", () => {
    setup();
    try {
      const comPendente = [
        ...diasComHELimpo,
        { data: "2026-02-16", dia_semana: "Segunda", situacao: "Pendente", marcacoes: [], ocorrencias: ["ABONO DE HORAS"], he: null, ha: null },
      ];
      writeEspelhoCelio(tmpDir, comPendente);
      const result = scanLiberados(tmpDir, "zerar");
      expect(result.length).toBe(0);
    } finally { teardown(); }
  });
});

// ── Documentação: HE malformado vs. limpo ────────────────────────────────────

describe("Comportamento parseHHMM: HE malformado (bug parser) vs. limpo", () => {
  it("HE '08:00Horas' não é reconhecido → heEntries vazio → nenhum bloqueio por HE", () => {
    setup();
    try {
      const diasHEMalformado = diasComHELimpo.map(r => ({ ...r, he: "08:00Horas", ha: null }));
      writeEspelhoCelio(tmpDir, diasHEMalformado);
      // manual + HE malformado → liberado (parseHHMM retorna null, não bloqueia)
      const result = scanLiberados(tmpDir, "manual");
      expect(result.length).toBe(1);
      expect(result[0].heEntries.length).toBe(0);
    } finally { teardown(); }
  });

  it("HE '04:02Total' não é reconhecido → heEntries vazio", () => {
    setup();
    try {
      // marcacoes par (2) para não disparar marcacoes_incompletas
      const diasHETotal = [
        { data: "2026-02-09", dia_semana: "Segunda", situacao: null, marcacoes: ["08:00", "17:00"], ocorrencias: [], he: "04:02Total", ha: "02:00//", },
      ];
      writeEspelhoCelio(tmpDir, diasHETotal);
      const result = scanLiberados(tmpDir, "manual");
      expect(result.length).toBe(1);
      expect(result[0].heEntries.length).toBe(0);
    } finally { teardown(); }
  });
});
