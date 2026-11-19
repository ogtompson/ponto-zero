"""Exportar a análise exibida na tela (HU-010)."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from ..config import config
from ..db import conexao, consulta_um
from ..seguranca import usuario_opcional
from ..servicos import relatorio
from ..servicos.territorio import analise, chave_ordem, comparacao, erro

router = APIRouter(tags=["exportação"])


class PedidoExportacao(BaseModel):
    segmento: int | None = None
    regioes: list[int] = []
    formato: Literal["PDF", "CSV"] = "PDF"
    id_analise: int | None = None


@router.post("/exportacoes", summary="Gerar arquivo da análise (PDF ou CSV)")
def exportar(pedido: PedidoExportacao, usuario: dict | None = Depends(usuario_opcional)):
    salva = None
    if pedido.id_analise is not None:
        if usuario is None:
            raise erro(401, "Entre na sua conta para exportar esta análise salva.")
        salva = consulta_um(
            "SELECT snapshot FROM analise WHERE id_analise = %s AND id_empresa = %s",
            (pedido.id_analise, usuario["id_empresa"]),
        )
        if not salva:
            raise erro(404, "Análise salva não encontrada.")

    if salva and salva["snapshot"]:
        comp = salva["snapshot"]["comparacao"]
        anal = salva["snapshot"]["analise"]
    else:
        if pedido.segmento is None or len(pedido.regioes) < 2:
            raise erro(422, "Não há análise exibida para exportar. Escolha um segmento e ao menos duas regiões.")
        regioes = list(dict.fromkeys(pedido.regioes))
        comp = comparacao(pedido.segmento, regioes)
        anal = analise(pedido.segmento, regioes)

    try:
        if pedido.formato == "PDF":
            conteudo = relatorio.gerar_pdf(comp, anal, usuario)
            tipo, ext = "application/pdf", "pdf"
        else:
            conteudo = relatorio.gerar_csv(comp, anal)
            tipo, ext = "text/csv; charset=utf-8", "csv"
    except Exception as exc:  # noqa: BLE001 - mensagem clara para o usuário tentar de novo
        raise erro(500, "Não foi possível gerar o arquivo. Tente de novo.") from exc

    # Se a exportação veio de uma análise salva, registra em RELATORIO
    if pedido.id_analise is not None and salva:
        with conexao() as conn:
            conn.execute(
                "INSERT INTO relatorio (data_geracao, formato, id_analise) VALUES (%s, %s, %s)",
                (datetime.now(config.fuso).date(), pedido.formato, pedido.id_analise),
            )

    segmento = chave_ordem(anal["segmento"]["nome"]).replace(" ", "-")
    nome = f"pontozero-{segmento}-{datetime.now(config.fuso):%Y%m%d-%H%M}.{ext}"
    return Response(
        content=conteudo,
        media_type=tipo,
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
