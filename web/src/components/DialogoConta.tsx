// HU-001 (cadastro) e HU-002 (login). Ter conta é opcional: serve para salvar análises.
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, ErroApi, type Usuario } from "@/lib/api";

type Erros = Record<string, string>;

function Campo({
  id,
  rotulo,
  erro,
  dica,
  ...props
}: { id: string; rotulo: string; erro?: string; dica?: string } & React.ComponentProps<"input">) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{rotulo}</Label>
      <Input id={id} name={id} aria-invalid={!!erro} aria-describedby={erro ? `${id}-erro` : undefined} spellCheck={props.type === "email" ? false : props.spellCheck} {...props} />
      {erro ? (
        <p id={`${id}-erro`} role="alert" className="text-[12.5px] font-medium text-destructive">
          {erro}
        </p>
      ) : (
        dica && <p className="text-[12.5px] text-tinta-fraca">{dica}</p>
      )}
    </div>
  );
}

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function DialogoConta({ aberto, aoMudar, abaInicial = "entrar" }: { aberto: boolean; aoMudar: (v: boolean) => void; abaInicial?: "entrar" | "criar" }) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent>
        <FormularioConta abaInicial={abaInicial} aoConcluir={() => aoMudar(false)} />
      </DialogContent>
    </Dialog>
  );
}

export function FormularioConta({
  abaInicial = "entrar",
  aoConcluir,
  mostrarCabecalho = true,
}: {
  abaInicial?: "entrar" | "criar";
  aoConcluir?: (usuario: Usuario) => void;
  mostrarCabecalho?: boolean;
}) {
  const qc = useQueryClient();
  const [aba, setAba] = useState(abaInicial);
  const [erros, setErros] = useState<Erros>({});
  const [erroGeral, setErroGeral] = useState<string | null>(null);

  const sucesso = (u: Usuario, texto: string) => {
    qc.setQueryData(["sessao"], u);
    qc.invalidateQueries({ queryKey: ["analises"] });
    toast(texto, { description: u.empresa });
    setErros({});
    setErroGeral(null);
    aoConcluir?.(u);
  };

  const falha = (e: unknown) => {
    if (e instanceof ErroApi && e.campo) setErros({ [e.campo]: e.message });
    else setErroGeral(e instanceof Error ? e.message : "Algo deu errado.");
  };

  const entrar = useMutation({
    mutationFn: (dados: Record<string, string>) => api.post<Usuario>("/auth/login", dados),
    onSuccess: (u) => sucesso(u, `Olá, ${u.nome.split(" ")[0]}`),
    onError: falha,
  });

  const criar = useMutation({
    mutationFn: (dados: Record<string, string>) => api.post<Usuario>("/auth/cadastro", dados),
    onSuccess: (u) => sucesso(u, "Conta criada"),
    onError: falha,
  });

  function enviar(e: React.FormEvent<HTMLFormElement>, tipo: "entrar" | "criar") {
    e.preventDefault();
    const formulario = e.currentTarget;
    const dados = Object.fromEntries(new FormData(formulario)) as Record<string, string>;
    const novos: Erros = {};
    // RN: campos vazios bloqueiam o envio e apontam o campo
    if (tipo === "criar" && !dados.nome?.trim()) novos.nome = "Informe seu nome.";
    if (!dados.email?.trim()) novos.email = "Informe o e-mail.";
    else if (!EMAIL.test(dados.email.trim())) novos.email = "Digite um e-mail válido, como nome@empresa.com.";
    if (!dados.senha) novos.senha = "Informe a senha.";
    else if (tipo === "criar" && dados.senha.length < 8) novos.senha = "A senha precisa ter pelo menos 8 caracteres.";
    setErros(novos);
    setErroGeral(null);
    if (Object.keys(novos).length) {
      const primeiro = Object.keys(novos)[0];
      requestAnimationFrame(() => (formulario.elements.namedItem(primeiro) as HTMLElement | null)?.focus());
      return;
    }
    if (tipo === "entrar") entrar.mutate({ email: dados.email, senha: dados.senha });
    else criar.mutate(dados);
  }

  return (
    <div>
        {mostrarCabecalho && (
          <DialogHeader className="mb-4">
            <DialogTitle>{aba === "entrar" ? "Entrar" : "Criar conta"}</DialogTitle>
            <DialogDescription>Com uma conta, você salva análises e guarda o histórico de relatórios. Explorar o mapa não exige conta.</DialogDescription>
          </DialogHeader>
        )}
        <Tabs
          value={aba}
          onValueChange={(v) => {
            setAba(v as "entrar" | "criar");
            setErros({});
            setErroGeral(null);
          }}
        >
          <TabsList className="mb-4 w-full rounded-md bg-secondary p-1">
            <TabsTrigger value="entrar" className="h-8 flex-1">Entrar</TabsTrigger>
            <TabsTrigger value="criar" className="h-8 flex-1">Criar conta</TabsTrigger>
          </TabsList>
          <TabsContent value="entrar">
            <form noValidate onSubmit={(e) => enviar(e, "entrar")} className="flex flex-col gap-3.5">
              <Campo id="email" rotulo="E-mail" type="email" autoComplete="email" erro={erros.email} />
              <Campo id="senha" rotulo="Senha" type="password" autoComplete="current-password" erro={erros.senha} />
              {erroGeral && <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">{erroGeral}</p>}
              <Button type="submit" size="lg" disabled={entrar.isPending}>
                {entrar.isPending ? "Entrando…" : "Entrar"}
              </Button>
              <p className="text-center text-[12.5px] text-tinta-fraca">Conta de demonstração: demo@pontozero.app e senha pontozero2026</p>
            </form>
          </TabsContent>
          <TabsContent value="criar">
            <form noValidate onSubmit={(e) => enviar(e, "criar")} className="flex flex-col gap-3.5">
              <Campo id="nome" rotulo="Seu nome" autoComplete="name" erro={erros.nome} />
              <Campo id="email" rotulo="E-mail" type="email" autoComplete="email" erro={erros.email} />
              <Campo id="senha" rotulo="Senha" type="password" autoComplete="new-password" erro={erros.senha} dica="Pelo menos 8 caracteres." />
              {erroGeral && <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">{erroGeral}</p>}
              <Button type="submit" size="lg" disabled={criar.isPending}>
                {criar.isPending ? "Criando…" : "Criar conta"}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
    </div>
  );
}
