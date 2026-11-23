import { useState } from "react";
import { ChevronsDown, ChevronsUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Mapa } from "@/components/Mapa";
import { PainelControles } from "@/components/PainelControles";
import { PainelResultados } from "@/components/PainelResultados";
import { cn } from "@/lib/utils";

export function Explorar() {
  const [resultadosGrandes, setResultadosGrandes] = useState(false);

  return (
    <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
      <aside className="flex shrink-0 flex-col border-nevoa bg-white lg:w-[340px] lg:border-r lg:overflow-y-auto">
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
          className={cn("relative min-h-[320px] transition-[flex-basis] duration-300", resultadosGrandes ? "basis-[30%]" : "basis-[56%]")}
        >
          <Mapa />
          <Button
            variant="outline"
            size="sm"
            className="absolute bottom-3 right-3 z-[500] shadow-sm"
            onClick={() => setResultadosGrandes((v) => !v)}
            aria-pressed={resultadosGrandes}
          >
            {resultadosGrandes ? <ChevronsDown /> : <ChevronsUp />}
            {resultadosGrandes ? "Mais mapa" : "Mais resultados"}
          </Button>
        </section>
        <section aria-label="Resultados" className="min-h-[340px] flex-1 border-t border-nevoa">
          <PainelResultados />
        </section>
      </div>
    </div>
  );
}
