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
  - db/seed_dml.sql                      -> INSERTs de povoamento inicial (todas as 9 tabelas,
                                            no minimo 3 registros validos em cada uma)
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
SAIDA_SQL = RAIZ / "db" / "seed_dml.sql"
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


# ---------------------------------------------------------------------------
# Dados de demonstracao (EMPRESA, USUARIO, ANALISE, REGIAO_ANALISE e RELATORIO).
# Ficticios e marcados como "(demonstracao)". Todos os usuarios entram com a
# senha SENHA_DEMO (documentada no README). As datas sao fixas e no passado,
# porque o trigger trg_analise_data recusa analise com data no futuro.
# ---------------------------------------------------------------------------
SENHA_DEMO = b"pontozero2026"

# (nome, cnpj ou None, segmento = categoria.nome)
EMPRESAS_DEMO = [
    ("Rede Farma Nordeste (demonstração)", None, "Farmácia"),
    ("Padaria Pão do Bairro (demonstração)", "11222333000181", "Padaria"),
    ("Movimento Academias (demonstração)", "12345678000195", "Academia"),
]

# (nome, email, perfil, empresa)
USUARIOS_DEMO = [
    ("Demonstração PontoZero", "demo@pontozero.app", "admin", "Rede Farma Nordeste (demonstração)"),
    ("Analista da Rede Farma", "analista@pontozero.app", "analista", "Rede Farma Nordeste (demonstração)"),
    ("Gestão Pão do Bairro", "padaria@pontozero.app", "admin", "Padaria Pão do Bairro (demonstração)"),
    ("Gestão Movimento Academias", "academia@pontozero.app", "admin", "Movimento Academias (demonstração)"),
]

