from datetime import date

from app.servicos.diagnostico import faixa_percentil, montar_diagnostico, percentil_empirico


def _indicadores():
    linhas = []
    valores = {
        1: {"populacao": 1000, "domicilios": 400, "densidade": 5000, "renda_media_domiciliar": 1500, "area_km2": 0.2},
        2: {"populacao": 2000, "domicilios": 700, "densidade": 3000, "renda_media_domiciliar": 3000, "area_km2": 0.7},
        3: {"populacao": 3000, "domicilios": 1000, "densidade": 7000, "renda_media_domiciliar": 4500, "area_km2": 0.4},
    }
    for rid, indicadores in valores.items():
        for tipo, valor in indicadores.items():
            linhas.append({
                "id_regiao": rid,
                "tipo": tipo,
                "valor": valor,
                "fonte": "Fonte de teste",
                "data_referencia": date(2022, 7, 31),
            })
    return linhas


def _segmento():
    return {
        "id_categoria": 1,
        "nome": "Farmácia",
        "slug": "farmacia",
        "maturidade": "especializado",
        "disponibilidade": "piloto",
        "direcionadores": [],
        "area_influencia": {"modo": "caminhada", "minutos": 15},
    }


def test_percentil_e_faixa_sao_deterministicos():
    assert percentil_empirico(20, [10, 20, 30, None]) == 66.7
    assert faixa_percentil(66.7) == "intermediaria"
    assert faixa_percentil(67) == "alta"
    assert faixa_percentil(33) == "baixa"
    assert faixa_percentil(None) == "indisponivel"


def test_diagnostico_separa_dimensoes_e_nao_cria_score():
    resposta = montar_diagnostico(
        _segmento(),
        [{"id_regiao": 2, "nome": "Bairro B"}],
        _indicadores(),
        [
            {"id_regiao": 1, "quantidade": 1, "por_10k_hab": 10},
            {"id_regiao": 2, "quantidade": 2, "por_10k_hab": 10},
            {"id_regiao": 3, "quantidade": 6, "por_10k_hab": 20},
        ],
        {"fonte": "OpenStreetMap", "data_referencia": "2026-11-17", "cobertura": "parcial"},
    )

    assert resposta["sem_score"] is True
    assert "score" not in resposta
    dimensoes = {d["id"]: d for d in resposta["regioes"][0]["dimensoes"]}
    assert set(dimensoes) == {
        "demanda_residente", "perfil_publico", "oferta_local", "acesso_centralidade", "confianca_dados"
    }
    assert dimensoes["demanda_residente"]["status"] == "disponivel"
    assert dimensoes["perfil_publico"]["confianca"] == "aproximada"
    assert dimensoes["oferta_local"]["confianca"] == "aproximada"
    assert dimensoes["acesso_centralidade"]["status"] == "insuficiente"
    assert any("faixa etária" in texto for texto in dimensoes["perfil_publico"]["limitacoes"])
    sintese = resposta["regioes"][0]["sintese"]
    assert "Bairro B" in sintese["leitura"]
    assert 1 <= len(sintese["sinais"]) <= 3
    assert 1 <= len(sintese["atencoes"]) <= 3
    assert "microárea" in sintese["proximo_passo"]


def test_diagnostico_preserva_zero_como_valor_observado():
    resposta = montar_diagnostico(
        _segmento(),
        [{"id_regiao": 1, "nome": "Bairro A"}],
        _indicadores(),
        [{"id_regiao": 1, "quantidade": 0, "por_10k_hab": 0}],
        {"fonte": "OSM", "data_referencia": None, "cobertura": "parcial"},
    )
    oferta = next(d for d in resposta["regioes"][0]["dimensoes"] if d["id"] == "oferta_local")
    por_10k = next(e for e in oferta["evidencias"] if e["indicador"] == "oferta_por_10k")

    assert por_10k["valor"] == 0
    assert por_10k["disponivel"] is True
    assert oferta["limitacoes"]
    assert any("não comprova demanda" in texto for texto in resposta["regioes"][0]["sintese"]["atencoes"])
