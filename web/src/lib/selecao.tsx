// Estado da exploração (segmento, bairros escolhidos e cor do mapa), guardado na URL.
// Assim o botão voltar funciona e dá para mandar o link de uma comparação para alguém.
import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";

export const MAX_REGIOES = 8;
export type CorMapa = "populacao" | "renda" | "oferta";

type Selecao = {
  segmento: number | null;
  regioes: number[];
  cor: CorMapa;
  setSegmento: (id: number | null) => void;
  alternarRegiao: (id: number) => void;
  removerRegiao: (id: number) => void;
  definir: (segmento: number | null, regioes: number[]) => void;
  limpar: () => void;
  setCor: (c: CorMapa) => void;
};

const Contexto = createContext<Selecao | null>(null);

export function SelecaoProvider({ children }: { children: ReactNode }) {
  const [params, setParams] = useSearchParams();

  const segmento = params.get("segmento") ? Number(params.get("segmento")) : null;
  const regioes = useMemo(
    () => (params.get("bairros") ?? "").split(",").filter(Boolean).map(Number).filter((n) => !Number.isNaN(n)),
    [params],
  );
  const cor = (params.get("cor") as CorMapa) || (segmento ? "oferta" : "populacao");

  const atualizar = useCallback(
    (mudar: (p: URLSearchParams) => void) => {
      setParams(
        (atual) => {
          const p = new URLSearchParams(atual);
          mudar(p);
          return p;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  const valor = useMemo<Selecao>(
    () => ({
      segmento,
      regioes,
      cor,
      setSegmento: (id) =>
        atualizar((p) => {
          if (id == null) p.delete("segmento");
          else p.set("segmento", String(id));
          if (id == null && p.get("cor") === "oferta") p.delete("cor");
        }),
      alternarRegiao: (id) =>
        atualizar((p) => {
          const atual = (p.get("bairros") ?? "").split(",").filter(Boolean).map(Number);
          let novo: number[];
          if (atual.includes(id)) novo = atual.filter((x) => x !== id);
          else if (atual.length >= MAX_REGIOES) {
            toast(`Dá para comparar até ${MAX_REGIOES} bairros por vez.`, {
              description: "Tire um bairro da seleção para incluir outro.",
            });
            return;
          } else novo = [...atual, id];
          if (novo.length) p.set("bairros", novo.join(","));
          else p.delete("bairros");
        }),
      removerRegiao: (id) =>
        atualizar((p) => {
          const novo = (p.get("bairros") ?? "").split(",").filter(Boolean).map(Number).filter((x) => x !== id);
          if (novo.length) p.set("bairros", novo.join(","));
          else p.delete("bairros");
        }),
      definir: (seg, regs) =>
        atualizar((p) => {
          if (seg == null) p.delete("segmento");
          else p.set("segmento", String(seg));
          if (regs.length) p.set("bairros", regs.slice(0, MAX_REGIOES).join(","));
          else p.delete("bairros");
        }),
      limpar: () => atualizar((p) => p.delete("bairros")),
      setCor: (c) => atualizar((p) => p.set("cor", c)),
    }),
    [segmento, regioes, cor, atualizar],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useSelecao() {
  const ctx = useContext(Contexto);
  if (!ctx) throw new Error("useSelecao fora do SelecaoProvider");
  return ctx;
}
