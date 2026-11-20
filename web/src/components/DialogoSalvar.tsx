import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useRegioes, useSegmentos } from "@/hooks/dados";
import { api, ErroApi, type AnaliseSalva } from "@/lib/api";
import { useSelecao } from "@/lib/selecao";

export function DialogoSalvar({ aberto, aoMudar }: { aberto: boolean; aoMudar: (v: boolean) => void }) {
  const { segmento, regioes } = useSelecao();
  const segs = useSegmentos();
  const todas = useRegioes();
  const qc = useQueryClient();
  const navegar = useNavigate();
  const [, setParams] = useSearchParams();
  const [erro, setErro] = useState<string | null>(null);
  const nomeSeg = segs.data?.find((s) => s.id_categoria === segmento)?.nome;
  const nomes = regioes.map((id) => todas.data?.find((r) => r.id_regiao === id)?.nome).filter(Boolean);

  const salvar = useMutation({
    mutationFn: (dados: { nome: string; objetivo: string }) =>
      api.post<AnaliseSalva>("/analises", { ...dados, segmento, regioes }),
    onSuccess: (a) => {
      // a seleção atual passa a ser esta análise salva: exportar agora registra em RELATORIO
      setParams(
        (atual) => {
          const p = new URLSearchParams(atual);
          p.set("analise", String(a.id_analise));
          return p;
        },
        { replace: true },
      );
      qc.invalidateQueries({ queryKey: ["analises"] });
      qc.invalidateQueries({ queryKey: ["sessao"] });
      aoMudar(false);
      toast("Análise salva", {
        description: a.nome,
        action: { label: "Ver análises", onClick: () => navegar("/analises") },
      });
    },
    onError: (e) => setErro(e instanceof ErroApi ? e.message : "Não foi possível salvar."),
  });

  return (
    <Dialog open={aberto} onOpenChange={(v) => { setErro(null); aoMudar(v); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Salvar análise</DialogTitle>
          <DialogDescription>
            {nomeSeg ? `${nomeSeg} em ` : ""}
            {nomes.join(", ")}. Os dados, fontes e regras deste momento serão preservados.
          </DialogDescription>
        </DialogHeader>
        <form
          noValidate
          className="flex flex-col gap-3.5"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            const nome = String(f.get("nome") ?? "").trim();
            if (!nome) return setErro("Dê um nome para a análise.");
            salvar.mutate({ nome, objetivo: String(f.get("objetivo") ?? "") });
          }}
        >
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="nome-analise">Nome</Label>
            <Input id="nome-analise" name="nome" maxLength={100} placeholder="Ex.: Zona Sul antes da visita de campo" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="objetivo">Objetivo</Label>
            <Textarea id="objetivo" name="objetivo" placeholder="Opcional. O que você quer decidir com esta análise?" />
          </div>
          {erro && <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">{erro}</p>}
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => aoMudar(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={salvar.isPending}>
              {salvar.isPending ? "Salvando..." : "Salvar análise"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
