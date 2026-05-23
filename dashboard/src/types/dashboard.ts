export interface EspelhoMesResume {
  periodoReferencia: string | null;
  periodoSlug: string;
  status: "completed" | "empty";
  capturedAt: string;
  daysWithMarcacoes: number;
  somaCreditoMin: number;
  somaDebitoMin: number;
  somaHhMin: number;
  dncFinalMin: number | null;
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
  registros: RegistroDia[];
  fonte: {
    tipo: string;
    pagina: string | null;
    rotulos_visiveis: string[];
  };
}
