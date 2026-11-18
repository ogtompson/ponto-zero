"""
Gera a carga inicial do banco do PontoZero a partir de fontes abertas.

Entrada: um JSON com os dados brutos coletados (ver docs/dados.md):
  - IBGE / SIDRA  tabela 9923 (populacao 2022 por bairro)
  - IBGE / SIDRA  tabela 9922 (domicilios 2022 por bairro)
  - IBGE / SIDRA  tabela 3345 (renda media domiciliar 2010 por bairro)
  - Prefeitura do Recife (dados.recife.pe.gov.br): limites oficiais dos bairros (GeoJSON)
  - OpenStreetMap via Overpass API: farmacias, supermercados, padarias, cafeterias,
    academias e pet shops dentro do Recife

Saidas:
  - db/init/04_carga_dados.sql           -> INSERTs nas tabelas do modelo
  - api/app/data/bairros-recife.geojson  -> poligonos simplificados para o mapa

Uso:
  python tools/gerar_carga.py            (usa tools/dados/pontozero-dados.json)
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import bcrypt
from shapely.geometry import Point, mapping, shape
from shapely.strtree import STRtree

RAIZ = Path(__file__).resolve().parents[1]
SAIDA_SQL = RAIZ / "db" / "init" / "04_carga_dados.sql"
SAIDA_GEO = RAIZ / "api" / "app" / "data" / "bairros-recife.geojson"

# Datas de referencia oficiais de cada pesquisa
DATA_CENSO_2022 = "2022-07-31"
DATA_CENSO_2010 = "2010-07-31"

FONTE_POP = "IBGE, Censo Demográfico 2022 (SIDRA 9923)"
FONTE_DOM = "IBGE, Censo Demográfico 2022 (SIDRA 9922)"
FONTE_RENDA = "IBGE, Censo Demográfico 2010 (SIDRA 3345)"
FONTE_AREA = "Prefeitura do Recife, Portal de Dados Abertos"

# Categorias do piloto -> como reconhecer no OpenStreetMap
CATEGORIAS = [
    ("Farmácia", "Farmácias e drogarias", lambda t: t.get("amenity") == "pharmacy"),
    ("Supermercado", "Supermercados e mercados de bairro de porte médio", lambda t: t.get("shop") == "supermarket"),
    ("Padaria", "Padarias e confeitarias de bairro", lambda t: t.get("shop") == "bakery"),
    ("Cafeteria", "Cafés e cafeterias", lambda t: t.get("amenity") == "cafe"),
    ("Academia", "Academias de ginástica e estúdios de treino", lambda t: t.get("leisure") == "fitness_centre"),
    ("Pet shop", "Lojas de produtos e serviços para animais", lambda t: t.get("shop") == "pet"),
]


def norm(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def sql_txt(valor) -> str:
    if valor is None:
        return "NULL"
    return "'" + str(valor).replace("'", "''") + "'"


def main(caminho: str) -> None:
    bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))

    # ---------------------------------------------------------------- bairros
    feicoes = bruto["bairros_geojson"]["features"]
    bairros = []
    for f in feicoes:
        p = f["properties"]
        nome = (p.get("EBAIRRNOMEOF") or p.get("EBAIRRNOME")).strip()
        geom = shape(f["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        bairros.append(
            {
                "nome": nome,
                "chave": norm(nome),
                "rpa": p.get("CRPAAACODI"),
                "area_km2": round(p["DB2GSE.ST_Area(SHAPE)"] / 1_000_000, 2),
                "geom": geom,
            }
        )
    bairros.sort(key=lambda b: b["chave"])

    # O IBGE chama de "Cohab" o bairro que a Prefeitura chama de "Cohab - Ibura de Cima"
    apelidos = {"cohab": "cohab ibura de cima"}

    def chave_ibge(rotulo: str) -> str:
        nome = rotulo.split(" - Recife")[0]
        k = norm(nome)
        return apelidos.get(k, k)

    pop = {chave_ibge(r[1]): int(r[3]) for r in bruto["pop2022"] if r[3] not in ("-", "...", "X")}
    domicilios, media_moradores = {}, {}
    for cod, rotulo, var, valor in bruto["dom2022"]:
        if valor in ("-", "...", "X"):
            continue
        if var == "381":
            domicilios[chave_ibge(rotulo)] = int(valor)
        elif var == "5930":
            media_moradores[chave_ibge(rotulo)] = float(valor)
    renda = {chave_ibge(r[1]): float(r[3]) for r in bruto["renda2010"] if r[3] not in ("-", "...", "X")}

    faltando = [b["nome"] for b in bairros if b["chave"] not in pop]
    if faltando:
        raise SystemExit(f"Bairros sem populacao no IBGE: {faltando}")

    # ------------------------------------------------------- estabelecimentos
    arvore = STRtree([b["geom"] for b in bairros])
    estabelecimentos = []
    ignorados = 0
    vistos = set()
    for e in bruto["osm"]["elements"]:
        tags = e.get("tags", {})
        lat = e.get("lat") or (e.get("center") or {}).get("lat")
        lon = e.get("lon") or (e.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        cat = next((nome for nome, _, teste in CATEGORIAS if teste(tags)), None)
        if cat is None:
            ignorados += 1
            continue
        ponto = Point(lon, lat)
        idx = None
        for i in arvore.query(ponto):
            if bairros[i]["geom"].contains(ponto):
                idx = i
                break
        if idx is None:
            # ponto na borda: aceita o bairro mais proximo ate ~150 m
            i = arvore.nearest(ponto)
            if bairros[i]["geom"].distance(ponto) < 0.0015:
                idx = i
        if idx is None:
            ignorados += 1
            continue
        chave_dup = (cat, round(lat, 5), round(lon, 5))
        if chave_dup in vistos:
            continue
        vistos.add(chave_dup)
        nome = (tags.get("name") or tags.get("brand") or "").strip()
        if not nome:
            nome = f"{cat} sem nome no OpenStreetMap"
        rua = tags.get("addr:street")
        numero = tags.get("addr:housenumber")
        endereco = None
        if rua:
            endereco = f"{rua}, {numero}" if numero else rua
        estabelecimentos.append(
            {
                "nome": nome[:100],
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "endereco": endereco[:255] if endereco else None,
                "bairro": bairros[idx]["nome"],
                "categoria": cat,
            }
        )
    estabelecimentos.sort(key=lambda x: (x["categoria"], x["bairro"], x["nome"]))
    data_osm = bruto["osm"]["osm3s"]["timestamp_osm_base"][:10]

    # ------------------------------------------------------------------- SQL
    linhas: list[str] = []
    w = linhas.append
    w("-- =====================================================================")
    w("-- PontoZero | 04 - Carga inicial de dados (gerado por tools/gerar_carga.py)")
    w(f"-- Gerado em {date.today().isoformat()} a partir de fontes abertas:")
    w("--   IBGE (Censo 2022 e 2010), Prefeitura do Recife e OpenStreetMap.")
    w("-- Nao edite a mao: rode o script de novo se os dados mudarem.")
    w("-- =====================================================================")
    w("")
    w("BEGIN;")
    w("")
    w("-- Segmentos do piloto (CATEGORIA)")
    w("INSERT INTO categoria (nome, descricao) VALUES")
    w(",\n".join(f"  ({sql_txt(n)}, {sql_txt(d)})" for n, d, _ in CATEGORIAS) + ";")
    w("")
    w("-- 94 bairros oficiais do Recife (REGIAO)")
    w("INSERT INTO regiao (nome, tipo, cidade, estado) VALUES")
    w(",\n".join(f"  ({sql_txt(b['nome'])}, 'Bairro', 'Recife', 'PE')" for b in bairros) + ";")
    w("")
    w("-- Indicadores territoriais (INDICADOR). Cada linha guarda fonte e data de referencia.")
    w("INSERT INTO indicador (tipo, valor, data_referencia, fonte, id_regiao)")
    w("SELECT v.tipo, v.valor, v.data_ref::date, v.fonte, r.id_regiao")
    w("FROM (VALUES")
    vals = []
    for b in bairros:
        k = b["chave"]
        n = sql_txt(b["nome"])
        vals.append(f"  ({n}, 'populacao', {pop[k]}, '{DATA_CENSO_2022}', {sql_txt(FONTE_POP)})")
        if k in domicilios:
            vals.append(f"  ({n}, 'domicilios', {domicilios[k]}, '{DATA_CENSO_2022}', {sql_txt(FONTE_DOM)})")
        if k in media_moradores:
            vals.append(f"  ({n}, 'moradores_por_domicilio', {media_moradores[k]}, '{DATA_CENSO_2022}', {sql_txt(FONTE_DOM)})")
        if k in renda:
            vals.append(f"  ({n}, 'renda_media_domiciliar', {renda[k]}, '{DATA_CENSO_2010}', {sql_txt(FONTE_RENDA)})")
        # a fonte da area nao informa data de referencia -> NULL (HU-007 RN03)
        vals.append(f"  ({n}, 'area_km2', {b['area_km2']}, NULL, {sql_txt(FONTE_AREA)})")
    w(",\n".join(vals))
    w(") AS v(bairro, tipo, valor, data_ref, fonte)")
    w("JOIN regiao r ON r.nome = v.bairro AND r.cidade = 'Recife';")
    w("")
    w(f"-- Oferta comercial (ESTABELECIMENTO): {len(estabelecimentos)} pontos do OpenStreetMap")
    w("INSERT INTO estabelecimento (nome, latitude, longitude, endereco, id_regiao, id_categoria)")
    w("SELECT v.nome, v.lat, v.lon, v.endereco, r.id_regiao, c.id_categoria")
    w("FROM (VALUES")
    w(
        ",\n".join(
            f"  ({sql_txt(e['nome'])}, {e['lat']}, {e['lon']}, {sql_txt(e['endereco'])}, {sql_txt(e['bairro'])}, {sql_txt(e['categoria'])})"
            for e in estabelecimentos
        )
    )
    w(") AS v(nome, lat, lon, endereco, bairro, categoria)")
    w("JOIN regiao r ON r.nome = v.bairro AND r.cidade = 'Recife'")
    w("JOIN categoria c ON c.nome = v.categoria;")
    w("")
    w("-- Metadados da camada de oferta (lidos pela API para exibir fonte e data - HU-007)")
    w(
        "COMMENT ON TABLE estabelecimento IS "
        + sql_txt(f"fonte=OpenStreetMap, contribuidores (licença ODbL);data_referencia={data_osm}")
        + ";"
    )
    w("")

    # Conta de demonstracao para a apresentacao (senha documentada no README)
    senha_demo = bcrypt.hashpw(b"pontozero2026", bcrypt.gensalt(rounds=12)).decode()
    w("-- Empresa e usuario de demonstracao (login: demo@pontozero.app / pontozero2026)")
    w("INSERT INTO empresa (nome, cnpj, segmento) VALUES ('Rede Farma Nordeste (demonstração)', NULL, 'Farmácia');")
    w(
        "INSERT INTO usuario (nome, email, senha, perfil, id_empresa) "
        f"SELECT 'Demonstração PontoZero', 'demo@pontozero.app', {sql_txt(senha_demo)}, 'admin', id_empresa "
        "FROM empresa WHERE nome = 'Rede Farma Nordeste (demonstração)';"
    )
    w("")
    w("-- Uma analise salva de exemplo, com as regioes que ela inclui (REGIAO_ANALISE) e um relatorio")
    w("WITH nova AS (")
    w("  INSERT INTO analise (nome, data_criacao, objetivo, id_empresa)")
    w("  SELECT 'Zona Norte: onde abrir a próxima farmácia', CURRENT_DATE,")
    w("         'Comparar Casa Amarela, Água Fria e Encruzilhada antes da visita de campo.', id_empresa")
    w("  FROM empresa WHERE nome = 'Rede Farma Nordeste (demonstração)'")
    w("  RETURNING id_analise")
    w("), regioes AS (")
    w("  INSERT INTO regiao_analise (id_analise, id_regiao)")
    w("  SELECT nova.id_analise, r.id_regiao FROM nova")
    w("  JOIN regiao r ON r.nome IN ('Casa Amarela', 'Água Fria', 'Encruzilhada') AND r.cidade = 'Recife'")
    w("  RETURNING id_analise")
    w(")")
    w("INSERT INTO relatorio (data_geracao, formato, id_analise)")
    w("SELECT CURRENT_DATE, 'PDF', id_analise FROM nova;")
    w("")
    w("COMMIT;")
    SAIDA_SQL.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_SQL.write_text("\n".join(linhas) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- GeoJSON
    saida = {"type": "FeatureCollection", "features": []}

    def arredonda(c):
        if isinstance(c, (list, tuple)) and c and isinstance(c[0], (list, tuple)):
            return [arredonda(x) for x in c]
        return [round(c[0], 5), round(c[1], 5)]

    for b in bairros:
        g = b["geom"].simplify(0.00012, preserve_topology=True)
        ponto = b["geom"].representative_point()
        gm = mapping(g)
        saida["features"].append(
            {
                "type": "Feature",
                "properties": {
                    "nome": b["nome"],
                    "rpa": b["rpa"],
                    "lat": round(ponto.y, 5),
                    "lng": round(ponto.x, 5),
                },
                "geometry": {"type": gm["type"], "coordinates": arredonda(gm["coordinates"])},
            }
        )
    SAIDA_GEO.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_GEO.write_text(json.dumps(saida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    from collections import Counter

    print(f"bairros: {len(bairros)}")
    print(f"estabelecimentos: {len(estabelecimentos)} (ignorados {ignorados})", Counter(e["categoria"] for e in estabelecimentos))
    print(f"osm base: {data_osm}")
    print(f"sql: {SAIDA_SQL.stat().st_size/1024:.0f} KB | geojson: {SAIDA_GEO.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(RAIZ / "tools" / "dados" / "pontozero-dados.json"))
