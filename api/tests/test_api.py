"""Testes de ponta a ponta da API contra um banco real (o mesmo das imagens Docker).

Como rodar, na pasta api/, com o compose de pé (o banco fica exposto em localhost:55432):
    pip install -r requirements-dev.txt
    DATABASE_URL=postgresql://pontozero_app:pontozero_app@localhost:55432/pontozero \
    ADMIN_DATABASE_URL=postgresql://pontozero:pontozero_admin@localhost:55432/pontozero \
    python -m pytest -q tests

Cada teste cita a história de usuário (HU) e o critério que verifica.
"""

import os
import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def cliente():
    with TestClient(app) as c:
        yield c


def ids(cliente, *nomes):
    regioes = {r["nome"]: r["id_regiao"] for r in cliente.get("/api/regioes").json()}
    return [regioes[n] for n in nomes]


def id_segmento(cliente, nome):
    return next(s["id_categoria"] for s in cliente.get("/api/segmentos").json() if s["nome"] == nome)


def msg(resposta):
    detalhe = resposta.json()["detail"]
    return detalhe["mensagem"] if isinstance(detalhe, dict) else detalhe


# ------------------------------------------------------------------ infra
def test_health_e_status(cliente):
    assert cliente.get("/api/health").json() == {"status": "ok"}
    st = cliente.get("/api/status").json()
    assert st["banco"]["contagens"]["regiao"] == 94
    assert st["banco"]["volume_inicializado_em"]


# ---------------------------------------------------------- HU-003 / 004
def test_mapa_tem_todos_os_bairros_com_id(cliente):
    geo = cliente.get("/api/mapa/bairros").json()
    assert len(geo["features"]) == 94
    assert all(f["properties"]["id_regiao"] for f in geo["features"])


def test_segmentos_so_com_dados(cliente):
    segs = cliente.get("/api/segmentos").json()
    assert {s["nome"] for s in segs} >= {"Farmácia", "Padaria", "Academia"}
    assert all(s["total_estabelecimentos"] > 0 for s in segs)


# ---------------------------------------------------------- HU-005 / 007
def test_indicadores_tem_valor_unidade_fonte_e_data(cliente):
    (boa_viagem,) = ids(cliente, "Boa Viagem")
    r = cliente.get(f"/api/indicadores?regioes={boa_viagem}").json()
    itens = {i["tipo"]: i for i in r["regioes"][0]["indicadores"]}
    assert itens["populacao"]["valor"] == 125805
    assert itens["populacao"]["unidade"] == "habitantes"
    assert itens["populacao"]["fonte"].startswith("IBGE")
    assert itens["populacao"]["data_referencia"] == "2022-07-31"
    # fonte sem data -> texto exigido pela HU-007 RN03
    assert itens["area_km2"]["data_texto"] == "data de referência não informada"
    assert "aproximações" in r["aviso"]


def test_indicador_sem_dado_aparece_indisponivel(cliente):
    admin = os.getenv("ADMIN_DATABASE_URL")
    if not admin:
        pytest.skip("ADMIN_DATABASE_URL não definido")
    with psycopg.connect(admin, autocommit=True) as conn:
        novo = conn.execute(
            "INSERT INTO regiao (nome, tipo, cidade, estado) VALUES ('Região de teste', 'Bairro', 'Teste', 'PE') RETURNING id_regiao"
        ).fetchone()[0]
    try:
        r = cliente.get(f"/api/indicadores?regioes={novo}").json()["regioes"][0]
        assert all(i["valor"] is None and not i["disponivel"] for i in r["indicadores"])
        assert r["mensagem"] == "Não há indicadores disponíveis para esta região."
    finally:
        with psycopg.connect(admin, autocommit=True) as conn:
            conn.execute("DELETE FROM regiao WHERE id_regiao = %s", (novo,))


# --------------------------------------------------------------- HU-006
def test_oferta_exige_segmento(cliente):
    r = cliente.get("/api/oferta")
    assert r.status_code == 422
    assert "segmento" in msg(r)


def test_oferta_usa_base_formal_e_expoe_qualidade(cliente):
    farmacia = id_segmento(cliente, "Farmácia")
    agua_fria, boa_viagem = ids(cliente, "Água Fria", "Boa Viagem")
    r = cliente.get(f"/api/oferta?segmento={farmacia}&regioes={agua_fria},{boa_viagem}").json()
    assert r["metrica"] == "estabelecimentos por 10 mil habitantes"
    assert r["fonte"].startswith("Prefeitura do Recife")
    assert sum(item["quantidade"] for item in r["regioes"]) > 0
    assert r["qualidade"]["cobertura"] == "cadastral"
    assert r["qualidade"]["cnpjs_formais"] == 1043
    assert r["qualidade"]["registros_associados"] == 1040
    assert r["qualidade"]["coordenadas_precisas"] == 0
    assert r["qualidade"]["zero_confirmado"] is False
    assert r["estabelecimentos"] == []


# --------------------------------------------------------------- HU-008
def test_comparacao_bloqueia_uma_regiao(cliente):
    (boa_viagem,) = ids(cliente, "Boa Viagem")
    r = cliente.get(f"/api/comparacao?regioes={boa_viagem}")
    assert r.status_code == 422
    assert msg(r) == "Selecione ao menos duas regiões para comparar"


def test_comparacao_mantem_ordem_sem_ranking(cliente):
    a, b, c = ids(cliente, "Pina", "Boa Viagem", "Graças")
    r = cliente.get(f"/api/comparacao?regioes={a},{b},{c}").json()
    assert [x["id_regiao"] for x in r["regioes"]] == [a, b, c]
    assert all(len(l["valores"]) == 3 for l in r["linhas"])


