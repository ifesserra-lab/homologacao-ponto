import type { RawEspelho, RegistroDia } from "@/types/dashboard";
import { parseHHMM } from "@/lib/aggregation";
import { dedupRegistros } from "@/lib/dedupRegistros";

export type HomologacaoStatus = "liberado" | "bloqueado" | "mes_atual" | "vazio";

export type RazaoBloqueio =
  | "dias_pendentes"
  | "he_nao_autorizado"
  | "debito_nao_autorizado"
  | "marcacoes_incompletas";

export interface DiaProblema {
  data: string;
  dataFormatada: string;
  diaSemana: string | null;
  razoes: { tipo: RazaoBloqueio; detalhe: string }[];
}

export interface HomologacaoResult {
  status: HomologacaoStatus;
  razoes: RazaoBloqueio[];
  diasProblema: DiaProblema[];
  debitoNaoAutorizado: string | null;
}

const MONTH_MAP: Record<string, number> = {
  janeiro: 1, fevereiro: 2, março: 3, abril: 4, maio: 5, junho: 6,
  julho: 7, agosto: 8, setembro: 9, outubro: 10, novembro: 11, dezembro: 12,
};

export function periodoToDate(periodo: string): Date {
  const [m, y] = periodo.toLowerCase().split("/");
  return new Date(parseInt(y, 10), (MONTH_MAP[m.trim()] ?? 1) - 1, 1);
}

function formatData(data: string): string {
  const p = data.split("-");
  return p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : data;
}

function isCurrentMonth(periodoReferencia: string | null): boolean {
  if (!periodoReferencia) return false;
  const now = new Date();
  const d = periodoToDate(periodoReferencia);
  return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
}

export function checkHomologavel(raw: RawEspelho): HomologacaoResult {
  if (raw.status === "empty") {
    return { status: "vazio", razoes: [], diasProblema: [], debitoNaoAutorizado: null };
  }
  if (isCurrentMonth(raw.periodo_referencia)) {
    return { status: "mes_atual", razoes: [], diasProblema: [], debitoNaoAutorizado: null };
  }

  const registros = dedupRegistros(raw.registros) as RegistroDia[];
  const razoes = new Set<RazaoBloqueio>();
  const diasMap = new Map<string, DiaProblema>();

  function getDia(r: RegistroDia): DiaProblema {
    if (!diasMap.has(r.data)) {
      diasMap.set(r.data, {
        data: r.data,
        dataFormatada: formatData(r.data),
        diaSemana: r.dia_semana,
        razoes: [],
      });
    }
    return diasMap.get(r.data)!;
  }

  for (const r of registros) {
    // AX-006: situação pendente → ocorrência não homologada
    if (r.situacao === "Pendente") {
      razoes.add("dias_pendentes");
      getDia(r).razoes.push({
        tipo: "dias_pendentes",
        detalhe: "Situação Pendente — verifique se há ocorrência ou ausência em aberto no SIGRH",
      });
    }

    // AX-007: horas excedentes sem autorização
    const he = parseHHMM(r.he);
    const ha = parseHHMM(r.ha);
    if (he !== null && he > 0 && (ha === null || ha === 0)) {
      razoes.add("he_nao_autorizado");
      getDia(r).razoes.push({
        tipo: "he_nao_autorizado",
        detalhe: `Horas excedentes ${r.he} não autorizadas pela chefia`,
      });
    }

    // AX-003: marcações ímpares em dia útil sem ocorrência (possível batida faltando)
    if (
      r.marcacoes.length > 0 &&
      r.marcacoes.length % 2 !== 0 &&
      r.ocorrencias.length === 0 &&
      r.situacao !== "Homologado"
    ) {
      const dow = r.data ? new Date(r.data + "T12:00:00Z").getUTCDay() : -1;
      if (dow >= 1 && dow <= 5) {
        razoes.add("marcacoes_incompletas");
        getDia(r).razoes.push({
          tipo: "marcacoes_incompletas",
          detalhe: `${r.marcacoes.length} marcação(ões) — possível batida faltando`,
        });
      }
    }
  }

  // AX-007: débito do mês não autorizado (campo de resumo)
  const debito = raw.resumo?.debito_mes_atual_nao_autorizado ?? null;
  let debitoNaoAutorizado: string | null = null;
  if (debito && debito !== "00:00" && debito !== "-00:00") {
    razoes.add("debito_nao_autorizado");
    debitoNaoAutorizado = debito;
  }

  const diasProblema = Array.from(diasMap.values())
    .filter((d) => d.razoes.length > 0)
    .sort((a, b) => a.data.localeCompare(b.data));

  return {
    status: razoes.size > 0 ? "bloqueado" : "liberado",
    razoes: Array.from(razoes),
    diasProblema,
    debitoNaoAutorizado,
  };
}

