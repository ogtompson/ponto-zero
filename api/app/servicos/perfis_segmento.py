"""Perfis analíticos versionados dos segmentos atendidos pelo PontoZero.

O catálogo separa disponibilidade de profundidade metodológica. Um segmento pode
estar visível no produto sem que o sistema finja possuir dados suficientes para
diagnosticá-lo.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


_ARQUIVO_CATALOGO = Path(__file__).resolve().parents[1] / "data" / "catalogo-segmentos.json"
_CATALOGO = json.loads(_ARQUIVO_CATALOGO.read_text(encoding="utf-8"))
VERSAO_CATALOGO = _CATALOGO["versao"]
_PERFIS = tuple(_CATALOGO["segmentos"])

for _perfil in _PERFIS:
    if "cnaes_oferta" in _perfil:
        _perfil["cnaes_diretos"] = [item["codigo"] for item in _perfil["cnaes_oferta"]]

_POR_NOME = {perfil["nome"].casefold(): perfil for perfil in _PERFIS}


def perfil_por_nome(nome: str) -> dict:
    """Retorna o perfil conhecido ou um perfil geral seguro."""
    perfil = _POR_NOME.get(nome.casefold())
    if perfil:
        return deepcopy(perfil)
    return {
        "slug": "personalizado",
        "nome": nome,
        "maturidade": "geral",
        "disponibilidade": "personalizado",
        "direcionadores": ["população", "domicílios", "renda", "oferta informada pelo usuário"],
        "area_influencia": None,
    }


def listar_perfis() -> dict:
    return {
        "versao": VERSAO_CATALOGO,
        "segmentos": deepcopy(list(_PERFIS)),
        "personalizado": {
            "disponibilidade": "personalizado",
            "maturidade": "geral",
            "descricao": "Leitura territorial inicial configurada com as informações do usuário.",
        },
        "niveis": {
            "especializado": "Metodologia específica estudada e documentada.",
            "configurado": "Direcionadores definidos, ainda sem validação profunda.",
            "geral": "Leitura territorial preliminar, sem conclusão específica do segmento.",
        },
    }
