import { describe, it, expect } from "vitest";
import {
  parseHHMM,
  parseSignedHHMM,
  formatMin,
  pctCarga,
  countOcorrencias,
  aggregateMonth,
} from "./aggregation";

describe("parseHHMM", () => {
  it("parses valid time string", () => expect(parseHHMM("08:30")).toBe(510));
  it("parses zero", () => expect(parseHHMM("00:00")).toBe(0));
  it("returns null for null", () => expect(parseHHMM(null)).toBeNull());
  it("returns null for undefined", () => expect(parseHHMM(undefined)).toBeNull());
  it("returns null for empty string", () => expect(parseHHMM("")).toBeNull());
  it("returns null for bad format", () => expect(parseHHMM("abc")).toBeNull());
});

describe("parseSignedHHMM", () => {
  it("parses positive", () => expect(parseSignedHHMM("01:30")).toBe(90));
  it("parses negative", () => expect(parseSignedHHMM("-01:30")).toBe(-90));
  it("parses negative zero", () => expect(parseSignedHHMM("-00:00")).toBe(0));
  it("returns null for null", () => expect(parseSignedHHMM(null)).toBeNull());
});

describe("formatMin", () => {
  it("formats positive minutes", () => expect(formatMin(510)).toBe("08:30"));
  it("formats negative minutes", () => expect(formatMin(-90)).toBe("-01:30"));
  it("formats zero", () => expect(formatMin(0)).toBe("00:00"));
  it("formats null as em dash", () => expect(formatMin(null)).toBe("—"));
});

describe("pctCarga", () => {
  it("100% when equal", () => expect(pctCarga(480, 480)).toBe(100));
  it("50% when half", () => expect(pctCarga(240, 480)).toBe(50));
  it("caps at 100", () => expect(pctCarga(600, 480)).toBe(100));
  it("rounds correctly", () => expect(pctCarga(481, 480)).toBe(100));
  it("null when carga is 0", () => expect(pctCarga(100, 0)).toBeNull());
});

describe("countOcorrencias", () => {
  it("counts and deduplicates occurrences across days", () => {
    const registros = [
      { ocorrencias: ["LIC. PATERNIDADE (01/05/2025 a 05/05/2025)", "OUTRA"], marcacoes: [] },
      { ocorrencias: ["LIC. PATERNIDADE (01/05/2025 a 05/05/2025)"], marcacoes: [] },
      { ocorrencias: [], marcacoes: [] },
    ] as any;
    const result = countOcorrencias(registros);
    const pat = result.find(r => r.type === "LIC. PATERNIDADE");
    expect(pat?.count).toBe(2);
    const out = result.find(r => r.type === "OUTRA");
    expect(out?.count).toBe(1);
  });

  it("strips date suffix from occurrence type", () => {
    const registros = [{ ocorrencias: ["RECESSO (24/12/2024)"], marcacoes: [] }] as any;
    const result = countOcorrencias(registros);
    expect(result[0].type).toBe("RECESSO");
  });

  it("returns empty for no occurrences", () => {
    const registros = [{ ocorrencias: [], marcacoes: [] }] as any;
    expect(countOcorrencias(registros)).toHaveLength(0);
  });
});

describe("aggregateMonth", () => {
  it("sums credito minutes", () => {
    const registros = [
      { data: "2025-05-02", marcacoes: ["08:00", "17:00"], credito: "08:00", debito: null, hr: null, hh: null, dnc: null, credito_acumulado: null, situacao: null, ocorrencias: [] },
      { data: "2025-05-05", marcacoes: ["08:00", "17:00"], credito: "08:00", debito: null, hr: null, hh: null, dnc: null, credito_acumulado: null, situacao: null, ocorrencias: [] },
    ] as any;
    const agg = aggregateMonth(registros, null);
    expect(agg.somaCreditoMin).toBe(960);
    expect(agg.daysWithMarcacoes).toBe(2);
  });

  it("uses resumo balance when available", () => {
    const registros = [
      { data: "2025-05-02", marcacoes: ["08:00", "17:00"], credito: "08:00", debito: null, hr: null, hh: null, dnc: null, credito_acumulado: null, situacao: null, ocorrencias: [] },
    ] as any;
    const resumo = {
      total_horas_homologadas: "08:00",
      total_horas_registradas: "09:00",
      carga_horaria_esperada_mes: "176:00",
      saldo_horas_mes: "-10:00",
    } as any;
    const agg = aggregateMonth(registros, resumo);
    expect(agg.balanceMin).toBe(-600);
    expect(agg.cargaEsperadaMin).toBe(10560);
  });
});
