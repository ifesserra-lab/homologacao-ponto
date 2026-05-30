import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdirSync, writeFileSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { scanLiberados } from "./homologar.js";

// ── Fixtures ──────────────────────────────────────────────────────────────────

function slugify(name) {
  return name
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function writeEspelho(outputDir, nome, periodoReferencia, data) {
  const slug = slugify(nome);
  const slugPath = join(outputDir, "servidores", slug);
  mkdirSync(slugPath, { recursive: true });
  const filename = `espelho-${periodoReferencia.replace("/", "-").toLowerCase()}.json`;
  writeFileSync(join(slugPath, filename), JSON.stringify({ periodo_referencia: periodoReferencia, ...data }));
}

// Espelho mínimo limpo — sem pendências, sem HE
function espelhoLimpo(nome, periodoReferencia) {
  return {
    status: "completed",
    servidor: { nome },
    registros: [
      { data: "2025-03-10", dia_semana: "Segunda", situacao: "Homologado", marcacoes: ["07:58", "12:00", "13:00", "17:03"], ocorrencias: [], he: null, ha: null },
      { data: "2025-03-11", dia_semana: "Terça",   situacao: "Homologado", marcacoes: ["07:55", "12:00", "13:00", "17:00"], ocorrencias: [], he: null, ha: null },
    ],
    resumo: { debito_mes_atual_nao_autorizado: "00:00", saldo_horas_mes: "00:00" },
  };
}

// Espelho com HE sem HA
function espelhoComHE(nome, periodoReferencia) {
  return {
    status: "completed",
    servidor: { nome },
    registros: [
      { data: "2025-03-10", dia_semana: "Segunda", situacao: "Homologado", marcacoes: ["07:58", "12:00", "13:00", "18:30"], ocorrencias: [], he: "01:30", ha: null },
    ],
    resumo: { debito_mes_atual_nao_autorizado: "00:00", saldo_horas_mes: "00:00" },
  };
}

// Espelho com HE e HA preenchidos (HE autorizado)
function espelhoHEAutorizado(nome, periodoReferencia) {
  return {
    status: "completed",
    servidor: { nome },
    registros: [
      { data: "2025-03-10", dia_semana: "Segunda", situacao: "Homologado", marcacoes: ["07:58", "12:00", "13:00", "18:30"], ocorrencias: [], he: "01:30", ha: "01:30" },
    ],
    resumo: { debito_mes_atual_nao_autorizado: "00:00", saldo_horas_mes: "00:00" },
  };
}

// Espelho com situação Pendente (AX-006)
function espelhoComPendente(nome, periodoReferencia) {
  return {
    status: "completed",
    servidor: { nome },
    registros: [
      { data: "2025-03-10", dia_semana: "Segunda", situacao: "Pendente", marcacoes: [], ocorrencias: ["ABONO DE HORAS"], he: null, ha: null },
      { data: "2025-03-11", dia_semana: "Terça",   situacao: "Homologado", marcacoes: ["07:55", "12:00", "13:00", "17:00"], ocorrencias: [], he: null, ha: null },
    ],
    resumo: { debito_mes_atual_nao_autorizado: "00:00", saldo_horas_mes: "00:00" },
  };
}

// Espelho com marcações ímpares sem ocorrência em dia útil (AX-003)
function espelhoMarcacoesImpar(nome, periodoReferencia) {
  return {
    status: "completed",
    servidor: { nome },
    registros: [
      // 2025-03-10 é Segunda (dia útil)
      { data: "2025-03-10", dia_semana: "Segunda", situacao: null, marcacoes: ["07:58", "12:00", "13:00"], ocorrencias: [], he: null, ha: null },
    ],
    resumo: { debito_mes_atual_nao_autorizado: "00:00", saldo_horas_mes: "00:00" },
  };
}

// Espelho com débito não autorizado no resumo (AX-007)
function espelhoComDebito(nome, periodoReferencia) {
  return {
    status: "completed",
    servidor: { nome },
    registros: [
      { data: "2025-03-10", dia_semana: "Segunda", situacao: "Homologado", marcacoes: ["07:58", "17:00"], ocorrencias: [], he: null, ha: null },
    ],
    resumo: { debito_mes_atual_nao_autorizado: "-02:00", saldo_horas_mes: "-02:00" },
  };
}

// Espelho vazio
function espelhoVazio(nome, periodoReferencia) {
  return { status: "empty", servidor: { nome }, registros: [], resumo: null };
}

// Espelho com período do mês atual (deve ser ignorado)
function espelhoMesAtual(nome) {
  const now = new Date();
  const meses = ["", "janeiro","fevereiro","março","abril","maio","junho",
                  "julho","agosto","setembro","outubro","novembro","dezembro"];
  const periodo = `${meses[now.getMonth() + 1]}/${now.getFullYear()}`;
  return {
    periodo_referencia: periodo,
    status: "completed",
    servidor: { nome },
    registros: [{ data: `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-05`, dia_semana: "Segunda", situacao: "Homologado", marcacoes: [], ocorrencias: [], he: null, ha: null }],
    resumo: { debito_mes_atual_nao_autorizado: "00:00", saldo_horas_mes: "00:00" },
  };
}

// ── Setup ─────────────────────────────────────────────────────────────────────

let tmpDir;
beforeEach(() => {
  tmpDir = join(tmpdir(), `homologar-test-${Date.now()}`);
  mkdirSync(tmpDir, { recursive: true });
});
afterEach(() => {
  rmSync(tmpDir, { recursive: true, force: true });
});

// ── politica_he = "manual" (padrão) ──────────────────────────────────────────

describe("scanLiberados — politica_he manual", () => {
  it("retorna espelho limpo como liberado", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoLimpo(nome, periodo));
    const result = scanLiberados(tmpDir, "manual");
    expect(result.length).toBe(1);
    expect(result[0].nome).toBe("Ana Lima");
    expect(result[0].periodoReferencia).toBe(periodo);
  });

  it("bloqueia espelho com HE sem HA (AX-007)", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoComHE(nome, periodo));
    const result = scanLiberados(tmpDir, "manual");
    expect(result.length).toBe(0);
  });

  it("libera espelho com HE quando HA preenchido", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoHEAutorizado(nome, periodo));
    const result = scanLiberados(tmpDir, "manual");
    expect(result.length).toBe(1);
  });

  it("bloqueia espelho com situacao Pendente (AX-006)", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoComPendente(nome, periodo));
    const result = scanLiberados(tmpDir, "manual");
    expect(result.length).toBe(0);
  });

  it("bloqueia espelho com marcações ímpares sem ocorrência em dia útil (AX-003)", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoMarcacoesImpar(nome, periodo));
    const result = scanLiberados(tmpDir, "manual");
    expect(result.length).toBe(0);
  });

  it("bloqueia espelho com débito não autorizado no resumo", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoComDebito(nome, periodo));
    const result = scanLiberados(tmpDir, "manual");
    expect(result.length).toBe(0);
  });

  it("ignora espelho vazio", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoVazio(nome, periodo));
    const result = scanLiberados(tmpDir, "manual");
    expect(result.length).toBe(0);
  });

  it("ignora espelho do mês atual", () => {
    const nome = "Ana Lima";
    const data = espelhoMesAtual(nome);
    const slug = slugify(nome);
    const slugPath = join(tmpDir, "servidores", slug);
    mkdirSync(slugPath, { recursive: true });
    writeFileSync(join(slugPath, "espelho-mes-atual.json"), JSON.stringify(data));
    const result = scanLiberados(tmpDir, "manual");
    expect(result.length).toBe(0);
  });
});

