// Componente do registro 21st.dev: https://21st.dev/r/shadcn/sonner
import { Toaster as Sonner } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = (props: ToasterProps) => (
  <Sonner
    position="bottom-center"
    toastOptions={{
      classNames: {
        toast: "!bg-marinho !text-white !border-0 !rounded-lg !font-sans !shadow-xl",
        description: "!text-white/75",
        actionButton: "!bg-ouro !text-marinho",
      },
    }}
    {...props}
  />
);

export { Toaster };
