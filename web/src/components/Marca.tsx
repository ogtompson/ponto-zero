import { cn } from "@/lib/utils";

export function LogoPontoZero({ claro = false, className }: { claro?: boolean; className?: string }) {
  return (
    <img
      src={claro ? "/marca/pontozero-branco.png" : "/marca/pontozero.png"}
      alt="PontoZero"
      width={407}
      height={216}
      className={cn("h-8 w-auto select-none", className)}
      draggable={false}
    />
  );
}

/** O pino da marca: usado para marcar os bairros escolhidos. */
export function Pino({ className, tamanho = 22 }: { className?: string; tamanho?: number }) {
  return (
    <svg viewBox="0 0 64 80" width={tamanho} height={(tamanho * 80) / 64} className={className} aria-hidden>
      <path
        d="M32 2C15.4 2 2 15.3 2 31.7c0 21.1 26.2 44.6 28.3 46.4a2.6 2.6 0 0 0 3.4 0C35.8 76.3 62 52.8 62 31.7 62 15.3 48.6 2 32 2Z"
        fill="#19214A"
      />
      <circle cx="32" cy="31" r="17" fill="#fff" />
      <circle cx="32" cy="31" r="11" fill="#DDBA43" />
    </svg>
  );
}

export const PINO_SVG =
  '<svg viewBox="0 0 64 80" width="26" height="33" xmlns="http://www.w3.org/2000/svg"><path d="M32 2C15.4 2 2 15.3 2 31.7c0 21.1 26.2 44.6 28.3 46.4a2.6 2.6 0 0 0 3.4 0C35.8 76.3 62 52.8 62 31.7 62 15.3 48.6 2 32 2Z" fill="#19214A" stroke="#fff" stroke-width="3"/><circle cx="32" cy="31" r="17" fill="#fff"/><circle cx="32" cy="31" r="11" fill="#DDBA43"/></svg>';
