import { describe, it, expect } from "vitest";
import { dedupRegistros } from "./dedupRegistros";

describe("dedupRegistros", () => {
  it("returns empty for empty input", () => {
    expect(dedupRegistros([])).toEqual([]);
  });

  it("keeps distinct dates separate", () => {
    const input = [
      { data: "2025-05-02", ocorrencias: [], marcacoes: [], credito: "08:00" },
      { data: "2025-05-05", ocorrencias: [], marcacoes: [], credito: "08:00" },
    ];
    expect(dedupRegistros(input)).toHaveLength(2);
  });

  it("merges duplicate dates into one row", () => {
    const input = [
      { data: "2025-05-07", ocorrencias: ["LIC. PATERNIDADE"], marcacoes: [], credito: null },
      { data: "2025-05-07", ocorrencias: ["LIC. PATERNIDADE"], marcacoes: [], credito: "00:00" },
      { data: "2025-05-07", ocorrencias: ["LIC. PATERNIDADE"], marcacoes: [], credito: null },
    ];
    const result = dedupRegistros(input);
    expect(result).toHaveLength(1);
    expect(result[0].credito).toBe("00:00");
  });

  it("unions ocorrencias across duplicates without duplicating entries", () => {
    const input = [
      { data: "2025-05-07", ocorrencias: ["LIC. PATERNIDADE", "EXTRA"], marcacoes: [] },
      { data: "2025-05-07", ocorrencias: ["LIC. PATERNIDADE"], marcacoes: [] },
    ];
    const result = dedupRegistros(input);
    expect(result[0].ocorrencias).toEqual(["LIC. PATERNIDADE", "EXTRA"]);
  });

  it("unions marcacoes across duplicates", () => {
    const input = [
      { data: "2025-05-07", ocorrencias: [], marcacoes: ["08:00", "17:00"] },
      { data: "2025-05-07", ocorrencias: [], marcacoes: ["08:00", "17:00"] },
    ];
    const result = dedupRegistros(input);
    expect(result[0].marcacoes).toEqual(["08:00", "17:00"]);
  });

  it("takes first non-null scalar value", () => {
    const input = [
      { data: "2025-05-07", ocorrencias: [], marcacoes: [], situacao: null },
      { data: "2025-05-07", ocorrencias: [], marcacoes: [], situacao: "Homologado" },
    ];
    const result = dedupRegistros(input);
    expect(result[0].situacao).toBe("Homologado");
  });

  it("does not overwrite existing non-null scalar with later value", () => {
    const input = [
      { data: "2025-05-07", ocorrencias: [], marcacoes: [], situacao: "Pendente" },
      { data: "2025-05-07", ocorrencias: [], marcacoes: [], situacao: "Homologado" },
    ];
    const result = dedupRegistros(input);
    expect(result[0].situacao).toBe("Pendente");
  });

  it("handles rows without data field (uses dia_semana as key)", () => {
    const input = [
      { dia_semana: "Seg", data: undefined, ocorrencias: ["X"], marcacoes: [] },
      { dia_semana: "Seg", data: undefined, ocorrencias: ["X"], marcacoes: [] },
    ];
    const result = dedupRegistros(input);
    expect(result).toHaveLength(1);
    expect(result[0].ocorrencias).toEqual(["X"]);
  });
});
