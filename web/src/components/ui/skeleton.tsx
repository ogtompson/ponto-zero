// Componente do registro 21st.dev: https://21st.dev/r/shadcn/skeleton
import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded-md bg-[#e6e9f1]", className)} {...props} />;
}

export { Skeleton };
