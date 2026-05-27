import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdirSync, writeFileSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { scanStaleMonths } from "./stale.js";

const NOW = new Date();
const CURRENT_MONTH = NOW.getMonth() + 1;
const CURRENT_YEAR = NOW.getFullYear();
const PREV_MONTH = CURRENT_MONTH === 1 ? 12 : CURRENT_MONTH - 1;
const PREV_YEAR = CURRENT_MONTH === 1 ? CURRENT_YEAR - 1 : CURRENT_YEAR;

const MONTH_NAMES = [
  "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

function makeConfig(servidor, extra = {}) {
  return {
    anos: [CURRENT_YEAR],
    servidores: [{ nome: servidor, siape: "12345", ...extra }],
  };
}

function slugify(name) {
  return name.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function writeEspelho(outputDir, nome, mes, ano, data) {
  const serverDir = join(outputDir, "servidores", slugify(nome));
  mkdirSync(serverDir, { recursive: true });
  const mesName = MONTH_NAMES[mes];
  writeFileSync(join(serverDir, `espelho-${mesName}-${ano}.json`), JSON.stringify(data));
}

let tmpDir;
beforeEach(() => {
  tmpDir = join(tmpdir(), `stale-test-${Date.now()}`);
  mkdirSync(tmpDir, { recursive: true });
});
afterEach(() => {
  rmSync(tmpDir, { recursive: true, force: true });
});

describe("scanStaleMonths", () => {
  it("marks arquivo_ausente when file missing", () => {
    const result = scanStaleMonths(tmpDir, makeConfig("Maria Silva"));
    const item = result.find(r => r.mes === PREV_MONTH && r.ano === PREV_YEAR);
    expect(item?.reasons).toContain("arquivo_ausente");
  });

  it("marks mes_atual for current month (even if file exists and complete)", () => {
    writeEspelho(tmpDir, "Maria Silva", CURRENT_MONTH, CURRENT_YEAR, {
      status: "ok",
      registros: [],
      resumo: { saldo_horas_mes: "00:00", debito_mes_atual_nao_autorizado: "00:00" },
      captured_at: NOW.toISOString(),
    });
    const result = scanStaleMonths(tmpDir, makeConfig("Maria Silva"));
    const item = result.find(r => r.mes === CURRENT_MONTH && r.ano === CURRENT_YEAR);
    expect(item?.reasons).toEqual(["mes_atual"]);
  });

  it("marks dias_pendentes when any registro has situacao Pendente", () => {
    writeEspelho(tmpDir, "Maria Silva", PREV_MONTH, PREV_YEAR, {
      status: "ok",
      registros: [
        { situacao: "Homologado", ocorrencias: [], marcacoes: [] },
        { situacao: "Pendente", ocorrencias: [], marcacoes: [] },
      ],
      resumo: { saldo_horas_mes: "00:00", debito_mes_atual_nao_autorizado: "00:00" },
      captured_at: new Date().toISOString(),
    });
    const result = scanStaleMonths(tmpDir, makeConfig("Maria Silva"));
    const item = result.find(r => r.mes === PREV_MONTH && r.ano === PREV_YEAR);
    expect(item?.reasons).toContain("dias_pendentes");
  });

  it("marks debito_nao_autorizado when resumo has non-zero value", () => {
    writeEspelho(tmpDir, "Maria Silva", PREV_MONTH, PREV_YEAR, {
      status: "ok",
      registros: [{ situacao: "Homologado", ocorrencias: [], marcacoes: [] }],
      resumo: { saldo_horas_mes: "00:00", debito_mes_atual_nao_autorizado: "02:00" },
      captured_at: new Date().toISOString(),
    });
    const result = scanStaleMonths(tmpDir, makeConfig("Maria Silva"));
    const item = result.find(r => r.mes === PREV_MONTH && r.ano === PREV_YEAR);
    expect(item?.reasons).toContain("debito_nao_autorizado");
  });

  it("does not mark stale when complete and recently captured", () => {
    writeEspelho(tmpDir, "Maria Silva", PREV_MONTH, PREV_YEAR, {
      status: "ok",
      registros: [{ situacao: "Homologado", ocorrencias: [], marcacoes: [] }],
      resumo: { saldo_horas_mes: "00:00", debito_mes_atual_nao_autorizado: "00:00" },
      captured_at: new Date().toISOString(),
    });
    const result = scanStaleMonths(tmpDir, makeConfig("Maria Silva"));
    const item = result.find(r => r.mes === PREV_MONTH && r.ano === PREV_YEAR);
    expect(item).toBeUndefined();
  });

  it("marks saldo_negativo_antigo when negative balance and old capture", () => {
    const oldDate = new Date(Date.now() - 40 * 24 * 60 * 60 * 1000).toISOString();
    writeEspelho(tmpDir, "Maria Silva", PREV_MONTH, PREV_YEAR, {
      status: "ok",
      registros: [{ situacao: "Homologado", ocorrencias: [], marcacoes: [] }],
      resumo: { saldo_horas_mes: "-02:00", debito_mes_atual_nao_autorizado: "00:00" },
      captured_at: oldDate,
    });
    const result = scanStaleMonths(tmpDir, makeConfig("Maria Silva"));
    const item = result.find(r => r.mes === PREV_MONTH && r.ano === PREV_YEAR);
    expect(item?.reasons).toContain("saldo_negativo_antigo");
  });
});
