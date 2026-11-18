import { Coffee, Croissant, Dumbbell, PawPrint, Pill, ShoppingCart, Store, type LucideProps } from "lucide-react";

const ICONES: Record<string, React.ComponentType<LucideProps>> = {
  Farmácia: Pill,
  Supermercado: ShoppingCart,
  Padaria: Croissant,
  Cafeteria: Coffee,
  Academia: Dumbbell,
  "Pet shop": PawPrint,
};

export function IconeSegmento({ nome, ...props }: { nome: string } & LucideProps) {
  const Icone = ICONES[nome] ?? Store;
  return <Icone aria-hidden {...props} />;
}
