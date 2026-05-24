export interface EspelhoMesResume {
  periodoReferencia: string | null;
  periodoSlug: string;
  status: "completed" | "empty";
  capturedAt: string;
  daysWithMarcacoes: number;
  somaCreditoMin: number;
  somaHrMin: number;
  somaDebitoMin: number;
  somaHhMin: number;
  cargaEsperadaMin: number;
  dncFinalMin: number | null;
  balanceMin: number | null;
}

export interface ServidorResume {
  slug: string;
  nome: string;
  siape: string | null;
  meses: EspelhoMesResume[];
  totalMeses: number;
  periodoRange: string;
  statusIndicator: "completo" | "com-vazios";
}

export interface RegistroDia {
  data: string;
  dia_semana: string | null;
  marcacoes: string[];
  ocorrencias: string[];
  observacoes: string[];
  situacao: string | null;
  textos_visiveis: string[];
  hr: string | null;
  hc: string | null;
  he: string | null;
  ha: string | null;
  hh: string | null;
  credito: string | null;
  debito: string | null;
  saldo_no_mes: string | null;
  credito_acumulado: string | null;
  dnc: string | null;
}

export interface ResumoHorasApuradas {
  carga_horaria_contratada: string | null;
  carga_horaria_esperada_mes: string | null;
  total_horas_registradas: string | null;
  total_horas_justificadas: string | null;
  total_horas_homologadas: string | null;
  saldo_mes_anterior_compensacao: string | null;
  total_horas_mes_anterior_compensadas: string | null;
  debito_mes_anterior_nao_compensado: string | null;
  debito_mes_atual_nao_autorizado: string | null;
  outros_debitos_nao_compensados_vencidos: string | null;
  totalizacao_debito_nao_compensavel: string | null;
  total_horas_pendentes_compensacao: string | null;
  saldo_horas_mes: string | null;
  saldo_horas_mes_compensar_proximo: string | null;
  credito_horas_disponivel_mes: string | null;
  credito_em_horas: string | null;
}

export interface RawEspelho {
  schema_version: number;
  run_id: string;
  captured_at: string;
  status: "completed" | "empty";
  periodo_referencia: string | null;
  mensagens: string[];
  servidor: {
    nome: string;
    identificador: string | null;
    texto_visivel: string | null;
  };
  resumo?: ResumoHorasApuradas | null;
  registros: RegistroDia[];
  fonte: {
    tipo: string;
    pagina: string | null;
    rotulos_visiveis: string[];
  };
}