// ── politica_he = "autorizar" ─────────────────────────────────────────────────

describe("scanLiberados — politica_he autorizar", () => {
  it("libera espelho com HE sem HA (HE não bloqueia)", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoComHE(nome, periodo));
    const result = scanLiberados(tmpDir, "autorizar");
    expect(result.length).toBe(1);
    expect(result[0].politicaHe).toBe("autorizar");
  });

  it("popula heEntries com dias que têm HE > 0", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoComHE(nome, periodo));
    const result = scanLiberados(tmpDir, "autorizar");
    expect(result[0].heEntries.length).toBe(1);
    expect(result[0].heEntries[0].he).toBe("01:30");
  });

  it("heEntries vazio quando espelho não tem HE", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoLimpo(nome, periodo));
    const result = scanLiberados(tmpDir, "autorizar");
    expect(result[0].heEntries.length).toBe(0);
  });

  it("ainda bloqueia por dias_pendentes mesmo com politica_he autorizar (AX-006)", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoComPendente(nome, periodo));
    const result = scanLiberados(tmpDir, "autorizar");
    expect(result.length).toBe(0);
  });
});

// ── politica_he = "zerar" (configuração do projeto) ──────────────────────────

describe("scanLiberados — politica_he zerar (configuração atual)", () => {
  it("libera espelho com HE sem HA (HE não bloqueia)", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoComHE(nome, periodo));
    const result = scanLiberados(tmpDir, "zerar");
    expect(result.length).toBe(1);
    expect(result[0].politicaHe).toBe("zerar");
  });

  it("popula heEntries mesmo com politica_he zerar", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoComHE(nome, periodo));
    const result = scanLiberados(tmpDir, "zerar");
    expect(result[0].heEntries.length).toBe(1);
  });

  it("ainda bloqueia por dias_pendentes (AX-006)", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoComPendente(nome, periodo));
    const result = scanLiberados(tmpDir, "zerar");
    expect(result.length).toBe(0);
  });

  it("ainda bloqueia por débito não autorizado", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoComDebito(nome, periodo));
    const result = scanLiberados(tmpDir, "zerar");
    expect(result.length).toBe(0);
  });

  // HE + Pendente no mesmo espelho: pendente vence
  it("bloqueia quando HE e Pendente combinados", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    const data = {
      status: "completed",
      servidor: { nome },
      registros: [
        { data: "2025-03-10", dia_semana: "Segunda", situacao: "Pendente", marcacoes: [], ocorrencias: [], he: "01:00", ha: null },
      ],
      resumo: { debito_mes_atual_nao_autorizado: "00:00", saldo_horas_mes: "00:00" },
    };
    writeEspelho(tmpDir, nome, periodo, data);
    const result = scanLiberados(tmpDir, "zerar");
    expect(result.length).toBe(0);
  });
});

