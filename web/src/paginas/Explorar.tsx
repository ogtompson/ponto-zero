import { useState } from "react";
import { ChevronsDown, ChevronsUp, Map, SlidersHorizontal, Telescope } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Mapa } from "@/components/Mapa";
import { PainelControles } from "@/components/PainelControles";
import { PainelResultados } from "@/components/PainelResultados";
import { cn } from "@/lib/utils";

export function Explorar() {
  const [resultadosGrandes, setResultadosGrandes] = useState(false);
  const [params, setParams] = useSearchParams();
  const vistaParam = params.get("vista");
  const vista = vistaParam === "mapa" || vistaParam === "resultados" ? vistaParam : "configurar";

  const mudarVista = (proxima: "configurar" | "mapa" | "resultados") => {
    setParams((atuais) => {
      const novos = new URLSearchParams(atuais);
      if (proxima === "configurar") novos.delete("vista");
      else novos.set("vista", proxima);
      return novos;
    }, { replace: true });
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <nav className="grid shrink-0 grid-cols-3 border-b border-nevoa bg-white p-1.5 lg:hidden" aria-label="Etapas da exploração">
        <BotaoVista ativo={vista === "configurar"} onClick={() => mudarVista("configurar")} icone={<SlidersHorizontal />}>
          Configurar
        </BotaoVista>
        <BotaoVista ativo={vista === "mapa"} onClick={() => mudarVista("mapa")} icone={<Map />}>
          Mapa
        </BotaoVista>
        <BotaoVista ativo={vista === "resultados"} onClick={() => mudarVista("resultados")} icone={<Telescope />}>
          Leitura
        </BotaoVista>
      </nav>
      <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
      <aside className={cn("min-h-0 shrink-0 flex-col overflow-y-auto border-nevoa bg-white lg:flex lg:w-[340px] lg:border-r", vista === "configurar" ? "flex" : "hidden")}>
        <PainelControles />
        <footer className="mt-auto hidden border-t border-nevoa px-5 py-4 lg:block">
          <p className="text-[11.5px] leading-snug text-tinta-fraca">
            Dados territoriais do IBGE e da Prefeitura do Recife. Fontes, datas e limitações acompanham cada análise.
          </p>
        </footer>
      </aside>
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <section
          aria-label="Mapa dos bairros do Recife"
          className={cn(
            "relative min-h-0 flex-1 transition-[flex-basis] duration-300 lg:flex-none",
            vista === "mapa" ? "block" : "hidden lg:block",
            resultadosGrandes ? "lg:basis-[30%]" : "lg:basis-[56%]",
          )}
        >
          <Mapa />
          <Button
            variant="outline"
            size="sm"
            className="absolute bottom-3 right-3 z-[500] hidden shadow-sm lg:inline-flex"
            onClick={() => setResultadosGrandes((v) => !v)}
            aria-pressed={resultadosGrandes}
          >
            {resultadosGrandes ? <ChevronsDown /> : <ChevronsUp />}
            {resultadosGrandes ? "Mais mapa" : "Mais resultados"}
          </Button>
        </section>
        <section aria-label="Resultados" className={cn("min-h-0 flex-1 border-t border-nevoa lg:block lg:min-h-[340px]", vista === "resultados" ? "block" : "hidden")}>
          <PainelResultados />
        </section>
      </div>
      </div>
    </div>
  );
}

function BotaoVista({ ativo, onClick, icone, children }: { ativo: boolean; onClick: () => void; icone: React.ReactNode; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={ativo ? "page" : undefined}
      className={cn(
        "flex min-h-11 items-center justify-center gap-1.5 rounded-md px-2 text-[13px] font-semibold transition-colors [&_svg]:size-4",
        ativo ? "bg-marinho text-white" : "text-tinta-suave hover:bg-secondary hover:text-marinho",
      )}
    >
      {icone}
      {children}
    </button>
  );
}
