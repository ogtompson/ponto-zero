from app.servicos.perfis_segmento import listar_perfis, perfil_por_nome


def test_catalogo_separa_maturidade_e_disponibilidade():
    catalogo = listar_perfis()
    segmentos = catalogo["segmentos"]

    assert len(segmentos) == 11
    assert {x["maturidade"] for x in segmentos} == {"especializado", "configurado", "geral"}
    assert {x["disponibilidade"] for x in segmentos} == {"piloto", "preparacao"}

    farmacia = perfil_por_nome("Farmácia")
    assert farmacia["maturidade"] == "especializado"
    assert farmacia["disponibilidade"] == "piloto"
    assert farmacia["cnaes_diretos"] == ["4771-7/01", "4771-7/02", "4771-7/03"]
    pilotos = [x for x in segmentos if x["disponibilidade"] == "piloto"]
    assert len(pilotos) == 6
    assert all(x["cnaes_oferta"] and x["perimetro_oferta"] for x in pilotos)
    assert perfil_por_nome("Cafeteria")["precisao_oferta"] == "aproximada"


def test_segmento_desconhecido_recebe_perfil_geral_sem_falsa_precisao():
    perfil = perfil_por_nome("Loja de suplementos")

    assert perfil["slug"] == "personalizado"
    assert perfil["maturidade"] == "geral"
    assert perfil["disponibilidade"] == "personalizado"
    assert perfil["area_influencia"] is None


def test_catalogo_nao_expoe_estado_mutavel_global():
    perfil = perfil_por_nome("Farmácia")
    perfil["direcionadores"].clear()

    assert perfil_por_nome("Farmácia")["direcionadores"]
