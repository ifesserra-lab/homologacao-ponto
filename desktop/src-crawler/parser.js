import { createRequire } from "module";

// ── helpers ──────────────────────────────────────────────────────────────────

const SIGRH_ROW_RE = /frequenciaForm:listagemPontos:\d+:/;

function normalizeLabel(text) {
  return text.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim().replace(/:$/, "");
}

const RESUMO_MAP = [
  ["carga horaria contratada", "carga_horaria_contratada"],
  ["carga horaria esperada", "carga_horaria_esperada_mes"],
  ["total de horas registradas", "total_horas_registradas"],
  ["total de horas justificadas", "total_horas_justificadas"],
  ["total de horas homologadas", "total_horas_homologadas"],
  ["para compensacao", "saldo_mes_anterior_compensacao"],
  ["compensadas", "total_horas_mes_anterior_compensadas"],
  ["compensado em", "debito_mes_anterior_nao_compensado"],
  ["nao autorizado", "debito_mes_atual_nao_autorizado"],
  ["outros debitos nao compensados vencidos", "outros_debitos_nao_compensados_vencidos"],
  ["totalizacao do debito nao compensavel", "totalizacao_debito_nao_compensavel"],
  ["total de horas pendentes de compensacao", "total_horas_pendentes_compensacao"],
  ["a compensar", "saldo_horas_mes_compensar_proximo"],
  ["saldo de horas de", "saldo_horas_mes"],
  ["credito de horas disponivel", "credito_horas_disponivel_mes"],
  ["credito em horas", "credito_em_horas"],
];

function matchResumoLabel(norm) {
  for (const [sub, field] of RESUMO_MAP) {
    if (norm.includes(sub)) return field;
  }
  return null;
}

// ── minimal HTML parser (no external dep) ────────────────────────────────────

function parseResumo(html) {
  const fields = {};
  // Find "Resumo das Horas Apuradas" table via caption
  const captionRe = /<caption[^>]*>([\s\S]*?)<\/caption>/gi;
  let cap;
  let resumoStart = -1;
  while ((cap = captionRe.exec(html)) !== null) {
    if (normalizeLabel(cap[1].replace(/<[^>]+>/g, "")).includes("resumo das horas apuradas")) {
      resumoStart = cap.index;
      break;
    }
  }
  if (resumoStart === -1) return null;

  // Extract rows from that table
  const tableSlice = html.slice(resumoStart);
  const endTable = tableSlice.indexOf("</table>");
  const slice = endTable > 0 ? tableSlice.slice(0, endTable) : tableSlice;
  const rowRe = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
  let row;
  while ((row = rowRe.exec(slice)) !== null) {
    const cells = [];
    const cellRe = /<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi;
    let cell;
    while ((cell = cellRe.exec(row[1])) !== null) {
      cells.push(cell[1].replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim());
    }
    if (cells.length >= 2) {
      const field = matchResumoLabel(normalizeLabel(cells[0]));
      if (field) fields[field] = cells[1] || null;
    }
  }
  if (Object.keys(fields).length === 0) return null;
  return {
    carga_horaria_contratada: null,
    carga_horaria_esperada_mes: null,
    total_horas_registradas: null,
    total_horas_justificadas: null,
    total_horas_homologadas: null,
    saldo_mes_anterior_compensacao: null,
    total_horas_mes_anterior_compensadas: null,
    debito_mes_anterior_nao_compensado: null,
    debito_mes_atual_nao_autorizado: null,
    outros_debitos_nao_compensados_vencidos: null,
    totalizacao_debito_nao_compensavel: null,
    total_horas_pendentes_compensacao: null,
    saldo_horas_mes: null,
    saldo_horas_mes_compensar_proximo: null,
    credito_horas_disponivel_mes: null,
    credito_em_horas: null,
    ...fields,
  };
}

