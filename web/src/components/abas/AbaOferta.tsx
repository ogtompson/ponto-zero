// HU-006: oferta comercial do segmento e concentração por região (mesma métrica para todas).
import { useOferta, useSegmentos, useSnapshotDaSelecao } from "@/hooks/dados";
import { dataBr, num } from "@/lib/formato";
import { useSelecao } from "@/lib/selecao";
import { Aviso } from "../Aviso";
import { FonteInfo } from "../FonteInfo";
import { IconeSegmento } from "../IconeSegmento";
import { Vazio } from "../Vazio";
import { Carregando } from "./AbaIndicadores";

export function AbaOferta() {
  const { segmento, regioes } = useSelecao();
  const segs = useSegmentos();
  const q = useOferta(segmento, regioes);
  const salva = useSnapshotDaSelecao(segmento, regioes);

  if (segmento == null)
    return <Vazio titulo="Escolha um segmento para ver a oferta comercial">A oferta e a análise dependem do tipo de negócio.</Vazio>;
  if (salva.id && salva.isLoading) return <Carregando />;
  if (q.isLoading && !salva.snapshot) return <Carregando />;
  if (q.isError && !salva.snapshot) return <Vazio titulo="Não deu para carregar a oferta">{(q.error as Error).message}</Vazio>;
  const d = salva.snapshot?.oferta ?? q.data!;
  const seg = salva.snapshot?.selection.segmento ?? segs.data?.find((s) => s.id_categoria === segmento);
  const referencia = seg?.por_10k_hab ?? 0;
  const maximo = Math.max(referencia * 1.4, ...d.regioes.map((r) => r.por_10k_hab ?? 0)) || 1;
  const totalOferta = d.qualidade.registros_associados ?? d.segmento.total_estabelecimentos ?? d.estabelecimentos.length;

  return (
    <div className="flex flex-col gap-4 p-4 lg:flex-row">
      <div className="flex-1">
        {regioes.length === 0 ? (
          <div className="flex items-center gap-3 rounded-lg border border-nevoa bg-white p-4">
            <IconeSegmento nome={d.segmento.nome} className="size-6 text-marinho-3" />
            <p className="text-[15px]">
              <strong className="numeros">{num(totalOferta)}</strong> empresas formais ativas no Recife para este recorte.
              Escolha bairros para comparar a concentração.
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-3" aria-label={`Concentração de ${d.segmento.nome.toLowerCase()}`}>
            {d.regioes.map((r) => (
              <li key={r.id_regiao} className="grid grid-cols-[minmax(110px,160px)_1fr] items-center gap-3">
                <span className="truncate text-[14px] font-semibold">{r.nome}</span>
                <div>
                  <div className="relative h-6 rounded bg-secondary">
                    <div
                      className="absolute inset-y-0 left-0 rounded bg-marinho"
                      style={{ width: `${Math.min(100, ((r.por_10k_hab ?? 0) / maximo) * 100)}%` }}
                    />
                    <div
                      className="absolute inset-y-[-3px] w-0.5 bg-ouro"
                      style={{ left: `${(referencia / maximo) * 100}%` }}
                      title="Média do Recife"
                    />
                  </div>
                  <p className="mt-1 text-[12.5px] text-tinta-suave numeros">
                    {r.quantidade > 0 ? (
                      <>
                        <strong className="text-marinho">{num(r.por_10k_hab, 2)}</strong> por 10 mil habitantes, {num(r.quantidade)} no total
                      </>
                    ) : (
                      <span className="italic">{r.mensagem}</span>
                    )}
                  </p>
                </div>
              </li>
            ))}
            <li className="flex items-center gap-2 pl-[calc(min(160px,40%)+12px)] text-[12px] text-tinta-suave">
              <span className="inline-block h-3 w-0.5 bg-ouro" /> média do Recife: {num(referencia, 2)} por 10 mil habitantes
            </li>
          </ul>
        )}
      </div>
      <aside className="flex flex-col gap-2 lg:w-72">
        <p className="flex items-center gap-1 text-[13px] text-tinta-suave">
          Fonte: <span className="font-semibold text-marinho">{d.fonte}</span>
          <FonteInfo fonte={d.fonte} data={d.data_referencia} rotulo="oferta comercial" />
        </p>
        <p className="text-[13px] text-tinta-suave">Base atualizada em {dataBr(d.data_referencia)}</p>
        {d.qualidade.criterio && (
          <p className="text-[13px] leading-relaxed text-tinta-suave">
            <span className="font-semibold text-marinho">Recorte:</span> {d.qualidade.criterio}
          </p>
        )}
        {d.qualidade.coordenadas_precisas === 0 && (
          <p className="text-[13px] leading-relaxed text-tinta-suave">
            O mapa colore os bairros pela contagem cadastral. A fonte não informa pontos precisos para marcadores.
          </p>
        )}
        <Aviso>{d.qualidade.descricao}</Aviso>
      </aside>
    </div>
  );
}
