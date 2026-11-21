// HU-004: filtros por segmento e região. A seleção aqui e no mapa é a mesma.
import { useState } from "react";
import { Check, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Command, CommandEmpty, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useRegioes, useSegmentos } from "@/hooks/dados";
import { num } from "@/lib/formato";
import { MAX_REGIOES, useSelecao, type CorMapa } from "@/lib/selecao";
import { cn } from "@/lib/utils";
import { IconeSegmento } from "./IconeSegmento";
import { Pino } from "./Marca";

function Bloco({ titulo, dica, children }: { titulo: string; dica?: string; children: React.ReactNode }) {
  return (
    <section className="px-5 py-4">
      <h2 className="semi-larga text-[15px] font-bold text-marinho">{titulo}</h2>
      {dica && <p className="mt-0.5 text-[13px] text-tinta-suave">{dica}</p>}
      <div className="mt-3">{children}</div>
    </section>
  );
}

export function PainelControles() {
  const { segmento, setSegmento, regioes, alternarRegiao, removerRegiao, limpar, cor, setCor } = useSelecao();
  const segmentos = useSegmentos();
  const todas = useRegioes();
  const [aberto, setAberto] = useState(false);
  const porId = new Map(todas.data?.map((r) => [r.id_regiao, r]));

  return (
    <div className="flex flex-col divide-y divide-nevoa">
      <div className="px-5 pb-1 pt-5">
        <h1 className="larga text-[24px] font-extrabold leading-tight text-marinho">Explore bairros do Recife</h1>
        <p className="mt-1 text-[13px] leading-relaxed text-tinta-suave">Compare dados locais antes de escolher onde abrir seu negócio.</p>
      </div>
      <Bloco titulo="O que você quer abrir?">
        {segmentos.isLoading ? (
          <div className="grid grid-cols-2 gap-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-[58px]" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Segmento de negócio">
            {segmentos.data?.map((s) => {
              const ativo = s.id_categoria === segmento;
              return (
                <button
                  key={s.id_categoria}
                  role="radio"
                  aria-checked={ativo}
                  onClick={() => setSegmento(ativo ? null : s.id_categoria)}
                  className={cn(
                    "group flex items-center gap-2 rounded-md border px-2.5 py-2.5 text-left transition-colors cursor-pointer",
                    ativo ? "border-marinho bg-marinho text-white" : "border-nevoa bg-white hover:border-marinho-3",
                  )}
                >
                  <IconeSegmento nome={s.nome} className={cn("size-[18px] shrink-0", ativo ? "text-ouro" : "text-marinho-3")} />
                  <span className="min-w-0">
                    <span className="block truncate text-[13.5px] font-semibold leading-tight">{s.nome}</span>
                    <span className={cn("block text-[11.5px] leading-tight numeros", ativo ? "text-white/70" : "text-tinta-fraca")}>
                      {num(s.total_estabelecimentos)} registros formais
                    </span>
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </Bloco>

      <Bloco titulo="Onde?" dica={regioes.length ? undefined : "Clique nos bairros do mapa ou procure pelo nome."}>
        {regioes.length > 0 && (
          <ul className="mb-3 flex flex-wrap gap-1.5" aria-label="Bairros escolhidos">
            {regioes.map((id) => (
              <li key={id}>
                <button
                  onClick={() => removerRegiao(id)}
                  className="group flex min-h-9 items-center gap-1.5 rounded-full bg-ouro-claro py-1 pl-2 pr-3 text-[13px] font-semibold text-marinho hover:bg-ouro/45 cursor-pointer"
                  aria-label={`Tirar ${porId.get(id)?.nome ?? "bairro"} da seleção`}
                >
                  <Pino tamanho={12} />
                  {porId.get(id)?.nome ?? "…"}
                  <X className="size-3 text-marinho/50 group-hover:text-marinho" />
                </button>
              </li>
            ))}
          </ul>
        )}
        <div className="flex items-center gap-2">
          <Popover open={aberto} onOpenChange={setAberto}>
            <PopoverTrigger asChild>
              <Button variant="outline" className="flex-1 justify-start text-tinta-suave" disabled={!todas.data}>
                <Plus /> Procurar bairro
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[290px] p-0">
              <Command
                filter={(valor, busca) =>
                  valor.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase().includes(busca.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase()) ? 1 : 0
                }
              >
                <CommandInput placeholder="Boa Viagem, Casa Forte..." />
                <CommandList>
                  <CommandEmpty>Nenhum bairro com esse nome.</CommandEmpty>
                  {todas.data?.map((r) => {
                    const marcado = regioes.includes(r.id_regiao);
                    return (
                      <CommandItem key={r.id_regiao} value={r.nome} onSelect={() => alternarRegiao(r.id_regiao)}>
                        <Check className={cn("size-4", marcado ? "text-marinho" : "text-transparent")} />
                        <span className="flex-1">{r.nome}</span>
                        <span className="text-xs text-tinta-fraca numeros">{num(r.populacao)} hab.</span>
                      </CommandItem>
                    );
                  })}
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
          {regioes.length > 0 && (
            <Button variant="ghost" size="sm" onClick={limpar}>
              Limpar
            </Button>
          )}
        </div>
        <p className="mt-2 text-[12px] text-tinta-fraca numeros">
          {regioes.length} de {MAX_REGIOES} bairros
        </p>
      </Bloco>

      <Bloco titulo="Pintar o mapa por">
        <ToggleGroup type="single" value={cor} onValueChange={(v) => v && setCor(v as CorMapa)} aria-label="Cor do mapa">
          <ToggleGroupItem value="populacao">Moradores</ToggleGroupItem>
          <ToggleGroupItem value="renda">Renda</ToggleGroupItem>
          <ToggleGroupItem value="oferta" disabled={segmento == null} title={segmento == null ? "Escolha um segmento antes" : undefined}>
            Oferta
          </ToggleGroupItem>
        </ToggleGroup>
      </Bloco>
    </div>
  );
}
