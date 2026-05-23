import { describe, it, expect } from "vitest";
import { parseHHMM, formatMin, aggregateMonth } from "../lib/aggregation";
import type { RegistroDia, ResumoHorasApuradas } from "../types/dashboard";

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

describe("aggregateMonth with resumo", () => {
  const baseRegistro: RegistroDia = {
    data: "2026-05-02",
    dia_semana: "Sabado",
    marcacoes: ["07:58", "17:00"],
    ocorrencias: [],
    observacoes: [],
    situacao: null,
    textos_visiveis: [],
    hr: "08:00",
    hc: null,
    he: null,
    ha: null,
    hh: null,
    credito: "00:02",
    debito: null,
    saldo_no_mes: null,
    credito_acumulado: "-09:10",
    dnc: null,
  };

  const resumo: ResumoHorasApuradas = {
    carga_horaria_contratada: "160:00",
    carga_horaria_esperada_mes: "160:00",
    total_horas_registradas: "50:31",
    total_horas_justificadas: "00:00",
    total_horas_homologadas: "49:25",
    saldo_mes_anterior_compensacao: "00:00",
    total_horas_mes_anterior_compensadas: "00:00",
    debito_mes_anterior_nao_compensado: "00:00",
    debito_mes_atual_nao_autorizado: "-61:25",
    outros_debitos_nao_compensados_vencidos: "00:00",
    totalizacao_debito_nao_compensavel: "-61:25",
    total_horas_pendentes_compensacao: "-09:10",
    saldo_horas_mes: "-09:10",
    saldo_horas_mes_compensar_proximo: "-09:10",
    credito_horas_disponivel_mes: "00:00",
    credito_em_horas: "00:00",
  };

  it("uses total_horas_homologadas as somaCreditoMin when resumo non-null", () => {
    const result = aggregateMonth([baseRegistro], resumo);
    expect(result.somaCreditoMin).toBe(49 * 60 + 25); // 49:25 = 2965
  });

  it("uses saldo_horas_mes as balanceMin when resumo non-null", () => {
    const result = aggregateMonth([baseRegistro], resumo);
    expect(result.balanceMin).toBe(-(9 * 60 + 10)); // -09:10 = -550
  });

  it("uses carga_horaria_esperada_mes as cargaEsperadaMin when resumo non-null", () => {
    const result = aggregateMonth([baseRegistro], resumo);
    expect(result.cargaEsperadaMin).toBe(160 * 60); // 160:00 = 9600
  });

  it("uses fallback calculation when resumo is null", () => {
    const result = aggregateMonth([baseRegistro], null);
    // Falls back to calculated values (not resumo)
    expect(result.somaCreditoMin).toBe(2); // only "00:02" from registro
  });

  it("uses fallback calculation when resumo is absent (JSON v1 compat)", () => {
    const result = aggregateMonth([baseRegistro]);
    // No resumo arg → fallback
    expect(result.somaCreditoMin).toBe(2);
  });
});
