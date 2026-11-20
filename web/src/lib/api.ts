// Cliente da API. Tudo passa por /api: no Docker, o Nginx encaminha para o container da API.

export class ErroApi extends Error {
  status: number;
  campo: string | null;
  constructor(status: number, mensagem: string, campo: string | null = null) {
    super(mensagem);
    this.status = status;
    this.campo = campo;
  }
}

async function pedir<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  let resposta: Response;
  try {
    resposta = await fetch(`/api${caminho}`, {
      credentials: "same-origin",
      ...opcoes,
      headers: { "Content-Type": "application/json", ...(opcoes.headers ?? {}) },
    });
  } catch {
    throw new ErroApi(0, "Sem conexão com a API. Confira se os containers estão no ar.");
  }
  if (!resposta.ok) {
    let mensagem = "Algo não saiu como esperado. Tente de novo.";
    let campo: string | null = null;
    try {
      const corpo = await resposta.json();
      const d = corpo?.detail;
      if (typeof d === "string") mensagem = d;
      else if (d?.mensagem) {
        mensagem = d.mensagem;
        campo = d.campo ?? null;
      }
    } catch {
      /* resposta sem JSON */
    }
    throw new ErroApi(resposta.status, mensagem, campo);
  }
  if (resposta.status === 204) return undefined as T;
  return resposta.json() as Promise<T>;
}

export const api = {
  get: <T,>(c: string) => pedir<T>(c),
  post: <T,>(c: string, corpo?: unknown) => pedir<T>(c, { method: "POST", body: corpo ? JSON.stringify(corpo) : undefined }),
  del: <T,>(c: string) => pedir<T>(c, { method: "DELETE" }),
  async baixar(caminho: string, corpo: unknown): Promise<{ blob: Blob; nome: string }> {
    const resposta = await fetch(`/api${caminho}`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });
    if (!resposta.ok) {
      let mensagem = "Não foi possível gerar o arquivo. Tente de novo.";
      try {
        const d = (await resposta.json())?.detail;
        mensagem = typeof d === "string" ? d : d?.mensagem ?? mensagem;
      } catch {
        /* sem JSON */
      }
      throw new ErroApi(resposta.status, mensagem);
    }
    const disp = resposta.headers.get("Content-Disposition") ?? "";
    const nome = /filename="([^"]+)"/.exec(disp)?.[1] ?? "pontozero";
    return { blob: await resposta.blob(), nome };
  },
};

// ------------------------------------------------------------------ tipos
export type Segmento = {
  id_categoria: number;
  nome: string;
  descricao: string | null;
  total_estabelecimentos: number;
  por_10k_hab: number;
  slug: string;
  maturidade: "especializado" | "configurado" | "geral";
  disponibilidade: "piloto" | "preparacao" | "personalizado";
  direcionadores: string[];
  area_influencia: null | { modo: "caminhada" | "deslocamento"; minutos: number };
  perimetro_oferta?: string;
  precisao_oferta?: "direta" | "aproximada";
  cnaes_oferta?: { codigo: string; descricao: string }[];
  cnaes_diretos?: string[];
};

export type Regiao = {
  id_regiao: number;
  nome: string;
  tipo: string;
  cidade: string;
  estado: string;
  populacao: number | null;
  renda: number | null;
  densidade: number | null;
};

export type Indicador = {
  tipo: string;
  rotulo: string;
  unidade: string;
  valor: number | null;
  disponivel: boolean;
  fonte: string | null;
  data_referencia: string | null;
  data_texto: string | null;
  derivado: boolean;
};

export type RespostaIndicadores = {
  regioes: (Regiao & { indicadores: Indicador[]; mensagem: string | null })[];
  aviso: string;
};

export type Estabelecimento = {
  id: number;
  nome: string;
  lat: number;
  lng: number;
  endereco: string | null;
  id_regiao: number;
  regiao: string;
};

export type RespostaOferta = {
  segmento: Segmento;
  fonte: string;
  data_referencia: string | null;
  data_texto: string;
  metrica: string;
  regioes: {
    id_regiao: number;
    nome: string;
    quantidade: number;
    populacao: number | null;
    por_10k_hab: number | null;
    mensagem: string | null;
    status_dado: "observado" | "sem_registro_observado";
  }[];
  estabelecimentos: Estabelecimento[];
  qualidade: QualidadeOferta;
  aviso: string;
};