# --------------------------------------------------------------- HU-009
def test_analise_exige_segmento_e_duas_regioes(cliente):
    (pina,) = ids(cliente, "Pina")
    farmacia = id_segmento(cliente, "Farmácia")
    assert cliente.get(f"/api/analise?regioes={pina}").status_code == 422
    assert cliente.get(f"/api/analise?segmento={farmacia}&regioes={pina}").status_code == 422


def test_analise_qualifica_oferta_formal_e_mostra_fontes(cliente):
    farmacia = id_segmento(cliente, "Farmácia")
    agua_fria, boa_viagem = ids(cliente, "Água Fria", "Boa Viagem")
    r = cliente.get(f"/api/analise?segmento={farmacia}&regioes={agua_fria},{boa_viagem}").json()
    assert r["qualidade_oferta"]["cobertura"] == "cadastral"
    assert r["qualidade_oferta"]["registros_associados"] == 1040
    assert all(x["classificacao"] in {"oferta_observada_baixa", "oferta_observada_compativel", "nao_classificada"} for x in r["resultados"])
    assert all(x["zero_confirmado"] is False for x in r["resultados"])
    res = {x["id_regiao"]: x for x in r["resultados"]}
    assert res[agua_fria]["encontrados"] > 0
    assert res[agua_fria]["status_dado"] == "observado"
    assert res[boa_viagem]["encontrados"] > res[agua_fria]["encontrados"]
    assert any("não é recomendação" in a for a in r["avisos"])
    assert len(r["fontes"]) == 2 and len(r["criterios"]) == 5


# ---------------------------------------------------------- HU-001 / 002
def test_conta_completa(cliente):
    email = f"teste-{uuid.uuid4().hex[:8]}@pontozero.app"
    base = {"nome": "Pessoa Teste", "email": email, "senha": "12345678", "empresa": "Padaria Teste", "segmento": "Padaria"}

    curta = cliente.post("/api/auth/cadastro", json={**base, "senha": "123"})
    assert curta.status_code == 422 and curta.json()["detail"]["campo"] == "senha"
    invalido = cliente.post("/api/auth/cadastro", json={**base, "email": "sem-arroba"})
    assert invalido.status_code == 422 and invalido.json()["detail"]["campo"] == "email"

    assert cliente.post("/api/auth/cadastro", json=base).status_code == 201
    repetido = cliente.post("/api/auth/cadastro", json={**base, "email": email.upper()})
    assert repetido.status_code == 409 and msg(repetido) == "Este e-mail já está em uso."

    cliente.post("/api/auth/logout")
    errado = cliente.post("/api/auth/login", json={"email": email, "senha": "senhaerrada"})
    assert errado.status_code == 401 and msg(errado) == "E-mail ou senha inválidos"
    assert cliente.post("/api/auth/login", json={"email": email, "senha": "12345678"}).status_code == 200
    assert cliente.get("/api/auth/sessao").json()["email"] == email

    # o segmento pertence à análise e o estado fica congelado
    pina, boa_viagem = ids(cliente, "Pina", "Boa Viagem")
    padaria = id_segmento(cliente, "Padaria")
    farmacia = id_segmento(cliente, "Farmácia")
    incompleta = cliente.post("/api/analises", json={"nome": "X", "segmento": farmacia, "regioes": [pina]})
    assert incompleta.status_code == 422
    criada = cliente.post("/api/analises", json={"nome": "Orla", "segmento": padaria, "regioes": [pina, boa_viagem]}).json()
    assert len(criada["regioes"]) == 2
    assert criada["segmento"] == "Padaria"
    assert criada["snapshot_disponivel"] is True
    assert criada["versao_metodologia"] == "2026.11.3"
    assert criada["snapshot"]["selection"]["segmento"]["nome"] == "Padaria"
    admin = os.getenv("ADMIN_DATABASE_URL")
    if admin:
        with psycopg.connect(admin, autocommit=True) as conn:
            with pytest.raises(psycopg.errors.RaiseException, match="snapshot de análise é imutável"):
                conn.execute(
                    "UPDATE analise SET versao_metodologia = 'alterada' WHERE id_analise = %s",
                    (criada["id_analise"],),
                )

    # o id salvo prevalece sobre filtros atuais: a exportação usa o snapshot
    csv = cliente.post("/api/exportacoes", json={"segmento": farmacia, "regioes": [pina], "formato": "CSV", "id_analise": criada["id_analise"]})
    texto = csv.content.decode("utf-8-sig")
    assert csv.status_code == 200 and "Segmento;Padaria" in texto
    assert "Regiões;Pina, Boa Viagem" in texto
    assert cliente.get(f"/api/analises/{criada['id_analise']}").json()["qtd_relatorios"] == 1

    assert cliente.delete(f"/api/analises/{criada['id_analise']}").status_code == 204
    assert cliente.post("/api/auth/logout").status_code == 204
    assert cliente.get("/api/auth/sessao").status_code == 401


# --------------------------------------------------------------- HU-010
def test_exportacao_sem_analise_fica_indisponivel(cliente):
    r = cliente.post("/api/exportacoes", json={"regioes": [], "formato": "PDF"})
    assert r.status_code == 422


def test_exportacao_csv_tem_fontes_e_avisos(cliente):
    farmacia = id_segmento(cliente, "Farmácia")
    a, b = ids(cliente, "Casa Amarela", "Encruzilhada")
    r = cliente.post("/api/exportacoes", json={"segmento": farmacia, "regioes": [a, b], "formato": "CSV"})
    texto = r.content.decode("utf-8-sig")
    assert "Fonte;Data de referência;Usada em" in texto
    assert "não é recomendação definitiva de investimento" in texto
