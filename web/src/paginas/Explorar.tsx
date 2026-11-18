import { useState } from "react";
import { ChevronsDown, ChevronsUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LogoCesar } from "@/components/Marca";
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
        <footer className="mt-auto hidden items-center gap-3 border-t border-nevoa px-5 py-4 lg:flex">
          <LogoCesar className="h-9" />
          <p className="text-[11.5px] leading-snug text-tinta-fraca">
            Projeto acadêmico da CESAR School. Dados do IBGE, da Prefeitura do Recife e do OpenStreetMap. Interface com componentes do 21st.dev.
          </p>
        </footer>
      </aside>
      <main className="flex min-h-0 min-w-0 flex-1 flex-col">
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
      </main>
    </div>
  );
}
