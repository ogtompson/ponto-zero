// HU-010: exportar a análise exibida (PDF ou CSV). Fica indisponível sem análise na tela.
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Download, FileSpreadsheet, FileText } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { api } from "@/lib/api";
import { useSelecao } from "@/lib/selecao";

export function MenuExportar({ idAnalise }: { idAnalise?: number }) {
  const { segmento, regioes } = useSelecao();
  const qc = useQueryClient();
  const [gerando, setGerando] = useState(false);
  const pronto = segmento != null && regioes.length >= 2;

  async function exportar(formato: "PDF" | "CSV") {
    setGerando(true);
    try {
      const { blob, nome } = await api.baixar("/exportacoes", { segmento, regioes, formato, id_analise: idAnalise ?? null });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = nome;
      a.click();
      URL.revokeObjectURL(url);
      toast(`${formato} gerado`, { description: nome });
      if (idAnalise) qc.invalidateQueries({ queryKey: ["analises"] });
    } catch (e) {
      toast("Não foi possível gerar o arquivo", {
        description: e instanceof Error ? e.message : undefined,
        action: { label: "Tentar de novo", onClick: () => exportar(formato) },
      });
    } finally {
      setGerando(false);
    }
  }

  const botao = (
    <Button variant="outline" size="sm" disabled={!pronto || gerando}>
      <Download /> {gerando ? "Gerando…" : "Exportar"}
    </Button>
  );

  if (!pronto)
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <span tabIndex={0}>{botao}</span>
        </TooltipTrigger>
        <TooltipContent>Para exportar, escolha um segmento e ao menos dois bairros.</TooltipContent>
      </Tooltip>
    );

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>{botao}</DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>Comparação, análise, fontes e avisos</DropdownMenuLabel>
        <DropdownMenuItem onSelect={() => exportar("PDF")}>
          <FileText /> Relatório em PDF
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => exportar("CSV")}>
          <FileSpreadsheet /> Planilha CSV
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
