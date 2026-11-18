// HU-007: fonte e data de referência consultáveis em qualquer tela.
import { Info } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { dataBr } from "@/lib/formato";
import { cn } from "@/lib/utils";

export function FonteInfo({
  fonte,
  data,
  rotulo,
  className,
}: {
  fonte: string | null;
  data: string | null;
  rotulo?: string;
  className?: string;
}) {
  if (!fonte) return null;
  return (
    <Popover>
      <PopoverTrigger
        className={cn("inline-flex size-6 items-center justify-center rounded-full text-tinta-fraca hover:bg-secondary hover:text-marinho cursor-pointer", className)}
        aria-label={`Fonte de ${rotulo ?? "dado"}`}
      >
        <Info className="size-3.5" />
      </PopoverTrigger>
      <PopoverContent className="w-64">
        <p className="text-xs text-tinta-suave">Fonte</p>
        <p className="font-semibold leading-snug">{fonte}</p>
        <p className="mt-2 text-xs text-tinta-suave">Data de referência</p>
        <p className={cn("leading-snug", !data && "italic text-tinta-suave")}>{dataBr(data)}</p>
      </PopoverContent>
    </Popover>
  );
}

export function ListaFontes({ fontes }: { fontes: { fonte: string; data_texto: string; usada_em: string[] }[] }) {
  return (
    <ul className="divide-y divide-nevoa">
      {fontes.map((f) => (
        <li key={f.fonte + f.data_texto} className="py-2.5">
          <p className="text-sm font-semibold leading-snug">{f.fonte}</p>
          <p className="text-xs text-tinta-suave">
            {/^\d{4}-/.test(f.data_texto) ? `Referência ${dataBr(f.data_texto)}` : f.data_texto}. Usada em {f.usada_em.join(", ").toLowerCase()}.
          </p>
        </li>
      ))}
    </ul>
  );
}
