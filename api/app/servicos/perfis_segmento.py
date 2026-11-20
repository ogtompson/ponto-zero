"""Perfis analíticos versionados dos segmentos atendidos pelo PontoZero.

O catálogo separa disponibilidade de profundidade metodológica. Um segmento pode
estar visível no produto sem que o sistema finja possuir dados suficientes para
diagnosticá-lo.
"""

from __future__ import annotations

from copy import deepcopy


VERSAO_CATALOGO = "2026.11.1"

_PERFIS = (
    {
        "slug": "farmacia",
        "nome": "Farmácia",
        "maturidade": "especializado",
        "disponibilidade": "piloto",
        "direcionadores": ["população residente", "pessoas com 60 anos ou mais", "renda", "oferta formal"],
        "area_influencia": {"modo": "caminhada", "minutos": 15},
        "cnaes_diretos": ["4771-7/01", "4771-7/02", "4771-7/03"],
    },
    {
        "slug": "cafeteria",
        "nome": "Cafeteria",
        "maturidade": "configurado",
        "disponibilidade": "piloto",
        "direcionadores": ["renda", "polos de trabalho e estudo", "fluxo diurno", "oferta próxima"],
        "area_influencia": {"modo": "caminhada", "minutos": 10},
    },
    {
        "slug": "academia",
        "nome": "Academia",
        "maturidade": "configurado",
        "disponibilidade": "piloto",
        "direcionadores": ["densidade residencial", "perfil etário", "renda", "concorrência próxima"],
        "area_influencia": {"modo": "deslocamento", "minutos": 15},
    },
    {
        "slug": "supermercado",
        "nome": "Supermercado",
        "maturidade": "configurado",
        "disponibilidade": "piloto",
        "direcionadores": ["domicílios", "renda", "acesso viário", "porte da oferta"],
        "area_influencia": {"modo": "deslocamento", "minutos": 15},
    },
    {
        "slug": "padaria",
        "nome": "Padaria",
        "maturidade": "configurado",
        "disponibilidade": "piloto",
        "direcionadores": ["domicílios", "densidade residencial", "renda", "oferta de conveniência"],
        "area_influencia": {"modo": "caminhada", "minutos": 10},
    },
    {
        "slug": "pet-shop",
        "nome": "Pet shop",
        "maturidade": "configurado",
        "disponibilidade": "piloto",
        "direcionadores": ["domicílios", "renda", "serviços complementares", "oferta próxima"],
        "area_influencia": {"modo": "deslocamento", "minutos": 15},
    },
    {
        "slug": "restaurante",
        "nome": "Restaurante e lanchonete",
        "maturidade": "geral",
        "disponibilidade": "preparacao",
        "direcionadores": ["fluxo por período", "trabalho e estudo", "renda", "oferta por ocasião"],
        "area_influencia": {"modo": "caminhada", "minutos": 15},
    },
    {
        "slug": "beleza",
        "nome": "Salão de beleza e barbearia",
        "maturidade": "geral",
        "disponibilidade": "preparacao",
        "direcionadores": ["população residente", "perfil do público", "renda", "recorrência"],
        "area_influencia": {"modo": "deslocamento", "minutos": 15},
    },
    {
        "slug": "clinica",
        "nome": "Clínica e consultório",
        "maturidade": "geral",
        "disponibilidade": "preparacao",
        "direcionadores": ["perfil etário", "renda", "acessibilidade", "polos de saúde"],
        "area_influencia": {"modo": "deslocamento", "minutos": 20},
    },
    {
        "slug": "educacao",
        "nome": "Escola e curso",
        "maturidade": "geral",
        "disponibilidade": "preparacao",
        "direcionadores": ["faixa etária", "domicílios", "renda", "acessibilidade"],
        "area_influencia": {"modo": "deslocamento", "minutos": 20},
    },
    {
        "slug": "moda",
        "nome": "Roupas e calçados",
        "maturidade": "geral",
        "disponibilidade": "preparacao",
        "direcionadores": ["renda", "fluxo comercial", "centralidade", "oferta complementar"],
        "area_influencia": {"modo": "deslocamento", "minutos": 20},
    },
)

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
