// HU-009: análise inicial da relação entre demanda e oferta.
// Regras e fontes ficam visíveis; o resultado é sempre hipótese, nunca recomendação.
import { useAnalise } from "@/hooks/dados";
import type { Classificacao } from "@/lib/api";
import { num } from "@/lib/formato";
import { useSelecao } from "@/lib/selecao";
import { cn } from "@/lib/utils";
import { Aviso } from "../Aviso";
import { ListaFontes } from "../FonteInfo";
import { PontosEsperados } from "../PontosEsperados";
import { Vazio } from "../Vazio";
import { Carregando } from "./AbaIndicadores";

const SELO: Record<Classificacao, string> = {
  possivel_lacuna: "bg-ouro text-marinho",
  sem_indicio: "bg-secondary text-tinta-suave",
  nao_classificada: "hachura text-tinta-suave",
};

export function AbaAnalise() {
  const { segmento, regioes } = useSelecao();
  const q = useAnalise(segmento, regioes);

  const falta = [segmento == null && "um segmento", regioes.length < 2 && `${regioes.length ? "mais um bairro" : "ao menos dois bairros"}`].filter(Boolean);
  if (falta.length)
    return (
      <Vazio titulo="A análise precisa de um segmento e de dois ou mais bairros">
        Falta escolher {falta.join(" e ")}.
      </Vazio>
    );
  if (q.isLoading) return <Carregando />;
  if (q.isError) return <Vazio titulo="Não deu para calcular a análise">{(q.error as Error).message}</Vazio>;
  const d = q.data!;
  const [naoRecomendacao, ...outros] = d.avisos;

  return (
    <div className="flex flex-col gap-4 p-4">
      <Aviso forte>{naoRecomendacao}</Aviso>
      <div className="flex flex-col gap-4 xl:flex-row">
        <ul className="grid flex-1 gap-3 sm:grid-cols-2 2xl:grid-cols-3">
          {d.resultados.map((r) => (
            <li
              key={r.id_regiao}
              className={cn(
                "rounded-lg border bg-white p-4",
                r.classificacao === "possivel_lacuna" ? "border-ouro shadow-[inset_4px_0_0_#DDBA43]" : "border-nevoa",
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <h3 className="larga text-[16px] font-extrabold leading-tight text-marinho">{r.nome}</h3>
                <span className={cn("shrink-0 rounded-full px-2.5 py-0.5 text-[12px] font-semibold", SELO[r.classificacao])}>{r.rotulo}</span>
              </div>
              <div className="mt-3">
                <PontosEsperados esperado={r.esperado} encontrados={r.encontrados} />
              </div>
              <p className="mt-2.5 text-[13px] text-tinta-suave">
                {r.classificacao === "nao_classificada" ? (
                  <>Motivo: {r.motivo}</>
                ) : (
                  <>
                    <strong className="text-marinho numeros">{num(r.encontrados)}</strong> encontrado{r.encontrados === 1 ? "" : "s"} para{" "}
                    <strong className="text-marinho numeros">{num(r.esperado, 1)}</strong> esperado{r.esperado === 1 ? "" : "s"} em {num(r.populacao)} moradores
                  </>
                )}
              </p>
            </li>
          ))}
        </ul>
        <aside className="flex flex-col gap-4 xl:w-80">
          <section>
            <h3 className="semi-larga text-[14px] font-bold text-marinho">Como a análise é feita</h3>
            <dl className="mt-2 flex flex-col gap-1.5 text-[13px]">
              {d.criterios.map((c) => (
                <div key={c.nome}>
                  <dt className="inline font-semibold text-marinho">{c.nome}: </dt>
                  <dd className="inline text-tinta-suave">{c.regra}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-2 flex items-center gap-3 text-[12px] text-tinta-suave">
              <span className="flex items-center gap-1">
                <span className="inline-block size-3 rounded-full border-[1.5px] border-dashed border-marinho/45" /> esperado
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block size-3 rounded-full bg-ouro ring-[1.5px] ring-marinho" /> encontrado
              </span>
            </p>
          </section>
          <section>
            <h3 className="semi-larga text-[14px] font-bold text-marinho">Fontes usadas no cálculo</h3>
            <ListaFontes fontes={d.fontes} />
          </section>
          <div className="flex flex-col gap-1.5">
            {outros.map((a) => (
              <Aviso key={a}>{a}</Aviso>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
