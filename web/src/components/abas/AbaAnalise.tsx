import {
  Building2,
  ChevronDown,
  CircleCheck,
  CircleDashed,
  Columns3,
  Route,
  ShieldCheck,
  Store,
  TriangleAlert,
  UsersRound,
} from "lucide-react";
import { useDiagnostico, useSnapshotDaSelecao } from "@/hooks/dados";
import type { DimensaoDiagnostico, EvidenciaDiagnostico, RespostaDiagnostico } from "@/lib/api";
import { num } from "@/lib/formato";
import { useSelecao } from "@/lib/selecao";
import { cn } from "@/lib/utils";
import { FonteInfo } from "../FonteInfo";
import { Vazio } from "../Vazio";
import { Carregando } from "./AbaIndicadores";

const ICONE_DIMENSAO = {
  demanda_residente: UsersRound,
  perfil_publico: Building2,
  oferta_local: Store,
  acesso_centralidade: Route,
  confianca_dados: ShieldCheck,
};

const ROTULO_STATUS = {
  disponivel: "Com evidências",
  parcial: "Evidência parcial",
  insuficiente: "Dados insuficientes",
};

const ROTULO_MATURIDADE = {
  especializado: "Análise especializada",
  configurado: "Análise configurada",
  geral: "Leitura territorial geral",
};

function valorDaEvidencia(evidencia: EvidenciaDiagnostico) {
  if (evidencia.valor == null) return "Indisponível";
  if (evidencia.unidade === "R$ por mês") return `R$ ${num(evidencia.valor)}`;
  const casas = evidencia.unidade.includes("/") || evidencia.unidade.includes("km²") ? 2 : 0;
  return `${num(evidencia.valor, casas)} ${evidencia.unidade}`;
}

function valorDoContraste(valor: number, unidade: string) {
  const casas = unidade.includes("/") || unidade.includes("km²") ? 2 : 0;
  return `${num(valor, casas)} ${unidade}`;
}

function ComparacaoSelecionados({ comparacao }: { comparacao: NonNullable<RespostaDiagnostico["comparacao"]> }) {
  return (
    <section className="rounded-lg border border-nevoa bg-white p-4 sm:p-5" aria-labelledby="comparacao-selecionados">
      <header className="flex items-start gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-marinho text-ouro">
          <Columns3 className="size-[18px]" aria-hidden />
        </span>
        <div>
          <h3 id="comparacao-selecionados" className="larga text-[18px] font-extrabold text-marinho">Onde os bairros mais diferem</h3>
          <p className="mt-1 max-w-[76ch] text-[13px] leading-relaxed text-tinta-suave">{comparacao.leitura}</p>
        </div>
      </header>

      <dl className="mt-4 divide-y divide-nevoa border-y border-nevoa">
        {comparacao.contrastes.map((contraste) => (
          <div key={contraste.indicador} className="grid gap-2 py-3.5 md:grid-cols-[minmax(11rem,0.8fr)_minmax(18rem,1.2fr)_minmax(16rem,1fr)] md:items-center md:gap-5">
            <dt className="text-[13px] font-bold text-marinho">{contraste.rotulo}</dt>
            <dd className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-[12.5px] text-tinta-suave">
              <span><strong className="text-marinho">{contraste.maior.nome}</strong> {valorDoContraste(contraste.maior.valor, contraste.unidade)}</span>
              <span aria-hidden>e</span>
              <span><strong className="text-marinho">{contraste.menor.nome}</strong> {valorDoContraste(contraste.menor.valor, contraste.unidade)}</span>
            </dd>
            <dd className="text-[12px] leading-relaxed text-tinta-suave">{contraste.interpretacao}</dd>
          </div>
        ))}
      </dl>

      <p className="mt-3 flex items-start gap-2 text-[12.5px] leading-relaxed text-tinta-suave">
        <ShieldCheck className="mt-0.5 size-4 shrink-0 text-marinho-3" aria-hidden />
        {comparacao.proximo_passo}
      </p>
    </section>
  );
}

function SeloConfianca({ nivel }: { nivel: DimensaoDiagnostico["confianca"] }) {
  return (
    <span
      className={cn(
        "inline-flex min-h-6 items-center rounded-full px-2.5 text-[11.5px] font-semibold",
        nivel === "adequada" && "bg-[#e4f3eb] text-[#216542]",
        nivel === "aproximada" && "bg-ouro-claro text-ouro-escuro",
        nivel === "insuficiente" && "bg-secondary text-tinta-suave",
      )}
    >
      Confiança {nivel}
    </span>
  );
}