function parseSigrhRow(cells) {
  // Find date cell
  let dateIdx = -1;
  for (let i = 0; i < cells.length; i++) {
    if (/\b\d{2}\/\d{2}\/\d{4}\b/.test(cells[i])) { dateIdx = i; break; }
  }
  if (dateIdx === -1) return null;
  const dateCell = cells[dateIdx];
  const dateMatch = dateCell.match(/\b(\d{2})\/(\d{2})\/(\d{4})\b/);
  if (!dateMatch) return null;
  const [, d, m, y] = dateMatch;
  const dayMatch = dateCell.match(/Dia da Semana:\s*(\w+)/i);
  const obsMatch = dateCell.match(/Observa[çc][aã]o:\s*(.+?)(?:\s*\/\/|$)/is);
  const timeCell = cells[dateIdx + 1] ?? "";
  const occCell = cells.find(c => /Ocorrên[çc]ia:|Ocorrencia:/i.test(c)) ?? "";
  const occMatch = occCell.match(/Ocorrên[çc]ia:\s*(.*?)(?=\s*Situa[çc][aã]o:|$)/is);

  const cv = (off) => {
    const v = (cells[dateIdx + off] ?? "").split(/\s/)[0] ?? "";
    return v && v !== "---" ? v : null;
  };

  return {
    data: `${y}-${m}-${d}`,
    dia_semana: dayMatch?.[1] ?? null,
    marcacoes: timeCell && timeCell !== "---" ? [timeCell] : [],
    ocorrencias: occMatch ? [occMatch[1].trim()] : [],
    observacoes: obsMatch ? [obsMatch[1].trim()] : [],
    situacao: null,
    hr: cv(2), hc: cv(3), he: cv(4), ha: cv(5), hh: cv(6),
    credito: cv(7), debito: cv(8), saldo_no_mes: cv(9),
    credito_acumulado: cv(10), dnc: cv(11),
  };
}

function extractRows(html) {
  const rows = [];
  const rowRe = /<tr([^>]*)>([\s\S]*?)<\/tr>/gi;
  let m;
  while ((m = rowRe.exec(html)) !== null) {
    const attrs = m[1];
    const inner = m[2];
    const idMatch = attrs.match(/id="([^"]+)"/);
    if (idMatch && SIGRH_ROW_RE.test(idMatch[1])) {
      const cells = [];
      const cellRe = /<td[^>]*>([\s\S]*?)<\/td>/gi;
      let c;
      while ((c = cellRe.exec(inner)) !== null) {
        cells.push(c[1].replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim());
      }
      const row = parseSigrhRow(cells);
      if (row) rows.push(row);
    }
  }
  return rows;
}

function extractTexts(html) {
  return html.replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function extractPeriod(text) {
  const m = text.match(/Per[ií]odo\s*:\s*([A-Za-zçÇéÉíÍóÓúÚãÃõÕ]+\/\d{4})/i);
  if (m) return m[1];
  const m2 = text.match(/Espelho de Ponto\s*[-–]\s*([A-Za-zçÇéÉíÍóÓúÚãÃõÕ]+)\s+de\s+(\d{4})/i);
  if (m2) return `${m2[1].charAt(0).toUpperCase() + m2[1].slice(1)}/${m2[2]}`;
  return null;
}

function extractIdentifier(text) {
  const m = text.match(/(?:SIAPE|Matr[ií]cula)\s*:?\s*(\d{5,})/i);
  return m?.[1] ?? null;
}

function normalizeServerName(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
}

// ── public API ────────────────────────────────────────────────────────────────

export function parseEspelho({ html, url, capturedAt, runId, serverName, identifier = null }) {
  const visibleText = extractTexts(html);
  const normText = normalizeServerName(visibleText);

  if (!normText.includes("espelho") || !normText.includes("ponto")) {
    throw new Error("Página não é um Espelho de Ponto");
  }
  if (!normText.includes(normalizeServerName(serverName)) && !(identifier && visibleText.includes(identifier))) {
    throw new Error(`Servidor "${serverName}" não identificado na página`);
  }

  const periodo = extractPeriod(visibleText);
  const foundId = extractIdentifier(visibleText) ?? identifier;
  const registros = extractRows(html);
  const resumo = parseResumo(html);

  const pagina = (() => { try { return new URL(url).pathname; } catch { return url; } })();

  const servidor = {
    nome: serverName.toUpperCase(),
    identificador: foundId,
    texto_visivel: null,
  };

  if (!registros.length) {
    return {
      schema_version: 2,
      run_id: runId,
      captured_at: capturedAt,
      status: "empty",
      servidor,
      periodo_referencia: periodo,
      mensagens: ["Espelho sem registros"],
      resumo: null,
      registros: [],
      fonte: { tipo: "sigrh-espelho-ponto-visivel", pagina, rotulos_visiveis: ["Espelho de Ponto"] },
    };
  }

  return {
    schema_version: 2,
    run_id: runId,
    captured_at: capturedAt,
    status: "completed",
    servidor,
    periodo_referencia: periodo,
    mensagens: [],
    resumo,
    registros,
    fonte: { tipo: "sigrh-espelho-ponto-visivel", pagina, rotulos_visiveis: ["Espelho de Ponto"] },
  };
}
