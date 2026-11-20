from shapely.geometry import Polygon
from shapely.strtree import STRtree

from tools.coletar_empresas_recife import bairro_do_ponto, processar_segmento


def _territorio():
    bairros = [
        {"nome": "Bairro A", "chave": "bairro a", "geom": Polygon([(-35, -9), (-34, -9), (-34, -8), (-35, -8)])},
        {"nome": "Bairro B", "chave": "bairro b", "geom": Polygon([(-34, -9), (-33, -9), (-33, -8), (-34, -8)])},
    ]
    return bairros, STRtree([item["geom"] for item in bairros]), {"bairro a": 0, "bairro b": 1}


def test_coordenada_municipal_imprecisa_nao_vira_ponto():
    bairros, arvore, _ = _territorio()

    assert bairro_do_ponto(-8.1, -34.9, bairros, arvore) == (None, None, None)


def test_deduplica_cnpj_categoria_e_usa_bairro_declarado_sem_inventar_coordenada():
    bairros, arvore, por_nome = _territorio()
    perfil = {"nome": "Farmácia"}
    base = {
        "cnpj": "12345678000190",
        "razao_social": "Farmácia Exemplo Ltda",
        "nome_fantasia": ".",
        "nome_bairro": "Bairro B",
        "situacao_empresa": "ATIVO",
        "data_abertura_empresa": "2020-01-02T00:00:00",
        "latitude": -8.1,
        "longitude": -34.9,
        "nome_logradouro": "Rua Um",
        "numero_residencia": "10",
    }
    registros = [
        {**base, "cnae": 4771701, "atividade_principal": "S"},
        {**base, "cnae": 4771702, "atividade_principal": "N"},
    ]

    resultado, qualidade = processar_segmento(perfil, registros, bairros, arvore, por_nome)

    assert len(resultado) == 1
    assert resultado[0]["nome"] == "Farmácia Exemplo Ltda"
    assert resultado[0]["bairro"] == "Bairro B"
    assert resultado[0]["latitude"] is None
    assert resultado[0]["cnaes"] == [4771701, 4771702]
    assert qualidade["cnpjs_unicos"] == 1
    assert qualidade["associados_por_bairro_declarado"] == 1
    assert qualidade["coordenadas_precisas"] == 0
