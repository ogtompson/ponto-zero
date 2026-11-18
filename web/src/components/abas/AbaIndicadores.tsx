// HU-005: indicadores territoriais. HU-007: fonte e data em cada valor.
import { NumberTicker } from "@/components/ui/number-ticker";
import { Skeleton } from "@/components/ui/skeleton";
import { useIndicadores } from "@/hooks/dados";
import { valorIndicador } from "@/lib/formato";
import { useSelecao } from "@/lib/selecao";
import { Aviso } from "../Aviso";
import { FonteInfo } from "../FonteInfo";
import { Pino } from "../Marca";
import { Vazio } from "../Vazio";

export function AbaIndicadores() {
  const { regioes } = useSelecao();
  const q = useIndicadores(regioes);

  if (!regioes.length) return <Vazio titulo="Escolha um bairro para ver os indicadores">Clique no mapa ou use a busca ao lado.</Vazio>;
  if (q.isLoading) return <Carregando />;
  if (q.isError) return <Vazio titulo="Não deu para carregar os indicadores">{(q.error as Error).message}</Vazio>;
  const d = q.data!;

  return (
    <div className="flex flex-col gap-3 p-4">
      <Aviso>{d.aviso}</Aviso>
      <div className="flex gap-3 overflow-x-auto pb-2">
        {d.regioes.map((r) => {
          const pop = r.indicadores.find((i) => i.tipo === "populacao");
          return (
            <article key={r.id_regiao} className="w-[272px] shrink-0 rounded-lg border border-nevoa bg-white p-4">
              <header className="flex items-center gap-2">
                <Pino tamanho={14} />
                <h3 className="larga truncate text-[17px] font-extrabold leading-tight text-marinho">{r.nome}</h3>
              </header>
              {pop?.valor != null && (
                <p className="mt-3 flex items-baseline gap-1.5">
                  <NumberTicker value={pop.valor} className="larga text-[30px] font-extrabold leading-none text-marinho" />
                  <span className="text-sm text-tinta-suave">moradores</span>
                  <FonteInfo fonte={pop.fonte} data={pop.data_referencia} rotulo={pop.rotulo} className="ml-auto" />
                </p>
              )}
              {r.mensagem && <p className="mt-3 text-sm text-tinta-suave">{r.mensagem}</p>}
              <dl className="mt-3 divide-y divide-nevoa">
                {r.indicadores
                  .filter((i) => i.tipo !== "populacao")
                  .map((i) => (
                    <div key={i.tipo} className="flex items-center gap-2 py-1.5">
                      <dt className="flex-1 text-[13px] text-tinta-suave">{i.rotulo}</dt>
                      <dd className={i.disponivel ? "text-[13.5px] font-semibold numeros" : "text-[13px] italic text-tinta-fraca"}>
                        {valorIndicador(i.valor, i.unidade)}
                      </dd>
                      <FonteInfo fonte={i.fonte} data={i.data_referencia} rotulo={i.rotulo} />
                      {!i.disponivel && <span className="size-6" />}
                    </div>
                  ))}
              </dl>
            </article>
          );
        })}
      </div>
    </div>
  );
}

export function Carregando() {
  return (
    <div className="flex gap-3 p-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <Skeleton key={i} className="h-56 w-[272px] shrink-0" />
      ))}
    </div>
  );
}
