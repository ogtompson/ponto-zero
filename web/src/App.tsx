import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Cabecalho } from "@/components/Cabecalho";
import { Vazio } from "@/components/Vazio";
import { SelecaoProvider } from "@/lib/selecao";
import { Explorar } from "@/paginas/Explorar";
import { Infraestrutura } from "@/paginas/Infraestrutura";
import { MinhasAnalises } from "@/paginas/MinhasAnalises";

const cliente = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={cliente}>
      <BrowserRouter>
        <SelecaoProvider>
          <TooltipProvider delayDuration={200}>
            <div className="flex h-dvh flex-col">
              <Cabecalho />
              <div className="flex min-h-0 flex-1 flex-col overflow-y-auto lg:overflow-hidden">
                <Routes>
                  <Route path="/" element={<Explorar />} />
                  <Route path="/analises" element={<div className="flex-1 overflow-y-auto"><MinhasAnalises /></div>} />
                  <Route path="/infraestrutura" element={<div className="flex-1 overflow-y-auto"><Infraestrutura /></div>} />
                  <Route
                    path="*"
                    element={
                      <Vazio titulo="Esta página não existe">
                        <Link to="/" className="font-semibold text-marinho underline">Voltar para o mapa</Link>
                      </Vazio>
                    }
                  />
                </Routes>
              </div>
            </div>
            <Toaster />
          </TooltipProvider>
        </SelecaoProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
