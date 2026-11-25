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

const inteiroPositivo = (valor: string | null) => {
  if (valor == null || !/^\d+$/.test(valor)) return null;
  const numero = Number(valor);
  return Number.isSafeInteger(numero) && numero > 0 ? numero : null;
};

const idsValidos = (valor: string | null) =>
  [...new Set((valor ?? "").split(",").map(inteiroPositivo).filter((id): id is number => id != null))].slice(0, MAX_REGIOES);

export function SelecaoProvider({ children }: { children: ReactNode }) {
  const [params, setParams] = useSearchParams();

  const segmento = inteiroPositivo(params.get("segmento"));
  const regioes = useMemo(
    () => idsValidos(params.get("bairros")),
    [params],
  );
  const corParam = params.get("cor");
  const cor: CorMapa = corParam === "populacao" || corParam === "renda" || (corParam === "oferta" && segmento != null)
    ? corParam
    : segmento ? "oferta" : "populacao";

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
          const atual = idsValidos(p.get("bairros"));
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
          const novo = idsValidos(p.get("bairros")).filter((x) => x !== id);
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
