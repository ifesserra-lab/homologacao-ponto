import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdirSync, writeFileSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { listServers, serverDetail } from "../lib/espelhoRepository";

function makeEspelho(override: Record<string, unknown> = {}) {
  return {
    schema_version: 1,
    run_id: "run-001",
    captured_at: "2026-03-01T00:00:00+00:00",
    status: "completed",
    periodo_referencia: "Março/2026",
    mensagens: [],
    servidor: { nome: "CELIO PROLICIANO MAIOLI", identificador: "1234", texto_visivel: null },
    registros: [
      {
        data: "2026-03-10",
        dia_semana: "Terça",
        marcacoes: ["08:00", "17:00"],
        ocorrencias: [],
        observacoes: [],
        situacao: "Homologado",
        textos_visiveis: [],
        hr: "08:00",
        hc: "08:00",
        he: null,
        ha: null,
        hh: "08:00",
        credito: "00:00",
        debito: null,
        saldo_no_mes: "00:00",
        credito_acumulado: "00:00",
        dnc: "00:00",
      },
    ],
    fonte: { tipo: "sigrh-espelho-ponto-visivel", pagina: null, rotulos_visiveis: [] },
    ...override,
  };
}

let tmpDir: string;

beforeEach(() => {
  tmpDir = join(tmpdir(), `repo-test-${Date.now()}`);
  mkdirSync(tmpDir, { recursive: true });
});

afterEach(() => {
  rmSync(tmpDir, { recursive: true, force: true });
});

describe("listServers", () => {
  it("returns empty list when servidores dir does not exist", () => {
    const result = listServers(join(tmpDir, "nonexistent"));
    expect(result).toEqual([]);
  });

  it("returns empty list when servidores dir is empty", () => {
    const result = listServers(tmpDir);
    expect(result).toEqual([]);
  });

  it("returns one ServidorResume per server subfolder", () => {
    const slug = "celio-proliciano-maioli";
    const serverDir = join(tmpDir, slug);
    mkdirSync(serverDir, { recursive: true });
    writeFileSync(join(serverDir, "espelho-marco-2026.json"), JSON.stringify(makeEspelho()));

    const result = listServers(tmpDir);
    expect(result).toHaveLength(1);
    expect(result[0].slug).toBe(slug);
    expect(result[0].nome).toBe("CELIO PROLICIANO MAIOLI");
    expect(result[0].siape).toBe("1234");
    expect(result[0].totalMeses).toBe(1);
  });

  it("skips corrupted JSON files without throwing", () => {
    const serverDir = join(tmpDir, "bad-server");
    mkdirSync(serverDir, { recursive: true });
    writeFileSync(join(serverDir, "espelho-bad.json"), "{ invalid json");

    const result = listServers(tmpDir);
    expect(result).toHaveLength(1);
    expect(result[0].totalMeses).toBe(0);
  });

  it("keeps only most recent file when same periodo_referencia appears twice", () => {
    const serverDir = join(tmpDir, "celio-proliciano-maioli");
    mkdirSync(serverDir, { recursive: true });
    const older = makeEspelho({ run_id: "old", captured_at: "2026-03-01T10:00:00+00:00" });
    const newer = makeEspelho({ run_id: "new", captured_at: "2026-03-02T10:00:00+00:00" });
    writeFileSync(join(serverDir, "espelho-marco-v1.json"), JSON.stringify(older));
    writeFileSync(join(serverDir, "espelho-marco-v2.json"), JSON.stringify(newer));

    const result = listServers(tmpDir);
    expect(result[0].totalMeses).toBe(1);
    expect(result[0].meses[0].capturedAt).toBe("2026-03-02T10:00:00+00:00");
  });
});

describe("serverDetail", () => {
  it("returns undefined for unknown slug", () => {
    const result = serverDetail("unknown-slug", tmpDir);
    expect(result).toBeUndefined();
  });

  it("returns ServidorResume for known slug", () => {
    const slug = "celio-proliciano-maioli";
    const serverDir = join(tmpDir, slug);
    mkdirSync(serverDir, { recursive: true });
    writeFileSync(join(serverDir, "espelho-marco-2026.json"), JSON.stringify(makeEspelho()));

    const result = serverDetail(slug, tmpDir);
    expect(result).toBeDefined();
    expect(result!.slug).toBe(slug);
    expect(result!.meses).toHaveLength(1);
  });

  it("status indicator is com-vazios when any month is empty", () => {
    const slug = "celio-proliciano-maioli";
    const serverDir = join(tmpDir, slug);
    mkdirSync(serverDir, { recursive: true });
    writeFileSync(join(serverDir, "espelho-jan.json"), JSON.stringify(makeEspelho({ periodo_referencia: "Janeiro/2026" })));
    writeFileSync(
      join(serverDir, "espelho-fev.json"),
      JSON.stringify(makeEspelho({ status: "empty", periodo_referencia: "Fevereiro/2026", registros: [] }))
    );

    const result = serverDetail(slug, tmpDir)!;
    expect(result.statusIndicator).toBe("com-vazios");
  });

  it("status indicator is completo when all months completed", () => {
    const slug = "celio-proliciano-maioli";
    const serverDir = join(tmpDir, slug);
    mkdirSync(serverDir, { recursive: true });
    writeFileSync(join(serverDir, "espelho-jan.json"), JSON.stringify(makeEspelho({ periodo_referencia: "Janeiro/2026" })));
    writeFileSync(join(serverDir, "espelho-fev.json"), JSON.stringify(makeEspelho({ run_id: "run-2", periodo_referencia: "Fevereiro/2026" })));

    const result = serverDetail(slug, tmpDir)!;
    expect(result.statusIndicator).toBe("completo");
  });

  it("periodoRange shows single period when only one month", () => {
    const slug = "celio-proliciano-maioli";
    const serverDir = join(tmpDir, slug);
    mkdirSync(serverDir, { recursive: true });
    writeFileSync(join(serverDir, "espelho-jan.json"), JSON.stringify(makeEspelho({ periodo_referencia: "Janeiro/2026" })));

    const result = serverDetail(slug, tmpDir)!;
    expect(result.periodoRange).toBe("Janeiro/2026");
  });
});
