import { lazy, Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Cabecalho } from "@/components/Cabecalho";
import { Vazio } from "@/components/Vazio";
import { SelecaoProvider } from "@/lib/selecao";

const Inicio = lazy(() => import("@/paginas/Inicio").then((modulo) => ({ default: modulo.Inicio })));
const Explorar = lazy(() => import("@/paginas/Explorar").then((modulo) => ({ default: modulo.Explorar })));
const MinhasAnalises = lazy(() => import("@/paginas/MinhasAnalises").then((modulo) => ({ default: modulo.MinhasAnalises })));
const Infraestrutura = lazy(() => import("@/paginas/Infraestrutura").then((modulo) => ({ default: modulo.Infraestrutura })));

const cliente = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={cliente}>
      <BrowserRouter>
        <SelecaoProvider>
          <TooltipProvider delayDuration={200}>
            <Estrutura />
            <Toaster />
          </TooltipProvider>
        </SelecaoProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function Estrutura() {
  const local = useLocation();
  const entrada = local.pathname === "/";
  return (
    <div className="flex h-dvh flex-col">
              <a
                href="#conteudo-principal"
                className="fixed left-3 top-3 z-[2000] -translate-y-24 rounded-md bg-marinho px-4 py-2 text-sm font-semibold text-white shadow-lg transition-transform focus:translate-y-0"
              >
                Pular para o conteúdo
              </a>
              {!entrada && <Cabecalho />}
              <main id="conteudo-principal" tabIndex={-1} className="flex min-h-0 flex-1 flex-col overflow-x-hidden overflow-y-auto lg:overflow-hidden">
                <Suspense fallback={<CarregandoRota />}>
                  <Routes>
                    <Route path="/" element={<Inicio />} />
                    <Route path="/explorar" element={<Explorar />} />
                    <Route path="/analises" element={<div className="flex-1 overflow-y-auto"><MinhasAnalises /></div>} />
                    <Route path="/admin/infraestrutura" element={<div className="flex-1 overflow-y-auto"><Infraestrutura /></div>} />
                    <Route path="/infraestrutura" element={<Navigate to="/admin/infraestrutura" replace />} />
                    <Route
                      path="*"
                      element={
                        <Vazio titulo="Esta página não existe">
                          <Link to="/" className="font-semibold text-marinho underline">Voltar para o início</Link>
                        </Vazio>
                      }
                    />
                  </Routes>
                </Suspense>
              </main>
    </div>
  );
}

function CarregandoRota() {
  return (
    <div className="flex min-h-64 flex-1 items-center justify-center" role="status" aria-live="polite">
      <div className="flex items-center gap-3 text-sm font-semibold text-tinta-suave">
        <span className="size-2.5 animate-pulse rounded-full bg-ouro" aria-hidden />
        Carregando página…
      </div>
    </div>
  );
}
