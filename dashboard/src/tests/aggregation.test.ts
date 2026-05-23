import { describe, it, expect } from "vitest";
import { parseHHMM, formatMin, aggregateMonth } from "../lib/aggregation";
import type { RegistroDia } from "../types/dashboard";

describe("parseHHMM", () => {
  it("returns null for null input", () => {
    expect(parseHHMM(null)).toBeNull();
  });

  it("returns null for undefined input", () => {
    expect(parseHHMM(undefined)).toBeNull();
  });

  it("parses HH:MM to total minutes", () => {
    expect(parseHHMM("08:30")).toBe(510);
  });

  it("parses 00:00 to 0", () => {
    expect(parseHHMM("00:00")).toBe(0);
  });

  it("returns null for invalid format", () => {
    expect(parseHHMM("invalid")).toBeNull();
  });

  it("returns null for empty string", () => {
    expect(parseHHMM("")).toBeNull();
  });
});

describe("formatMin", () => {
  it("returns dash for null", () => {
    expect(formatMin(null)).toBe("—");
  });

  it("formats minutes to HH:MM", () => {
    expect(formatMin(510)).toBe("08:30");
  });

  it("formats zero to 00:00", () => {
    expect(formatMin(0)).toBe("00:00");
  });

  it("pads single-digit hours and minutes", () => {
    expect(formatMin(65)).toBe("01:05");
  });

  it("handles hours over 24", () => {
    expect(formatMin(1500)).toBe("25:00");
  });
});

describe("aggregateMonth", () => {
  it("returns zeros and null dncFinalMin for empty registros", () => {
    const result = aggregateMonth([]);
    expect(result.daysWithMarcacoes).toBe(0);
    expect(result.somaCreditoMin).toBe(0);
    expect(result.somaDebitoMin).toBe(0);
    expect(result.somaHhMin).toBe(0);
    expect(result.dncFinalMin).toBeNull();
  });

  it("counts days with non-empty marcacoes", () => {
    const registros: Partial<RegistroDia>[] = [
      { marcacoes: ["07:58", "17:00"], credito: null, debito: null, hh: null, dnc: null },
      { marcacoes: [], credito: null, debito: null, hh: null, dnc: null },
      { marcacoes: ["08:00", "12:00", "13:00", "17:00"], credito: null, debito: null, hh: null, dnc: null },
    ];
    const result = aggregateMonth(registros as RegistroDia[]);
    expect(result.daysWithMarcacoes).toBe(2);
  });

  it("sums credito ignoring nulls", () => {
    const registros: Partial<RegistroDia>[] = [
      { marcacoes: [], credito: "01:00", debito: null, hh: null, dnc: null },
      { marcacoes: [], credito: null, debito: null, hh: null, dnc: null },
      { marcacoes: [], credito: "00:30", debito: null, hh: null, dnc: null },
    ];
    const result = aggregateMonth(registros as RegistroDia[]);
    expect(result.somaCreditoMin).toBe(90);
  });

  it("sums debito ignoring nulls", () => {
    const registros: Partial<RegistroDia>[] = [
      { marcacoes: [], credito: null, debito: "02:00", hh: null, dnc: null },
      { marcacoes: [], credito: null, debito: "01:00", hh: null, dnc: null },
    ];
    const result = aggregateMonth(registros as RegistroDia[]);
    expect(result.somaDebitoMin).toBe(180);
  });

  it("reads dncFinalMin from last record", () => {
    const registros: Partial<RegistroDia>[] = [
      { marcacoes: [], credito: null, debito: null, hh: null, dnc: "01:00" },
      { marcacoes: [], credito: null, debito: null, hh: null, dnc: "00:30" },
    ];
    const result = aggregateMonth(registros as RegistroDia[]);
    expect(result.dncFinalMin).toBe(30);
  });

  it("dncFinalMin is null when last record dnc is null", () => {
    const registros: Partial<RegistroDia>[] = [
      { marcacoes: [], credito: null, debito: null, hh: null, dnc: "00:00" },
      { marcacoes: [], credito: null, debito: null, hh: null, dnc: null },
    ];
    const result = aggregateMonth(registros as RegistroDia[]);
    expect(result.dncFinalMin).toBeNull();
  });
});
