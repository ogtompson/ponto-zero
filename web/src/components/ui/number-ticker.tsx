// Componente do registro 21st.dev (Magic UI): https://21st.dev/r/dillionverma/number-ticker
// Adaptado: formato brasileiro (pt-BR) e respeito a "reduzir movimento".
import { useEffect, useRef, type ComponentPropsWithoutRef } from "react";
import { useInView, useMotionValue, useReducedMotion, useSpring } from "framer-motion";
import { cn } from "@/lib/utils";

interface NumberTickerProps extends ComponentPropsWithoutRef<"span"> {
  value: number;
  startValue?: number;
  delay?: number;
  decimalPlaces?: number;
}

export function NumberTicker({ value, startValue = 0, delay = 0, className, decimalPlaces = 0, ...props }: NumberTickerProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const reduzir = useReducedMotion();
  const motionValue = useMotionValue(startValue);
  const springValue = useSpring(motionValue, { damping: 60, stiffness: 140 });
  const isInView = useInView(ref, { once: true, margin: "0px" });
  const formato = new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: decimalPlaces,
    maximumFractionDigits: decimalPlaces,
  });

  useEffect(() => {
    if (reduzir && ref.current) {
      ref.current.textContent = formato.format(value);
      return;
    }
    if (isInView) {
      const timer = setTimeout(() => motionValue.set(value), delay * 1000);
      return () => clearTimeout(timer);
    }
  }, [motionValue, isInView, delay, value, reduzir]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(
    () =>
      springValue.on("change", (latest) => {
        // a mola para "quase" no alvo; perto do fim mostramos o valor exato
        const exibido = Math.abs(latest - value) < 0.5 ? value : latest;
        if (ref.current) ref.current.textContent = formato.format(Number(exibido.toFixed(decimalPlaces)));
      }),
    [springValue, decimalPlaces, value], // eslint-disable-line react-hooks/exhaustive-deps
  );

  // quando a mola termina, garante o número exato
  useEffect(
    () =>
      springValue.on("animationComplete", () => {
        if (ref.current && motionValue.get() === value) ref.current.textContent = formato.format(value);
      }),
    [springValue, motionValue, value], // eslint-disable-line react-hooks/exhaustive-deps
  );

  return (
    <span ref={ref} className={cn("inline-block numeros", className)} {...props}>
      {formato.format(startValue)}
    </span>
  );
}
