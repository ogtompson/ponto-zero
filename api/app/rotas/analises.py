"""Análises salvas da empresa (ANALISE + REGIAO_ANALISE + RELATORIO).

No modelo da equipe, a análise pertence à EMPRESA e o segmento analisado é o
segmento da própria empresa (empresa.segmento). Por isso a análise é salva
para o segmento da empresa do usuário.
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..config import config
from ..db import conexao, consulta
from ..seguranca import usuario_obrigatorio
from ..servicos.territorio import chave_ordem, erro, regioes_validas

router = APIRouter(prefix="/analises", tags=["análises salvas"])


class NovaAnalise(BaseModel):
    nome: str = ""
    objetivo: str | None = None
    segmento: str | None = None
    regioes: list[int] = []


def _hoje():
    return datetime.now(config.fuso).date()


def _detalhar(linhas: list[dict]) -> list[dict]:
    if not linhas:
        return []
    ids = [l["id_analise"] for l in linhas]
    regs = consulta(
        """
        SELECT ra.id_analise, r.id_regiao, r.nome
        FROM regiao_analise ra JOIN regiao r ON r.id_regiao = ra.id_regiao
        WHERE ra.id_analise = ANY(%s)
        """,
        (ids,),
    )
    rels = consulta(
        """
        SELECT id_relatorio, id_analise, data_geracao, formato
        FROM relatorio WHERE id_analise = ANY(%s)
        ORDER BY data_geracao DESC, id_relatorio DESC
        """,
        (ids,),
    )
    for l in linhas:
        l["regioes"] = sorted(
            ({"id_regiao": r["id_regiao"], "nome": r["nome"]} for r in regs if r["id_analise"] == l["id_analise"]),
            key=lambda r: chave_ordem(r["nome"]),
        )
        l["relatorios"] = [
            {"id_relatorio": r["id_relatorio"], "data_geracao": r["data_geracao"].isoformat(), "formato": r["formato"]}
            for r in rels
            if r["id_analise"] == l["id_analise"]
        ]
        l["data_criacao"] = l["data_criacao"].isoformat()
        if l.get("ultimo_relatorio"):
            l["ultimo_relatorio"] = l["ultimo_relatorio"].isoformat()
    return linhas


@router.get("", summary="Análises da minha empresa")
def listar(usuario: dict = Depends(usuario_obrigatorio)):
    linhas = consulta(
        "SELECT * FROM vw_resumo_analise WHERE id_empresa = %s ORDER BY data_criacao DESC, id_analise DESC",
        (usuario["id_empresa"],),
    )
    return _detalhar(linhas)


@router.post("", status_code=201, summary="Salvar análise")
def criar(dados: NovaAnalise, usuario: dict = Depends(usuario_obrigatorio)):
    nome = dados.nome.strip()
    if not nome:
        raise erro(422, "Dê um nome para a análise.", "nome")
    regioes_validas(dados.regioes, 1, "Selecione ao menos uma região para salvar a análise.")

    segmento_empresa = usuario["segmento"]
    segmento_pedido = (dados.segmento or "").strip() or None
    if segmento_pedido and not consulta("SELECT 1 FROM categoria WHERE nome = %s", (segmento_pedido,)):
        raise erro(422, "Segmento desconhecido.", "segmento")
    if segmento_empresa and segmento_pedido and segmento_pedido != segmento_empresa:
        raise erro(
            409,
            f"Sua empresa está cadastrada no segmento {segmento_empresa}. "
            f"Troque o segmento para {segmento_empresa} para salvar esta análise.",
            "segmento",
        )

    with conexao() as conn:
        if not segmento_empresa and segmento_pedido:
            conn.execute(
                "UPDATE empresa SET segmento = %s WHERE id_empresa = %s",
                (segmento_pedido, usuario["id_empresa"]),
            )
        id_analise = conn.execute(
            """
            INSERT INTO analise (nome, data_criacao, objetivo, id_empresa)
            VALUES (%s, %s, %s, %s) RETURNING id_analise
            """,
            (nome[:100], _hoje(), (dados.objetivo or "").strip() or None, usuario["id_empresa"]),
        ).fetchone()["id_analise"]
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO regiao_analise (id_analise, id_regiao) VALUES (%s, %s)",
                [(id_analise, r) for r in dict.fromkeys(dados.regioes)],
            )
    return obter(id_analise, usuario)


@router.get("/{id_analise}", summary="Detalhe de uma análise")
def obter(id_analise: int, usuario: dict = Depends(usuario_obrigatorio)):
    linhas = consulta(
        "SELECT * FROM vw_resumo_analise WHERE id_analise = %s AND id_empresa = %s",
        (id_analise, usuario["id_empresa"]),
    )
    if not linhas:
        raise erro(404, "Análise não encontrada.")
    return _detalhar(linhas)[0]


@router.delete("/{id_analise}", status_code=204, summary="Excluir análise")
def excluir(id_analise: int, usuario: dict = Depends(usuario_obrigatorio)):
    with conexao() as conn:
        apagadas = conn.execute(
            "DELETE FROM analise WHERE id_analise = %s AND id_empresa = %s",
            (id_analise, usuario["id_empresa"]),
        ).rowcount
    if not apagadas:
        raise erro(404, "Análise não encontrada.")
