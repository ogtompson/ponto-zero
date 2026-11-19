// HU-008: comparação lado a lado, mesmos indicadores e unidades, sem ranking.
import { BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useComparacao } from "@/hooks/dados";
import { num, valorIndicador } from "@/lib/formato";
import { useSelecao } from "@/lib/selecao";
import { Aviso } from "../Aviso";
import { FonteInfo, ListaFontes } from "../FonteInfo";
import { Vazio } from "../Vazio";
import { Carregando } from "./AbaIndicadores";

const soData = (t: string | null | undefined) => (t && /^\d/.test(t) ? t : null);

function FonteDaLinha({ valores, rotulo }: { valores: { fonte: string | null; data_texto: string | null }[]; rotulo: string }) {
  const ref = valores.find((v) => v.fonte);
  return <FonteInfo fonte={ref?.fonte ?? null} data={soData(ref?.data_texto)} rotulo={rotulo} />;
}

export function AbaComparar() {
  const { segmento, regioes } = useSelecao();
  const q = useComparacao(segmento, regioes);

  if (regioes.length < 2) return <Vazio titulo="Selecione ao menos duas regiões para comparar">Marque mais um bairro no mapa.</Vazio>;
  if (q.isLoading) return <Carregando />;
  if (q.isError) return <Vazio titulo="Não deu para montar a comparação">{(q.error as Error).message}</Vazio>;
  const d = q.data!;

  return (
    <div className="flex flex-col gap-3 p-4">
      <div className="overflow-x-auto rounded-lg border border-nevoa bg-white">
        <table className="w-full min-w-[560px] border-collapse text-[13.5px]">
          <thead>
            <tr className="border-b border-marinho/80">
              <th scope="col" className="sticky left-0 bg-white px-3 py-2.5 text-left font-semibold text-tinta-suave">
                Indicador
              </th>
              {d.regioes.map((r) => (
                <th key={r.id_regiao} scope="col" className="semi-larga px-3 py-2.5 text-left font-bold text-marinho">
                  {r.nome}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {d.linhas.map((l) => (
              <tr key={l.tipo} className="border-b border-nevoa last:border-0">
                <th scope="row" className="sticky left-0 bg-white px-3 py-2 text-left font-normal text-tinta-suave">
                  <span className="flex items-center gap-1">
                    {l.rotulo}
                    <FonteDaLinha valores={l.valores} rotulo={l.rotulo} />
                  </span>
                </th>
                {l.valores.map((v) => (
                  <td key={v.id_regiao} className={v.disponivel ? "px-3 py-2 font-semibold numeros" : "px-3 py-2 italic text-tinta-fraca"}>
                    {valorIndicador(v.valor, l.unidade)}
                  </td>
                ))}
              </tr>
            ))}
            {d.oferta && (
              <>
                <tr className="border-t border-marinho/30 bg-papel/60">
                  <th scope="row" className="sticky left-0 bg-[#f9f9fc] px-3 py-2 text-left font-normal text-tinta-suave">
                    <span className="flex items-center gap-1">
                      {d.oferta.segmento}: estabelecimentos
                      <FonteInfo fonte={d.oferta.fonte} data={soData(d.oferta.data_texto)} rotulo="oferta" />
                    </span>
                  </th>
                  {d.oferta.valores.map((v) => (
                    <td key={v.id_regiao} className="px-3 py-2 font-semibold numeros">
                      {v.status_dado === "sem_registro_observado" ? <span className="font-normal italic text-tinta-fraca">Sem registro</span> : num(v.quantidade)}
                    </td>
                  ))}
                </tr>
                <tr className="bg-papel/60">
                  <th scope="row" className="sticky left-0 bg-[#f9f9fc] px-3 py-2 text-left font-normal text-tinta-suave">
                    Por 10 mil habitantes
                  </th>
                  {d.oferta.valores.map((v) => (
                    <td key={v.id_regiao} className="px-3 py-2 font-semibold numeros">
                      {v.status_dado === "sem_registro_observado" ? <span aria-label="Não calculado">—</span> : num(v.por_10k_hab, 2)}
                    </td>
                  ))}
                </tr>
              </>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex max-w-2xl flex-col gap-1.5">
          {!d.oferta && <p className="text-[13px] text-tinta-suave">Escolha um segmento para incluir a oferta comercial na comparação.</p>}
          {d.avisos.map((a) => (
            <Aviso key={a}>{a}</Aviso>
          ))}
        </div>
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm">
              <BookOpen /> Fontes usadas
            </Button>
          </PopoverTrigger>
          <PopoverContent align="end" className="w-80">
            <ListaFontes fontes={d.fontes} />
          </PopoverContent>
        </Popover>
      </div>
    </div>
  );
}
