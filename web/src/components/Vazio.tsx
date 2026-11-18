import { cn } from "@/lib/utils";

export function Vazio({ titulo, children, className }: { titulo: string; children?: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex h-full min-h-40 flex-col items-center justify-center px-6 py-8 text-center", className)}>
      <p className="semi-larga text-[17px] font-bold text-marinho">{titulo}</p>
      {children && <div className="mt-1.5 max-w-md text-sm text-tinta-suave">{children}</div>}
    </div>
  );
}

/** Primeira visita: o caminho em três passos (é uma sequência de verdade). */
export function PrimeirosPassos({ segmento, regioes }: { segmento: boolean; regioes: number }) {
  const passos = [
    { feito: segmento, texto: "Escolha o que você quer abrir" },
    { feito: regioes >= 2, texto: "Marque dois ou mais bairros no mapa" },
    { feito: false, texto: "Compare e veja onde a oferta parece menor" },
  ];
  return (
    <ol className="mx-auto flex max-w-3xl flex-col gap-3 px-6 py-8 sm:flex-row sm:gap-6">
      {passos.map((p, i) => (
        <li key={p.texto} className="flex flex-1 items-start gap-3">
          <span
            className={cn(
              "flex size-7 shrink-0 items-center justify-center rounded-full text-sm font-bold numeros",
              p.feito ? "bg-ouro text-marinho" : "border border-nevoa bg-white text-tinta-suave",
            )}
          >
            {i + 1}
          </span>
          <span className={cn("pt-0.5 text-[15px] leading-snug", p.feito ? "text-tinta-suave line-through decoration-ouro" : "text-marinho")}>
            {p.texto}
          </span>
        </li>
      ))}
    </ol>
  );
}