function Evidencia({ evidencia }: { evidencia: EvidenciaDiagnostico }) {
  return (
    <div className="relative grid gap-1 py-2.5 pr-8 sm:grid-cols-[minmax(11rem,1fr)_minmax(10rem,auto)_8.5rem_2rem] sm:items-center sm:gap-3 sm:pr-0">
      <dt className="text-[13px] font-medium leading-snug text-marinho">{evidencia.rotulo}</dt>
      <dd className={cn("numeros text-[13px] font-semibold sm:text-right", !evidencia.disponivel && "font-normal italic text-tinta-fraca")}>
        {valorDaEvidencia(evidencia)}
      </dd>
      <dd className="text-[12px] text-tinta-suave sm:text-right">
        {evidencia.percentil == null ? "Sem comparação" : `Percentil ${num(evidencia.percentil, 1)} · faixa ${evidencia.faixa}`}
      </dd>
      <dd className="absolute right-0 top-1.5 sm:static">
        <FonteInfo fonte={evidencia.fonte} data={evidencia.data_texto} rotulo={evidencia.rotulo} />
      </dd>
    </div>
  );
}

function Dimensao({ dimensao, regiaoId }: { dimensao: DimensaoDiagnostico; regiaoId: number }) {
  const Icone = ICONE_DIMENSAO[dimensao.id];
  const insuficiente = dimensao.status === "insuficiente";
  const tituloId = `dimensao-${regiaoId}-${dimensao.id}`;
  return (
    <section className="py-4 first:pt-0 last:pb-0" aria-labelledby={tituloId}>
      <div className="flex flex-wrap items-start gap-3">
        <span className={cn("mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md", insuficiente ? "bg-secondary text-tinta-fraca" : "bg-ouro-claro text-ouro-escuro")}>
          <Icone className="size-4" aria-hidden />
        </span>
        <div className="min-w-[12rem] flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <h4 id={tituloId} className="semi-larga text-[15px] font-bold text-marinho">{dimensao.titulo}</h4>
            <span className="inline-flex items-center gap-1 text-[11.5px] font-medium text-tinta-suave">
              {insuficiente ? <CircleDashed className="size-3.5" aria-hidden /> : <CircleCheck className="size-3.5 text-[#287553]" aria-hidden />}
              {ROTULO_STATUS[dimensao.status]}
            </span>
          </div>
          <p className="mt-1 max-w-[72ch] text-[13px] leading-relaxed text-tinta-suave">{dimensao.resumo}</p>
        </div>
        <SeloConfianca nivel={dimensao.confianca} />
      </div>

      {dimensao.evidencias.length > 0 && (
        <dl className="ml-11 mt-2 divide-y divide-nevoa">
          {dimensao.evidencias.map((evidencia) => <Evidencia key={evidencia.indicador} evidencia={evidencia} />)}
        </dl>
      )}

      <details className="group ml-11 mt-2 text-[12px] text-tinta-suave" open={insuficiente}>
        <summary className="flex min-h-8 w-fit cursor-pointer list-none items-center gap-1 font-semibold text-marinho marker:hidden">
          O que considerar
          <ChevronDown className="size-3.5 transition-transform group-open:rotate-180" aria-hidden />
        </summary>
        <ul className="max-w-[72ch] space-y-1 pb-1 leading-relaxed">
          {dimensao.limitacoes.map((texto) => <li key={texto}>— {texto}</li>)}
        </ul>
      </details>
    </section>
  );
}