export function gerarEmailHomologacao(raw: RawEspelho, result: HomologacaoResult, nomeChefia = ""): string {
  const nome = raw.servidor?.nome ?? "Servidor";
  const periodo = raw.periodo_referencia ?? "período";
  const sep = "─".repeat(44);

  const linhas: string[] = [
    `Assunto: Pendências Espelho de Ponto — ${periodo}`,
    "",
    `${nome},`,
    "",
    `Seu espelho de ponto de ${periodo} possui pendências que precisam ser resolvidas antes que eu possa homologar seu ponto eletrônico e sua frequência mensal.`,
    "",
    "PENDÊNCIAS IDENTIFICADAS:",
    sep,
  ];

  for (const dia of result.diasProblema) {
    const label = dia.diaSemana ? `${dia.dataFormatada} (${dia.diaSemana})` : dia.dataFormatada;
    linhas.push(`□  ${label}`);
    for (const r of dia.razoes) {
      linhas.push(`   • ${r.detalhe}`);
    }
    linhas.push("");
  }

  if (result.debitoNaoAutorizado) {
    linhas.push(`□  Débito não autorizado no mês: ${result.debitoNaoAutorizado}`);
    linhas.push(`   • Há horas de débito não compensadas. Verifique se há dias de ausência sem justificativa.`);
    linhas.push("");
  }

  linhas.push(
    "COMO CORRIGIR:",
    sep,
    `SIGRH → Consultas → Frequência → Espelho de Ponto → ${periodo}`,
    "",
    "Após corrigir, aguarde o próximo processamento do SIGRH para que as alterações reflitam no espelho.",
    "",
    "Qualquer dúvida, entre em contato.",
    "",
    "Atenciosamente,",
    nomeChefia || "Chefia de Unidade",
  );

  return linhas.join("\n");
}

export const RAZAO_LABEL: Record<RazaoBloqueio, string> = {
  dias_pendentes: "dias pendentes",
  he_nao_autorizado: "HE s/ autorização",
  debito_nao_autorizado: "débito n. autorizado",
  marcacoes_incompletas: "marcações incompletas",
};

export const STATUS_LABEL: Record<HomologacaoStatus, string> = {
  liberado: "Liberado",
  bloqueado: "Bloqueado",
  mes_atual: "Mês atual",
  vazio: "Vazio",
};

export interface BloqueioEntry {
  nome: string;
  periodoReferencia: string;
  raw: RawEspelho;
  result: HomologacaoResult;
}

export function gerarEmailServidor(entries: BloqueioEntry[], nomeChefia = ""): string {
  if (entries.length === 0) return "";
  const nome = entries[0].nome;
  const sepThin = "─".repeat(44);

  const linhas: string[] = [
    `Assunto: Pendências Espelho de Ponto`,
    "",
    `${nome},`,
    "",
    `Seu(s) espelho(s) de ponto abaixo possui(em) pendências que precisam ser resolvidas antes da homologação do ponto eletrônico e da frequência mensal.`,
    "",
  ];

  for (const entry of entries) {
    linhas.push(`PERÍODO: ${entry.periodoReferencia}`, sepThin);

    for (const dia of entry.result.diasProblema) {
      const label = dia.diaSemana ? `${dia.dataFormatada} (${dia.diaSemana})` : dia.dataFormatada;
      linhas.push(`□  ${label}`);
      for (const r of dia.razoes) linhas.push(`   • ${r.detalhe}`);
      linhas.push("");
    }

    if (entry.result.debitoNaoAutorizado) {
      linhas.push(`□  Débito não autorizado no mês: ${entry.result.debitoNaoAutorizado}`);
      linhas.push(`   • Verifique dias de ausência sem justificativa.`, "");
    }
  }

  linhas.push(
    "COMO CORRIGIR:",
    sepThin,
    "SIGRH → Consultas → Frequência → Espelho de Ponto → selecione o mês correspondente",
    "",
    "Após corrigir, aguarde o processamento do SIGRH para que as alterações reflitam no espelho.",
    "",
    "Qualquer dúvida, entre em contato.",
    "",
    "Atenciosamente,",
    nomeChefia || "Chefia de Unidade",
  );

  return linhas.join("\n");
}

export function gerarEmailGlobal(entries: BloqueioEntry[], nomeChefia = ""): string {
  if (entries.length === 0) return "";

  // Group by period
  const byPeriodo = new Map<string, BloqueioEntry[]>();
  for (const e of entries) {
    if (!byPeriodo.has(e.periodoReferencia)) byPeriodo.set(e.periodoReferencia, []);
    byPeriodo.get(e.periodoReferencia)!.push(e);
  }
  const periods = Array.from(byPeriodo.keys()).sort(
    (a, b) => periodoToDate(b).getTime() - periodoToDate(a).getTime()
  );

  const sep = "═".repeat(44);
  const sepThin = "─".repeat(44);

  const linhas: string[] = [
    `Assunto: Pendências Espelho de Ponto`,
    "",
    `Prezados servidores,`,
    "",
    `Os espelhos de ponto abaixo possuem pendências que precisam ser resolvidas para que eu possa homologar o ponto eletrônico e a frequência mensal de cada um.`,
    "",
    sep,
  ];

  for (const periodo of periods) {
    linhas.push(``, `  PERÍODO: ${periodo}`, sepThin);

    for (const entry of byPeriodo.get(periodo)!) {
      linhas.push(``, `  ${entry.nome}`);

      for (const dia of entry.result.diasProblema) {
        const label = dia.diaSemana ? `${dia.dataFormatada} (${dia.diaSemana})` : dia.dataFormatada;
        linhas.push(`  □  ${label}`);
        for (const r of dia.razoes) {
          linhas.push(`       • ${r.detalhe}`);
        }
      }

      if (entry.result.debitoNaoAutorizado) {
        linhas.push(`  □  Débito não autorizado no mês: ${entry.result.debitoNaoAutorizado}`);
        linhas.push(`       • Verifique dias de ausência sem justificativa.`);
      }
    }

    linhas.push(``, sep);
  }

  linhas.push(
    ``,
    `COMO CORRIGIR:`,
    sepThin,
    `SIGRH → Consultas → Frequência → Espelho de Ponto → selecione o mês correspondente`,
    ``,
    `Após corrigir, aguarde o processamento do SIGRH para que as alterações reflitam no espelho.`,
    ``,
    `Qualquer dúvida, entre em contato.`,
    ``,
    `Atenciosamente,`,
    nomeChefia || `Chefia de Unidade`,
  );

  return linhas.join("\n");
}
