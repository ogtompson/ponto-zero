import { TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";

/** Avisos obrigatórios das histórias (aproximação, cobertura da fonte, não recomendação). */
export function Aviso({ children, forte = false, className }: { children: React.ReactNode; forte?: boolean; className?: string }) {
  return (
    <p
      role="note"
      className={cn(
        "flex items-start gap-2 text-[13px] leading-snug",
        forte ? "rounded-md border border-ouro/60 bg-ouro-claro/60 px-3 py-2 font-semibold text-marinho" : "text-tinta-suave",
        className,
      )}
    >
      <TriangleAlert className={cn("mt-0.5 size-3.5 shrink-0", forte ? "text-ouro-escuro" : "text-tinta-fraca")} aria-hidden />
      <span>{children}</span>
    </p>
  );
}