# (empresa, nome, data_criacao, objetivo, bairros, [(data_geracao, formato), ...])
ANALISES_DEMO = [
    (
        "Rede Farma Nordeste (demonstração)",
        "Zona Norte: onde abrir a próxima farmácia",
        "2026-11-17",
        "Comparar Casa Amarela, Água Fria e Encruzilhada antes da visita de campo.",
        ["Casa Amarela", "Água Fria", "Encruzilhada"],
        [("2026-11-17", "PDF"), ("2026-11-18", "CSV")],
    ),
    (
        "Rede Farma Nordeste (demonstração)",
        "Orla sul: farmácias perto da praia",
        "2026-11-18",
        "Ver se Boa Viagem, Pina e Imbiribeira comportam mais uma loja.",
        ["Boa Viagem", "Pina", "Imbiribeira"],
        [("2026-11-19", "PDF")],
    ),
    (
        "Padaria Pão do Bairro (demonstração)",
        "Padarias no centro expandido",
        "2026-11-19",
        "Medir a oferta de padarias em Boa Vista, Santo Amaro, Graças e Espinheiro.",
        ["Boa Vista", "Santo Amaro", "Graças", "Espinheiro"],
        [("2026-11-20", "CSV")],
    ),
    (
        "Movimento Academias (demonstração)",
        "Academias na Zona Oeste",
        "2026-11-20",
        "Comparar Várzea, Cordeiro, Iputinga, Torre e Madalena para a primeira unidade.",
        ["Várzea", "Cordeiro", "Iputinga", "Torre", "Madalena"],
        [],  # analise ainda sem relatorio: ANALISE gera RELATORIO e (0,n)
    ),
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

    # ---------------------------------------------- conferencias e contagem
    nomes_bairros = {b["nome"] for b in bairros}
    nomes_empresas = {e[0] for e in EMPRESAS_DEMO}
    nomes_categorias = {c[0] for c in CATEGORIAS}
    for _, _, seg in EMPRESAS_DEMO:
        if seg not in nomes_categorias:
            raise SystemExit(f"Segmento de demonstracao desconhecido: {seg}")
    for _, _, _, emp in USUARIOS_DEMO:
        if emp not in nomes_empresas:
            raise SystemExit(f"Usuario de demonstracao com empresa desconhecida: {emp}")
    for emp, nome, data_a, _, bairros_a, rels in ANALISES_DEMO:
        if emp not in nomes_empresas:
            raise SystemExit(f"Analise {nome!r} com empresa desconhecida: {emp}")
        if not bairros_a:
            raise SystemExit(f"Analise {nome!r} precisa de ao menos uma regiao")
        if set(bairros_a) - nomes_bairros:
            raise SystemExit(f"Analise {nome!r} com bairro inexistente: {set(bairros_a) - nomes_bairros}")
        if date.fromisoformat(data_a) > date.today():
            raise SystemExit(f"Analise {nome!r} com data no futuro: {data_a}")
        if any(d < data_a for d, _ in rels):
            raise SystemExit(f"Analise {nome!r} com relatorio anterior a ela")

    qtd_indicadores = sum(
        1 + (b["chave"] in domicilios) + (b["chave"] in media_moradores) + (b["chave"] in renda) + 1
        for b in bairros
    )
    contagem = {
        "categoria": len(CATEGORIAS),
        "regiao": len(bairros),
        "indicador": qtd_indicadores,
        "estabelecimento": len(estabelecimentos),
        "empresa": len(EMPRESAS_DEMO),
        "usuario": len(USUARIOS_DEMO),
        "analise": len(ANALISES_DEMO),
        "regiao_analise": sum(len(a[4]) for a in ANALISES_DEMO),
        "relatorio": sum(len(a[5]) for a in ANALISES_DEMO),
    }
    pequenas = [t for t, q in contagem.items() if q < 3]
    if pequenas:
        raise SystemExit(f"Tabelas com menos de 3 registros: {pequenas}")

    # ------------------------------------------------------------------- SQL
    linhas: list[str] = []
    w = linhas.append
    w("-- =====================================================================")
    w("-- PontoZero | seed_dml.sql - Povoamento inicial do banco (INSERTs)")
    w("--")
    w("-- Gerado por tools/gerar_carga.py. Nao edite a mao: rode o script de novo.")
    w(f"-- Gerado em {date.today().isoformat()} a partir de fontes abertas:")
    w("--   IBGE (Censo 2022 e 2010), Prefeitura do Recife e OpenStreetMap,")
    w("--   mais empresas, usuarios e analises ficticios de demonstracao.")
    w("--")
    w("-- Roda depois do db/ddl.sql, num banco vazio, numa transacao so.")
    w("-- As chaves estrangeiras sao buscadas pelo nome (bairro, segmento,")
    w("-- empresa), nunca por numero fixo, entao a carga nao depende da ordem dos")
    w("-- IDs. No fim, um bloco confere quantas linhas cada tabela recebeu: se um")
    w("-- nome nao casar e uma linha ficar de fora, a transacao inteira e desfeita.")
    w("--")
    w("-- Linhas por tabela:")
    for tabela, qtd in contagem.items():
        w(f"--   {tabela:<16} {qtd:>4}")
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

    # ---------------------------------------------------- demonstracao
    def id_empresa(nome: str) -> str:
        return f"(SELECT id_empresa FROM empresa WHERE nome = {sql_txt(nome)})"

    w(f"-- Empresas de demonstracao (EMPRESA): {len(EMPRESAS_DEMO)}")
    w("INSERT INTO empresa (nome, cnpj, segmento) VALUES")
    w(",\n".join(f"  ({sql_txt(n)}, {sql_txt(c)}, {sql_txt(seg)})" for n, c, seg in EMPRESAS_DEMO) + ";")
    w("")
    w(f"-- Usuarios de demonstracao (USUARIO): {len(USUARIOS_DEMO)}. Senha de todos: {SENHA_DEMO.decode()}")
    w("-- A senha vai como hash bcrypt: o CHECK ck_usuario_senha recusa texto puro.")
    w("INSERT INTO usuario (nome, email, senha, perfil, id_empresa) VALUES")
    w(
        ",\n".join(
            f"  ({sql_txt(n)}, {sql_txt(e)}, "
            f"{sql_txt(bcrypt.hashpw(SENHA_DEMO, bcrypt.gensalt(rounds=12)).decode())}, "
            f"{sql_txt(p)},\n   {id_empresa(emp)})"
            for n, e, p, emp in USUARIOS_DEMO
        )
        + ";"
    )
    w("")
    w(f"-- Analises salvas (ANALISE): {len(ANALISES_DEMO)}")
    w("INSERT INTO analise (nome, data_criacao, objetivo, id_empresa) VALUES")
    w(
        ",\n".join(
            f"  ({sql_txt(nome)}, DATE '{data}',\n   {sql_txt(obj)},\n   {id_empresa(emp)})"
            for emp, nome, data, obj, _, _ in ANALISES_DEMO
        )
        + ";"
    )
    w("")
    w(f"-- Regioes de cada analise (REGIAO_ANALISE, N:N): {sum(len(a[4]) for a in ANALISES_DEMO)}")
    w("INSERT INTO regiao_analise (id_analise, id_regiao)")
    w("SELECT a.id_analise, r.id_regiao")
    w("FROM (VALUES")
    w(
        ",\n".join(
            f"  ({sql_txt(emp)}, {sql_txt(nome)}, {sql_txt(b)})"
            for emp, nome, _, _, bairros_a, _ in ANALISES_DEMO
            for b in bairros_a
        )
    )
    w(") AS v(empresa, analise, bairro)")
    w("JOIN empresa e ON e.nome = v.empresa")
    w("JOIN analise a ON a.nome = v.analise AND a.id_empresa = e.id_empresa")
    w("JOIN regiao  r ON r.nome = v.bairro AND r.cidade = 'Recife' AND r.estado = 'PE';")
    w("")
    w(f"-- Exportacoes geradas (RELATORIO): {sum(len(a[5]) for a in ANALISES_DEMO)}")
    w("INSERT INTO relatorio (data_geracao, formato, id_analise)")
    w("SELECT v.data_geracao::date, v.formato, a.id_analise")
    w("FROM (VALUES")
    w(
        ",\n".join(
            f"  ({sql_txt(emp)}, {sql_txt(nome)}, '{data}', {sql_txt(fmt)})"
            for emp, nome, _, _, _, rels in ANALISES_DEMO
            for data, fmt in rels
        )
    )
    w(") AS v(empresa, analise, data_geracao, formato)")
    w("JOIN empresa e ON e.nome = v.empresa")
    w("JOIN analise a ON a.nome = v.analise AND a.id_empresa = e.id_empresa;")
    w("")
    w("-- ---------------------------------------------------------------------")
    w("-- Conferencia: cada tabela recebeu exatamente as linhas esperadas (e no")
    w("-- minimo 3), toda analise tem ao menos uma regiao (cardinalidade 1,n) e")
    w("-- nenhum relatorio e anterior a sua analise. Se algo falhar, RAISE")
    w("-- desfaz a transacao inteira.")
    w("-- ---------------------------------------------------------------------")
    w("DO $$")
    w("DECLARE")
    w("    t record;")
    w("    n bigint;")
    w("BEGIN")
    w("    FOR t IN SELECT * FROM (VALUES")
    w(",\n".join(f"        ({sql_txt(tab)}, {qtd})" for tab, qtd in contagem.items()))
    w("    ) AS v(tabela, esperado) LOOP")
    w("        EXECUTE format('SELECT count(*) FROM %I', t.tabela) INTO n;")
    w("        IF n < 3 THEN")
    w("            RAISE EXCEPTION 'Tabela % tem só % linha(s); o mínimo é 3', t.tabela, n;")
    w("        END IF;")
    w("        IF n <> t.esperado THEN")
    w("            RAISE EXCEPTION 'Tabela % tem % linha(s), esperado %', t.tabela, n, t.esperado;")
    w("        END IF;")
    w("    END LOOP;")
    w("")
    w("    IF EXISTS (SELECT 1 FROM analise a")
    w("               WHERE NOT EXISTS (SELECT 1 FROM regiao_analise ra WHERE ra.id_analise = a.id_analise)) THEN")
    w("        RAISE EXCEPTION 'Há análise sem nenhuma região (ANALISE inclui REGIAO é 1,n)';")
    w("    END IF;")
    w("")
    w("    IF EXISTS (SELECT 1 FROM relatorio r JOIN analise a ON a.id_analise = r.id_analise")
    w("               WHERE r.data_geracao < a.data_criacao) THEN")
    w("        RAISE EXCEPTION 'Há relatório gerado antes da própria análise';")
    w("    END IF;")
    w("")
    w("    RAISE NOTICE 'seed_dml.sql: povoamento conferido em todas as 9 tabelas';")
    w("END")
    w("$$;")
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
