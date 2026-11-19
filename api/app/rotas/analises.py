"""Análises salvas com o estado territorial congelado no momento da criação."""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from psycopg.types.json import Jsonb

from ..config import METODOLOGIA_VERSAO, config
from ..db import conexao, consulta
from ..seguranca import usuario_obrigatorio
from ..servicos.territorio import (
    analise as calcular_analise,
    chave_ordem,
    comparacao,
    erro,
    indicadores,
    oferta,
    regioes_validas,
    segmento_valido,
)

router = APIRouter(prefix="/analises", tags=["análises salvas"])


class NovaAnalise(BaseModel):
    nome: str = ""
    objetivo: str | None = None
    segmento: int | None = None
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
        if l.get("capturado_em"):
            l["capturado_em"] = l["capturado_em"].isoformat()
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
    ids = list(dict.fromkeys(dados.regioes))
    regioes_validas(ids, 2, "Selecione ao menos duas regiões para salvar a análise.")
    segmento = segmento_valido(dados.segmento)
    capturado_em = datetime.now(config.fuso)
    snapshot = {
        "schema_version": 1,
        "methodology_version": METODOLOGIA_VERSAO,
        "captured_at": capturado_em.isoformat(),
        "selection": {"segmento": segmento, "regioes": ids},
        "indicadores": indicadores(ids),
        "oferta": oferta(segmento["id_categoria"], ids),
        "comparacao": comparacao(segmento["id_categoria"], ids),
        "analise": calcular_analise(segmento["id_categoria"], ids),
    }

    with conexao() as conn:
        id_analise = conn.execute(
            """
            INSERT INTO analise
                (nome, data_criacao, objetivo, id_categoria, versao_metodologia, capturado_em, snapshot, id_empresa)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_analise
            """,
            (
                nome[:100],
                _hoje(),
                (dados.objetivo or "").strip() or None,
                segmento["id_categoria"],
                METODOLOGIA_VERSAO,
                capturado_em,
                Jsonb(snapshot),
                usuario["id_empresa"],
            ),
        ).fetchone()["id_analise"]
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO regiao_analise (id_analise, id_regiao) VALUES (%s, %s)",
                [(id_analise, r) for r in ids],
            )
    return obter(id_analise, usuario)


@router.get("/{id_analise}", summary="Detalhe de uma análise")
def obter(id_analise: int, usuario: dict = Depends(usuario_obrigatorio)):
    linhas = consulta(
        """
        SELECT v.*, a.snapshot
        FROM vw_resumo_analise v JOIN analise a USING (id_analise)
        WHERE v.id_analise = %s AND v.id_empresa = %s
        """,
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