export type QualidadeOferta = {
  cobertura: "parcial" | "cadastral" | "verificada";
  zero_confirmado: boolean;
  descricao: string;
  cnpjs_formais?: number;
  registros_associados?: number;
  coordenadas_precisas?: number;
  descartados_sem_bairro?: number;
  criterio?: string;
  precisao_segmento?: "direta" | "aproximada";
};

export type Fonte = { fonte: string; data_texto: string; usada_em: string[] };

export type RespostaComparacao = {
  regioes: { id_regiao: number; nome: string }[];
  linhas: {
    tipo: string;
    rotulo: string;
    unidade: string;
    ordem: number;
    valores: { id_regiao: number; valor: number | null; disponivel: boolean; fonte: string | null; data_texto: string | null }[];
  }[];
  oferta: null | {
    segmento: string;
    fonte: string;
    data_texto: string;
    metrica: string;
    qualidade: QualidadeOferta;
    valores: { id_regiao: number; quantidade: number; por_10k_hab: number | null; mensagem: string | null; status_dado: "observado" | "sem_registro_observado" }[];
  };
  fontes: Fonte[];
  avisos: string[];
};

export type Classificacao = "oferta_observada_baixa" | "oferta_observada_compativel" | "nao_classificada";

export type RespostaAnalise = {
  segmento: Segmento;
  parametros: { min_esperado: number; cobertura_max: number; referencia_10k: number };
  criterios: { nome: string; regra: string }[];
  resultados: {
    id_regiao: number;
    nome: string;
    populacao: number | null;
    encontrados: number;
    esperado: number | null;
    cobertura: number | null;
    classificacao: Classificacao;
    rotulo: string;
    motivo: string;
    status_dado: "observado" | "sem_registro_observado";
    zero_confirmado: boolean;
  }[];
  qualidade_oferta: QualidadeOferta;
  fontes: Fonte[];
  avisos: string[];
};

export type EvidenciaDiagnostico = {
  indicador: string;
  rotulo: string;
  valor: number | null;
  unidade: string;
  percentil: number | null;
  faixa: "alta" | "intermediaria" | "baixa" | "indisponivel";
  disponivel: boolean;
  qualidade: "adequada" | "aproximada" | "insuficiente";
  interpretacao: string;
  fonte: string | null;
  data_texto: string | null;
};

export type DimensaoDiagnostico = {
  id: "demanda_residente" | "perfil_publico" | "oferta_local" | "acesso_centralidade" | "confianca_dados";
  titulo: string;
  status: "disponivel" | "parcial" | "insuficiente";
  confianca: "adequada" | "aproximada" | "insuficiente";
  resumo: string;
  evidencias: EvidenciaDiagnostico[];
  limitacoes: string[];
};

export type RespostaDiagnostico = {
  versao_metodologia: string;
  segmento: Segmento;
  sem_score: true;
  regioes: {
    id_regiao: number;
    nome: string;
    dimensoes: DimensaoDiagnostico[];
    sintese: {
      dimensoes_disponiveis: number;
      dimensoes_parciais: number;
      dimensoes_insuficientes: number;
      proximo_passo: string;
    };
  }[];
  avisos: string[];
};

export type Usuario = {
  id_usuario: number;
  nome: string;
  email: string;
  perfil: string;
  id_empresa: number;
  empresa: string;
  segmento: string | null;
};

export type AnaliseSalva = {
  id_analise: number;
  nome: string;
  data_criacao: string;
  objetivo: string | null;
  empresa: string;
  segmento: string | null;
  id_categoria: number | null;
  versao_metodologia: string;
  capturado_em: string | null;
  snapshot_disponivel: boolean;
  snapshot?: SnapshotAnalise | null;
  qtd_regioes: number;
  qtd_relatorios: number;
  ultimo_relatorio: string | null;
  regioes: { id_regiao: number; nome: string }[];
  relatorios: { id_relatorio: number; data_geracao: string; formato: string }[];
};

export type SnapshotAnalise = {
  schema_version: number;
  methodology_version: string;
  captured_at: string;
  selection: { segmento: Segmento; regioes: number[] };
  indicadores: RespostaIndicadores;
  oferta: RespostaOferta;
  comparacao: RespostaComparacao;
  analise: RespostaAnalise;
  diagnostico?: RespostaDiagnostico;
};

export type Status = {
  api: { versao: string; container: string; python: string; iniciada_em: string; segundos_no_ar: number; processo: number };
  banco: null | {
    versao: string;
    nome: string;
    usuario: string;
    ip: string | null;
    ligado_em: string;
    volume_inicializado_em: string | null;
    tamanho: string;
    contagens: Record<string, number>;
  };
};
