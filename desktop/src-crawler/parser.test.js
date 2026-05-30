import { describe, it, expect } from "vitest";
import { parseEspelho } from "./parser.js";

// ── Helpers ───────────────────────────────────────────────────────────────────

const SERVIDOR = "CELIO PROLICIANO MAIOLI";
const RUN_ID = "abc123";
const CAPTURED_AT = "2026-03-01T00:00:00Z";
const URL = "https://sigrh.ifes.edu.br/sigrh/frequencia/ponto_eletronico/espelho.jsf";

// Build minimal SIGRH espelho HTML with one row
function buildHtml({ heCell = "", haCell = "", timeCell = "", occCell = "", situacaoCell = "" } = {}) {
  const row = `
    <tr id="frequenciaForm:listagemPontos:0:coluna">
      <td>10/03/2026 Dia da Semana: Segunda</td>
      <td>${timeCell}</td>
      <td>08:00</td>
      <td>08:00</td>
      <td>${heCell}</td>
      <td>${haCell}</td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td>${occCell}</td>
      <td>${situacaoCell}</td>
    </tr>`;

  return `
    <html><body>
      <h2>Espelho de Ponto - Março de 2026</h2>
      <p>SIAPE: 1534589</p>
      <p>${SERVIDOR}</p>
      <p>Período : Março/2026</p>
      <table>
        <caption>Espelho de Ponto</caption>
        ${row}
      </table>
    </body></html>`;
}

function parse(opts) {
  return parseEspelho({
    html: buildHtml(opts),
    url: URL,
    capturedAt: CAPTURED_AT,
    runId: RUN_ID,
    serverName: SERVIDOR,
  });
}

// ── HE/HA extração ────────────────────────────────────────────────────────────

describe("parser — HE/HA com sufixo de label (bug antigo)", () => {
  it("extrai HH:MM de '08:00Horas' (sufixo concatenado)", () => {
    const esp = parse({ heCell: "08:00Horas" });
    expect(esp.registros[0].he).toBe("08:00");
  });

  it("extrai HH:MM de '04:02Total' (sufixo Total)", () => {
    const esp = parse({ heCell: "04:02Total" });
    expect(esp.registros[0].he).toBe("04:02");
  });

  it("extrai HH:MM de '01:50Horas' (valor não inteiro de hora)", () => {
    const esp = parse({ heCell: "01:50Horas" });
    expect(esp.registros[0].he).toBe("01:50");
  });

  it("retorna null para célula 'Ocorrência:' (sem HH:MM)", () => {
    const esp = parse({ heCell: "Ocorrência:" });
    expect(esp.registros[0].he).toBeNull();
  });

  it("retorna null para célula de data '17/03/2026Dia' bleeding em HA", () => {
    // Valor de HA incorretamente populado com data de célula adjacente
    const esp = parse({ haCell: "17/03/2026Dia" });
    expect(esp.registros[0].ha).toBeNull();
  });

  it("extrai HA de '02:00//' (valor com sufixo //)", () => {
    const esp = parse({ haCell: "02:00//" });
    expect(esp.registros[0].ha).toBe("02:00");
  });

  it("HE limpo '08:00' sem sufixo: continua funcionando", () => {
    const esp = parse({ heCell: "08:00" });
    expect(esp.registros[0].he).toBe("08:00");
  });

  it("HE '00:00' retorna '00:00'", () => {
    const esp = parse({ heCell: "00:00" });
    expect(esp.registros[0].he).toBe("00:00");
  });

  it("HE '---' retorna null", () => {
    const esp = parse({ heCell: "---" });
    expect(esp.registros[0].he).toBeNull();
  });

  it("HE vazio retorna null", () => {
    const esp = parse({ heCell: "" });
    expect(esp.registros[0].he).toBeNull();
  });
});

// ── Marcações: split de múltiplos horários ────────────────────────────────────

describe("parser — marcações split (múltiplos horários por célula)", () => {
  it("célula com 4 horários → array de 4 elementos", () => {
    const esp = parse({ timeCell: "07:58 12:00 13:00 17:03" });
    expect(esp.registros[0].marcacoes).toEqual(["07:58", "12:00", "13:00", "17:03"]);
  });

  it("célula com 2 horários → array de 2 elementos", () => {
    const esp = parse({ timeCell: "08:00 17:00" });
    expect(esp.registros[0].marcacoes).toEqual(["08:00", "17:00"]);
  });

  it("célula com 1 horário → array de 1 elemento", () => {
    const esp = parse({ timeCell: "08:00" });
    expect(esp.registros[0].marcacoes).toEqual(["08:00"]);
  });

  it("célula '---' → array vazio", () => {
    const esp = parse({ timeCell: "---" });
    expect(esp.registros[0].marcacoes).toEqual([]);
  });

  it("célula vazia → array vazio", () => {
    const esp = parse({ timeCell: "" });
    expect(esp.registros[0].marcacoes).toEqual([]);
  });
});

// ── Campos raiz e servidor ────────────────────────────────────────────────────

describe("parser — campos raiz", () => {
  it("periodo_referencia extraído do HTML", () => {
    const esp = parse();
    expect(esp.periodo_referencia).toBe("Março/2026");
  });

  it("servidor.nome em maiúsculas", () => {
    const esp = parse();
    expect(esp.servidor.nome).toBe(SERVIDOR);
  });

  it("servidor.identificador extraído do SIAPE", () => {
    const esp = parse();
    expect(esp.servidor.identificador).toBe("1534589");
  });

  it("status completed quando há registros", () => {
    const esp = parse();
    expect(esp.status).toBe("completed");
  });

  it("schema_version = 2", () => {
    expect(parse().schema_version).toBe(2);
  });
});

// ── PIT Docente: HE = "08:00Horas" com ocorrência ────────────────────────────

describe("parser — PIT Docente (HE + ocorrência)", () => {
  it("dia PIT: he='08:00Horas' → he='08:00', ocorrencia extraída", () => {
    const esp = parse({
      heCell: "08:00Horas",
      timeCell: "08:00",
      occCell: "Ocorrência: REGISTRO DO PIT - DOCENTE (10/03/2026)",
    });
    const reg = esp.registros[0];
    expect(reg.he).toBe("08:00");
    expect(reg.ocorrencias[0]).toBe("REGISTRO DO PIT - DOCENTE (10/03/2026)");
  });

  it("após fix: he='08:00' é parseável por parseHHMM (sem sufixo)", () => {
    const esp = parse({ heCell: "08:00Horas" });
    const he = esp.registros[0].he;
    // Verify parseHHMM can now parse the extracted value
    const m = he?.match(/^(\d+):(\d{2})$/);
    expect(m).not.toBeNull();
    expect(parseInt(m[1]) * 60 + parseInt(m[2])).toBe(480); // 8h = 480min
  });
});