export function AbaAnalise() {
  const { segmento, regioes } = useSelecao();
  const q = useDiagnostico(segmento, regioes);
  const salva = useSnapshotDaSelecao(segmento, regioes);

  if (segmento == null || !regioes.length) {
    return (
      <Vazio titulo="Escolha um segmento e ao menos um bairro">
        O diagnóstico organiza demanda, perfil, oferta, acesso e confiança para cada região selecionada.
      </Vazio>
    );
  }
  if (salva.id && salva.isLoading) return <Carregando />;
  if (salva.snapshot && !salva.snapshot.diagnostico) {
    return (
      <Vazio titulo="Este snapshot usa a metodologia anterior">
        O diagnóstico multidimensional não existia quando esta análise foi salva. Faça uma nova análise para preservar a metodologia atual.
      </Vazio>
    );
  }
  if (q.isLoading && !salva.snapshot?.diagnostico) return <Carregando />;
  if (q.isError && !salva.snapshot?.diagnostico) return <Vazio titulo="Não foi possível montar o diagnóstico">{(q.error as Error).message}</Vazio>;
  const d = salva.snapshot?.diagnostico ?? q.data!;
  const maturidade = ROTULO_MATURIDADE[d.segmento.maturidade];

  return (
    <div className="mx-auto flex w-full max-w-[1120px] flex-col gap-4 p-4 sm:p-5">
      <header className="flex flex-col gap-3 border-b border-nevoa pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="larga text-[21px] font-extrabold leading-tight text-marinho">Leitura territorial</h2>
            <span className="rounded-full bg-secondary px-2.5 py-1 text-[11.5px] font-semibold text-marinho">{maturidade}</span>
          </div>
          <p className="mt-1 max-w-[70ch] text-[13px] leading-relaxed text-tinta-suave">
            O que os dados sustentam sobre {d.segmento.nome.toLowerCase()}, o que ainda precisa ser validado e onde aprofundar a investigação.
          </p>
        </div>
        <span className="numeros shrink-0 text-[11.5px] text-tinta-fraca">Metodologia {d.versao_metodologia}</span>
      </header>

      <div className="flex items-start gap-2 rounded-md bg-ouro-claro/55 px-3 py-2.5 text-[12.5px] leading-relaxed text-marinho" role="note">
        <TriangleAlert className="mt-0.5 size-4 shrink-0 text-ouro-escuro" aria-hidden />
        <p><strong>Leitura orientativa:</strong> percentis mostram posição relativa entre bairros, não probabilidade de sucesso nem recomendação de investimento.</p>
      </div>

      {d.comparacao && <ComparacaoSelecionados comparacao={d.comparacao} />}

      <div className="flex flex-col gap-4">
        {d.regioes.map((regiao) => {
          const confianca = regiao.dimensoes.find((item) => item.id === "confianca_dados");
          const dimensoes = regiao.dimensoes.filter((item) => item.id !== "confianca_dados");
          const sinais = regiao.sintese.sinais ?? [];
          const atencoes = regiao.sintese.atencoes ?? [];
          return (
            <article key={regiao.id_regiao} className="rounded-lg border border-nevoa bg-white p-4 sm:p-5">
              <header className="flex flex-col gap-2 border-b border-nevoa pb-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="larga text-[18px] font-extrabold text-marinho">{regiao.nome}</h3>
                  <p className="mt-0.5 text-[12.5px] text-tinta-suave">
                    {regiao.sintese.dimensoes_disponiveis} dimensões completas · {regiao.sintese.dimensoes_parciais} parciais · {regiao.sintese.dimensoes_insuficientes} insuficientes
                  </p>
                </div>
                {confianca && <span className="self-start"><SeloConfianca nivel={confianca.confianca} /></span>}
              </header>

              <p className="max-w-[76ch] pt-4 text-[14px] font-medium leading-relaxed text-marinho">
                {regiao.sintese.leitura ?? "Este snapshot preserva a leitura da metodologia vigente quando a análise foi salva."}
              </p>

              {(sinais.length > 0 || atencoes.length > 0) && <div className="mt-4 grid gap-5 md:grid-cols-2 md:gap-8">
                <section aria-labelledby={`sinais-${regiao.id_regiao}`}>
                  <h4 id={`sinais-${regiao.id_regiao}`} className="semi-larga flex items-center gap-2 text-[14px] font-bold text-marinho">
                    <CircleCheck className="size-4 text-[#287553]" aria-hidden /> Sinais observados
                  </h4>
                  <ul className="mt-2 space-y-2 text-[12.5px] leading-relaxed text-tinta-suave">
                    {sinais.map((texto) => <li key={texto}>{texto}</li>)}
                  </ul>
                </section>
                <section aria-labelledby={`atencoes-${regiao.id_regiao}`}>
                  <h4 id={`atencoes-${regiao.id_regiao}`} className="semi-larga flex items-center gap-2 text-[14px] font-bold text-marinho">
                    <TriangleAlert className="size-4 text-ouro-escuro" aria-hidden /> Antes de decidir
                  </h4>
                  <ul className="mt-2 space-y-2 text-[12.5px] leading-relaxed text-tinta-suave">
                    {atencoes.map((texto) => <li key={texto}>{texto}</li>)}
                  </ul>
                </section>
              </div>}

              <footer className="mt-4 flex items-start gap-2 border-t border-nevoa pt-3 text-[12.5px] leading-relaxed text-tinta-suave">
                <ShieldCheck className="mt-0.5 size-4 shrink-0 text-marinho-3" aria-hidden />
                <p><strong className="text-marinho">Próximo passo:</strong> {regiao.sintese.proximo_passo}</p>
              </footer>

              <details className="group mt-3 border-t border-nevoa pt-2">
                <summary className="flex min-h-9 w-fit cursor-pointer list-none items-center gap-1.5 text-[12.5px] font-semibold text-marinho marker:hidden">
                  Ver evidências, fontes e limitações
                  <ChevronDown className="size-4 transition-transform group-open:rotate-180" aria-hidden />
                </summary>
                <div className="divide-y divide-nevoa pt-3">
                  {dimensoes.map((dimensao) => <Dimensao key={dimensao.id} dimensao={dimensao} regiaoId={regiao.id_regiao} />)}
                </div>
              </details>
            </article>
          );
        })}
      </div>
    </div>
  );
}
