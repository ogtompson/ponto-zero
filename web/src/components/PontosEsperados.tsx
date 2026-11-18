// Visualização da HU-009: cada círculo vazado é um estabelecimento esperado pela média
// do Recife; cada ponto dourado é um estabelecimento encontrado. O nome do produto é
// literalmente "ponto": aqui ele vira unidade de medida.
import { cn } from "@/lib/utils";

const LIMITE = 24;

export function PontosEsperados({ esperado, encontrados }: { esperado: number | null; encontrados: number }) {
  if (esperado == null) return <div className="hachura h-6 w-full rounded" aria-hidden />;
  const maior = Math.max(Math.ceil(esperado), encontrados);
  const escala = maior > LIMITE ? Math.ceil(maior / LIMITE) : 1;
  const totalEsp = Math.round(esperado / escala);
  const totalEnc = Math.round(encontrados / escala);
  const total = Math.max(totalEsp, totalEnc);
  return (
    <div>
      <div className="flex flex-wrap gap-[5px]" role="img" aria-label={`${encontrados} encontrados para ${esperado.toLocaleString("pt-BR")} esperados`}>
        {Array.from({ length: total }).map((_, i) => {
          const achou = i < totalEnc;
          const esperadoAqui = i < totalEsp;
          return (
            <span
              key={i}
              className={cn(
                "size-3.5 rounded-full",
                achou && "bg-ouro ring-[1.5px] ring-marinho",
                !achou && esperadoAqui && "border-[1.5px] border-dashed border-marinho/45",
              )}
            />
          );
        })}
        {total === 0 && <span className="text-xs text-tinta-fraca">nenhum esperado nem encontrado</span>}
      </div>
      {escala > 1 && <p className="mt-1 text-[11px] text-tinta-fraca">cada círculo vale {escala} estabelecimentos</p>}
    </div>
  );
}
