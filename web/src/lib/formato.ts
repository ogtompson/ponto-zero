const n0 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const n1 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const n2 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const dataCurta = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeZone: "America/Recife" });

export const num = (v: number | null | undefined, casas = 0) =>
  v == null ? "indisponível" : casas === 2 ? n2.format(v) : casas === 1 ? n1.format(v) : n0.format(v);

/** Valor de indicador com unidade, do jeito que a pessoa lê. */
export function valorIndicador(valor: number | null, unidade: string): string {
  if (valor == null) return "indisponível";
  if (unidade === "R$ por mês") return `${moeda.format(valor)} por mês`;
  if (unidade === "pessoas") return `${n2.format(valor)} pessoas`;
  if (unidade === "km²") return `${n2.format(valor)} km²`;
  return `${n0.format(valor)} ${unidade}`;
}

/** Só o número, para colocar em destaque com a unidade ao lado. */
export function numeroIndicador(valor: number, unidade: string): { numero: number; casas: number; prefixo?: string; sufixo: string } {
  if (unidade === "R$ por mês") return { numero: valor, casas: 0, prefixo: "R$ ", sufixo: "por mês" };
  if (unidade === "pessoas" || unidade === "km²") return { numero: valor, casas: 2, sufixo: unidade };
  return { numero: valor, casas: 0, sufixo: unidade };
}

export function dataBr(iso: string | null | undefined): string {
  if (!iso) return "data de referência não informada";
  if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) {
    return dataCurta.format(new Date(`${iso}T12:00:00-03:00`));
  }
  return iso;
}

export function dataHora(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export function duracao(segundos: number): string {
  if (segundos < 60) return `${segundos} s`;
  const m = Math.floor(segundos / 60);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  return `${h} h ${m % 60} min`;
}
