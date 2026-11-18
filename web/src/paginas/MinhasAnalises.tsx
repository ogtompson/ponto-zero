import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { MapPinned, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { DialogoConta } from "@/components/DialogoConta";
import { IconeSegmento } from "@/components/IconeSegmento";
import { Pino } from "@/components/Marca";
import { Vazio } from "@/components/Vazio";
import { useAnalisesSalvas, useSegmentos, useSessao } from "@/hooks/dados";
import { api, type AnaliseSalva } from "@/lib/api";
import { dataBr } from "@/lib/formato";

export function MinhasAnalises() {
  const sessao = useSessao();
  const lista = useAnalisesSalvas(!!sessao.data);
  const [conta, setConta] = useState(false);

  if (sessao.isLoading) return <Pagina><Skeleton className="h-40" /></Pagina>;
  if (!sessao.data)
    return (
      <Pagina>
        <Vazio titulo="Entre para ver as análises da sua empresa">
          <p>O mapa, a comparação e a análise funcionam sem conta. A conta serve para salvar e reabrir estudos.</p>
          <Button className="mt-4" onClick={() => setConta(true)}>Entrar ou criar conta</Button>
        </Vazio>
        <DialogoConta aberto={conta} aoMudar={setConta} />
      </Pagina>
    );

  const u = sessao.data;
  return (
    <Pagina>
      <header className="mb-6">
        <h1 className="larga text-[28px] font-extrabold leading-tight text-marinho">Análises de {u.empresa}</h1>
        <p className="mt-1 text-tinta-suave">
          {u.segmento ? <>Segmento da empresa: {u.segmento}.</> : "Sua empresa ainda não tem segmento: ele é definido na primeira análise salva."}
        </p>
      </header>
      {lista.isLoading ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      ) : !lista.data?.length ? (
        <Vazio titulo="Nenhuma análise salva ainda">Escolha um segmento e bairros no mapa e use o botão Salvar.</Vazio>
      ) : (
        <ul className="flex flex-col gap-3">
          {lista.data.map((a) => (
            <ItemAnalise key={a.id_analise} a={a} />
          ))}
        </ul>
      )}
    </Pagina>
  );
}

function Pagina({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto w-full max-w-4xl flex-1 px-4 py-8 sm:px-6">{children}</div>;
}

function ItemAnalise({ a }: { a: AnaliseSalva }) {
  const segs = useSegmentos();
  const navegar = useNavigate();
  const qc = useQueryClient();
  const [confirmar, setConfirmar] = useState(false);
  const idSeg = segs.data?.find((s) => s.nome === a.segmento)?.id_categoria;

  const excluir = useMutation({
    mutationFn: () => api.del(`/analises/${a.id_analise}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["analises"] });
      toast("Análise excluída", { description: a.nome });
    },
  });

  function abrir() {
    const p = new URLSearchParams();
    if (idSeg) p.set("segmento", String(idSeg));
    p.set("bairros", a.regioes.map((r) => r.id_regiao).join(","));
    p.set("analise", String(a.id_analise));
    navegar(`/?${p.toString()}`);
  }

  return (
    <li className="rounded-lg border border-nevoa bg-white p-5">
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0 flex-1">
          <h2 className="semi-larga text-[19px] font-bold leading-snug text-marinho">{a.nome}</h2>
          <p className="mt-0.5 flex items-center gap-1.5 text-[13px] text-tinta-suave">
            {a.segmento && <IconeSegmento nome={a.segmento} className="size-3.5" />}
            {a.segmento ?? "Sem segmento"}, criada em {dataBr(a.data_criacao)}
          </p>
          {a.objetivo && <p className="mt-2 max-w-prose text-[14.5px]">{a.objetivo}</p>}
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" onClick={abrir}>
            <MapPinned /> Abrir no mapa
          </Button>
          {confirmar ? (
            <>
              <Button size="sm" variant="destructive" onClick={() => excluir.mutate()} disabled={excluir.isPending}>
                Excluir de vez
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setConfirmar(false)}>
                Manter
              </Button>
            </>
          ) : (
            <Button size="icon" variant="ghost" aria-label={`Excluir ${a.nome}`} onClick={() => setConfirmar(true)}>
              <Trash2 />
            </Button>
          )}
        </div>
      </div>
      <ul className="mt-3 flex flex-wrap gap-1.5">
        {a.regioes.map((r) => (
          <li key={r.id_regiao} className="flex items-center gap-1.5 rounded-full bg-ouro-claro py-1 pl-1.5 pr-2.5 text-[12.5px] font-semibold text-marinho">
            <Pino tamanho={11} /> {r.nome}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-[12.5px] text-tinta-fraca">
        {a.qtd_relatorios === 0
          ? "Nenhum relatório exportado."
          : `${a.qtd_relatorios} ${a.qtd_relatorios === 1 ? "relatório exportado" : "relatórios exportados"}, o último em ${dataBr(a.ultimo_relatorio)} (${a.relatorios[0]?.formato}).`}
      </p>
    </li>
  );
}
