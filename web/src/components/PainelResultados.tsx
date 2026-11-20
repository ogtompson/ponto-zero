import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { BarChart3, Bookmark, Columns3, Store, Telescope } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useAnalisesSalvas, useSegmentos, useSessao } from "@/hooks/dados";
import { useSelecao } from "@/lib/selecao";
import { AbaAnalise } from "./abas/AbaAnalise";
import { AbaComparar } from "./abas/AbaComparar";
import { AbaIndicadores } from "./abas/AbaIndicadores";
import { AbaOferta } from "./abas/AbaOferta";
import { DialogoConta } from "./DialogoConta";
import { DialogoSalvar } from "./DialogoSalvar";
import { MenuExportar } from "./MenuExportar";
import { PrimeirosPassos } from "./Vazio";

export function PainelResultados() {
  const { segmento, regioes } = useSelecao();
  const [params] = useSearchParams();
  const sessao = useSessao();
  const salvas = useAnalisesSalvas(!!sessao.data);
  const segs = useSegmentos();
  const [aba, setAba] = useState<string>("indicadores");
  const [salvar, setSalvar] = useState(false);
  const [conta, setConta] = useState(false);

  // análise salva aberta a partir de "Minhas análises": vale enquanto a seleção for a mesma
  const idParam = params.get("analise") ? Number(params.get("analise")) : null;
  const salva = salvas.data?.find((a) => a.id_analise === idParam);
  const mesmaSelecao =
    salva &&
    salva.regioes.length === regioes.length &&
    salva.regioes.every((r) => regioes.includes(r.id_regiao)) &&
    segs.data?.find((s) => s.id_categoria === segmento)?.nome === salva.segmento;

  const nada = segmento == null && regioes.length === 0;
  const podeSalvar = regioes.length >= 2 && segmento != null;

  return (
    <Tabs value={aba} onValueChange={setAba} className="flex h-full flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b border-nevoa bg-white px-3 py-2">
        <TabsList aria-label="Resultados">
          <TabsTrigger value="indicadores">
            <BarChart3 /> Indicadores
          </TabsTrigger>
          <TabsTrigger value="oferta">
            <Store /> Oferta
          </TabsTrigger>
          <TabsTrigger value="comparar">
            <Columns3 /> Comparar
          </TabsTrigger>
          <TabsTrigger value="analise">
            <Telescope /> Oferta x referência
          </TabsTrigger>
        </TabsList>
        <div className="ml-auto flex items-center gap-2">
          {mesmaSelecao && <span className="hidden text-[13px] text-tinta-suave md:inline">Análise salva: <strong className="text-marinho">{salva!.nome}</strong></span>}
          {!mesmaSelecao && (
            <Tooltip>
              <TooltipTrigger asChild>
                <span tabIndex={podeSalvar ? -1 : 0}>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={!podeSalvar}
                    onClick={() => (sessao.data ? setSalvar(true) : setConta(true))}
                  >
                    <Bookmark /> Salvar
                  </Button>
                </span>
              </TooltipTrigger>
              <TooltipContent>
                {podeSalvar ? (sessao.data ? "Preservar os dados e regras desta análise" : "Entre na sua conta para salvar") : "Escolha um segmento e ao menos dois bairros"}
              </TooltipContent>
            </Tooltip>
          )}
          <MenuExportar idAnalise={mesmaSelecao ? salva!.id_analise : undefined} />
        </div>
      </div>
      {mesmaSelecao && (
        <div className="border-b border-nevoa bg-ouro-claro/45 px-4 py-1.5 text-[12.5px] text-marinho" role="status">
          {salva!.snapshot_disponivel
            ? `Você está vendo o snapshot preservado de “${salva!.nome}” (${salva!.versao_metodologia}).`
            : `“${salva!.nome}” é uma análise legada sem snapshot; os resultados usam os dados atuais.`}
        </div>
      )}
      <div className="min-h-0 flex-1 overflow-y-auto bg-papel">
        {nada ? (
          <div className="flex h-full items-center">
            <PrimeirosPassos segmento={segmento != null} regioes={regioes.length} />
          </div>
        ) : (
          <>
            <TabsContent value="indicadores"><AbaIndicadores /></TabsContent>
            <TabsContent value="oferta"><AbaOferta /></TabsContent>
            <TabsContent value="comparar"><AbaComparar /></TabsContent>
            <TabsContent value="analise"><AbaAnalise /></TabsContent>
          </>
        )}
      </div>
      <DialogoSalvar aberto={salvar} aoMudar={setSalvar} />
      <DialogoConta aberto={conta} aoMudar={setConta} />
    </Tabs>
  );
}