// ── Múltiplos servidores e slugFilter ─────────────────────────────────────────

describe("scanLiberados — múltiplos servidores", () => {
  it("retorna múltiplos servidores liberados", () => {
    const periodo = "março/2025";
    writeEspelho(tmpDir, "Ana Lima", periodo, espelhoLimpo("Ana Lima", periodo));
    writeEspelho(tmpDir, "Carlos Souza", periodo, espelhoLimpo("Carlos Souza", periodo));
    const result = scanLiberados(tmpDir, "manual");
    expect(result.length).toBe(2);
  });

  it("filtra por slugFilter — inclui apenas slugs passados", () => {
    const periodo = "março/2025";
    writeEspelho(tmpDir, "Ana Lima", periodo, espelhoLimpo("Ana Lima", periodo));
    writeEspelho(tmpDir, "Carlos Souza", periodo, espelhoLimpo("Carlos Souza", periodo));
    const result = scanLiberados(tmpDir, "manual", ["ana-lima"]);
    expect(result.length).toBe(1);
    expect(result[0].slug).toBe("ana-lima");
  });

  it("filtra por slugFilter — exclui slug não listado", () => {
    const periodo = "março/2025";
    writeEspelho(tmpDir, "Ana Lima", periodo, espelhoLimpo("Ana Lima", periodo));
    writeEspelho(tmpDir, "Carlos Souza", periodo, espelhoComHE("Carlos Souza", periodo));
    const result = scanLiberados(tmpDir, "manual", ["ana-lima"]);
    expect(result.length).toBe(1);
  });

  it("ordena por nome em pt-BR", () => {
    const periodo = "março/2025";
    writeEspelho(tmpDir, "Zé Silva", periodo, espelhoLimpo("Zé Silva", periodo));
    writeEspelho(tmpDir, "Ana Lima", periodo, espelhoLimpo("Ana Lima", periodo));
    const result = scanLiberados(tmpDir, "manual");
    expect(result[0].slug).toBe("ana-lima");
    expect(result[1].slug).toBe("ze-silva");
  });

  it("ordena por período quando mesmo servidor tem múltiplos meses", () => {
    writeEspelho(tmpDir, "Ana Lima", "março/2025", espelhoLimpo("Ana Lima", "março/2025"));
    writeEspelho(tmpDir, "Ana Lima", "janeiro/2025", espelhoLimpo("Ana Lima", "janeiro/2025"));
    writeEspelho(tmpDir, "Ana Lima", "fevereiro/2025", espelhoLimpo("Ana Lima", "fevereiro/2025"));
    const result = scanLiberados(tmpDir, "manual");
    expect(result[0].periodoReferencia).toBe("janeiro/2025");
    expect(result[1].periodoReferencia).toBe("fevereiro/2025");
    expect(result[2].periodoReferencia).toBe("março/2025");
  });

  it("retorna vazio quando outputDir não tem pasta servidores", () => {
    const result = scanLiberados(tmpDir, "manual");
    expect(result).toEqual([]);
  });
});

// ── PIT Docente (AX-005): marcacoes vazio com ocorrência não bloqueia ─────────

describe("scanLiberados — PIT Docente (AX-005)", () => {
  it("libera dia com PIT docente e marcacoes vazio", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    const data = {
      status: "completed",
      servidor: { nome },
      registros: [
        {
          data: "2025-03-10",
          dia_semana: "Segunda",
          situacao: "Homologado",
          marcacoes: [],
          ocorrencias: ["REGISTRO DO PIT - DOCENTE (10/03/2025)"],
          he: null,
          ha: null,
        },
      ],
      resumo: { debito_mes_atual_nao_autorizado: "00:00", saldo_horas_mes: "00:00" },
    };
    writeEspelho(tmpDir, nome, periodo, data);
    const result = scanLiberados(tmpDir, "manual");
    expect(result.length).toBe(1);
  });
});

// ── Campos de saída (entry shape) ────────────────────────────────────────────

describe("scanLiberados — shape da entrada retornada", () => {
  it("entry contém campos esperados", () => {
    const nome = "Ana Lima";
    const periodo = "março/2025";
    writeEspelho(tmpDir, nome, periodo, espelhoLimpo(nome, periodo));
    const [entry] = scanLiberados(tmpDir, "manual");
    expect(entry).toMatchObject({
      slug: "ana-lima",
      periodoReferencia: periodo,
      mes: 3,
      ano: 2025,
      politicaHe: "manual",
      heEntries: expect.any(Array),
    });
  });
});
