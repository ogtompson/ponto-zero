"""Consultas de território usadas pelas rotas e pela exportação.

Cada função devolve dicionários prontos para virar JSON. As regras das
histórias de usuário estão comentadas no ponto onde são aplicadas.
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache

from fastapi import HTTPException

from ..config import (
    AVISO_APROXIMACAO,
    AVISO_NAO_RECOMENDACAO,
    AVISO_OFERTA,
    SEM_DATA,
    config,
)
from ..db import consulta, consulta_um
from .diagnostico import montar_diagnostico
from .perfis_segmento import perfil_por_nome

MAX_REGIOES = 8  # HU-008: limite definido pela equipe para manter a comparação legível


def erro(status: int, mensagem: str, campo: str | None = None) -> HTTPException:
    return HTTPException(status_code=status, detail={"mensagem": mensagem, "campo": campo})


def chave_ordem(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def ids_da_query(texto: str | None) -> list[int]:
    """'3,1,3,7' -> [3, 1, 7] (sem repetir e mantendo a ordem de seleção)."""
    if not texto:
        return []
    ids: list[int] = []
    for parte in texto.split(","):
        parte = parte.strip()
        if not parte:
            continue
        if not parte.isdigit():
            raise erro(422, "Lista de regiões inválida.", "regioes")
        valor = int(parte)
        if valor not in ids:
            ids.append(valor)
    return ids


def _data(d) -> str | None:
    return d.isoformat() if d else None


# --------------------------------------------------------------------- base
def listar_segmentos() -> list[dict]:
    # HU-004 RN01: só segmentos com dados disponíveis no piloto
    linhas = consulta(
        """
        SELECT id_categoria, nome, total_estabelecimentos, por_10k_hab
        FROM vw_referencia_categoria
        WHERE total_estabelecimentos > 0
        """
    )
    descricoes = {r["id_categoria"]: r["descricao"] for r in consulta("SELECT id_categoria, descricao FROM categoria")}
    for linha in linhas:
        linha["descricao"] = descricoes.get(linha["id_categoria"])
        linha["por_10k_hab"] = float(linha["por_10k_hab"] or 0)
        _aplicar_perfil(linha)
    return sorted(linhas, key=lambda r: chave_ordem(r["nome"]))


def _aplicar_perfil(segmento: dict) -> dict:
    perfil = perfil_por_nome(segmento["nome"])
    for campo in ("slug", "maturidade", "disponibilidade", "direcionadores", "area_influencia"):
        segmento[campo] = perfil[campo]
    return segmento


def segmento_valido(id_categoria: int | None, obrigatorio: bool = True) -> dict | None:
    if id_categoria is None:
        if obrigatorio:
            raise erro(422, "Escolha um segmento para ver a oferta comercial e a análise.", "segmento")
        return None
    seg = consulta_um(
        """
        SELECT id_categoria, nome, total_estabelecimentos, por_10k_hab
        FROM vw_referencia_categoria WHERE id_categoria = %s
        """,
        (id_categoria,),
    )
    if not seg or seg["total_estabelecimentos"] == 0:
        raise erro(422, "Este segmento não tem dados disponíveis no piloto.", "segmento")
    seg["por_10k_hab"] = float(seg["por_10k_hab"])
    return _aplicar_perfil(seg)


def listar_regioes() -> list[dict]:
    linhas = consulta(
        """
        SELECT r.id_regiao, r.nome, r.tipo, r.cidade, r.estado,
               max(i.valor) FILTER (WHERE i.tipo = 'populacao')              AS populacao,
               max(i.valor) FILTER (WHERE i.tipo = 'renda_media_domiciliar') AS renda,
               max(i.valor) FILTER (WHERE i.tipo = 'densidade')              AS densidade
        FROM regiao r
        LEFT JOIN vw_indicador_completo i ON i.id_regiao = r.id_regiao
        GROUP BY r.id_regiao
        """
    )
    for r in linhas:
        for k in ("populacao", "renda", "densidade"):
            r[k] = float(r[k]) if r[k] is not None else None
    return sorted(linhas, key=lambda r: chave_ordem(r["nome"]))


def regioes_validas(ids: list[int], minimo: int = 1, mensagem_minimo: str | None = None) -> list[dict]:
    if len(ids) < minimo:
        raise erro(422, mensagem_minimo or "Selecione ao menos uma região.", "regioes")
    if len(ids) > MAX_REGIOES:
        raise erro(422, f"Selecione no máximo {MAX_REGIOES} regiões por vez.", "regioes")
    encontradas = consulta(
        "SELECT id_regiao, nome, tipo, cidade, estado FROM regiao WHERE id_regiao = ANY(%s)", (ids,)
    )
    por_id = {r["id_regiao"]: r for r in encontradas}
    faltando = [i for i in ids if i not in por_id]
    if faltando:
        raise erro(404, "Uma das regiões selecionadas não existe mais.", "regioes")
    return [por_id[i] for i in ids]


@lru_cache(maxsize=1)
def metadados_oferta() -> dict:
    """Fonte e data da camada de oferta ficam no COMMENT da tabela estabelecimento."""
    linha = consulta_um("SELECT obj_description('estabelecimento'::regclass, 'pg_class') AS c")
    meta = {"fonte": None, "data_referencia": None, "cobertura": "parcial"}
    for parte in (linha["c"] or "").split(";"):
        if "=" in parte:
            k, v = parte.split("=", 1)
            meta[k.strip()] = v.strip() or None
    if not meta["fonte"]:
        meta["fonte"] = "Fonte não identificada"
    # A coleta do OpenStreetMap não comprova que um bairro sem registros tenha
    # oferta igual a zero. Até existir uma medição de cobertura por região e
    # categoria, a API trata a camada como observacional e parcial.
    if meta["cobertura"] not in {"parcial", "verificada"}:
        meta["cobertura"] = "parcial"
    return meta


def qualidade_oferta(meta: dict) -> dict:
    verificada = meta["cobertura"] == "verificada"
    return {
        "cobertura": meta["cobertura"],
        "zero_confirmado": verificada,
        "descricao": (
            "Cobertura verificada para o recorte analisado."
            if verificada
            else "Cobertura parcial: ausência de registro não confirma ausência de estabelecimentos."
        ),
    }


def catalogo_indicadores() -> list[dict]:
    return consulta("SELECT tipo, rotulo, unidade, ordem FROM vw_catalogo_indicador ORDER BY ordem")


# ------------------------------------------------------------- HU-005 / 007
def indicadores(ids: list[int]) -> dict:
    regioes = regioes_validas(ids)
    catalogo = catalogo_indicadores()
    linhas = consulta(
        """
        SELECT id_regiao, tipo, valor, data_referencia, fonte, derivado
        FROM vw_indicador_completo
        WHERE id_regiao = ANY(%s) AND fonte IS NOT NULL   -- HU-007: sem fonte não exibe
        """,
        (ids,),
    )
    por_regiao: dict[int, dict[str, dict]] = {}
    for l in linhas:
        por_regiao.setdefault(l["id_regiao"], {})[l["tipo"]] = l

    resultado = []
    for r in regioes:
        dados = por_regiao.get(r["id_regiao"], {})
        itens = []
        for c in catalogo:
            l = dados.get(c["tipo"])
            itens.append(
                {
                    "tipo": c["tipo"],
                    "rotulo": c["rotulo"],
                    "unidade": c["unidade"],
                    # HU-005 RN03: sem dado aparece como indisponível, nunca como zero
                    "valor": float(l["valor"]) if l else None,
                    "disponivel": l is not None,
                    "fonte": l["fonte"] if l else None,
                    "data_referencia": _data(l["data_referencia"]) if l else None,
                    "data_texto": (_data(l["data_referencia"]) or SEM_DATA) if l else None,
                    "derivado": bool(l["derivado"]) if l else False,
                }
            )
        resultado.append(
            {
                **r,
                "indicadores": itens,
                "mensagem": None if dados else "Não há indicadores disponíveis para esta região.",
            }
        )
    return {"regioes": resultado, "aviso": AVISO_APROXIMACAO}


# ------------------------------------------------------------------ HU-006
def oferta(id_categoria: int | None, ids: list[int]) -> dict:
    seg = segmento_valido(id_categoria)
    meta = metadados_oferta()
    resumo = []
    if ids:
        regioes = regioes_validas(ids)
        linhas = consulta(
            """
            SELECT id_regiao, quantidade, populacao, por_10k_hab
            FROM vw_oferta_regiao WHERE id_categoria = %s AND id_regiao = ANY(%s)
            """,
            (seg["id_categoria"], ids),
        )
        por_id = {l["id_regiao"]: l for l in linhas}
        for r in regioes:
            l = por_id.get(r["id_regiao"])
            qtd = l["quantidade"] if l else 0
            resumo.append(
                {
                    "id_regiao": r["id_regiao"],
                    "nome": r["nome"],
                    "quantidade": qtd,
                    "populacao": float(l["populacao"]) if l and l["populacao"] is not None else None,
                    # RN02: mesma métrica para todas as regiões (por 10 mil habitantes)
                    "por_10k_hab": float(l["por_10k_hab"]) if l and l["por_10k_hab"] is not None else None,
                    "mensagem": None
                    if qtd
                    else "nenhum estabelecimento observado na base; a cobertura é parcial",
                    "status_dado": "observado" if qtd else "sem_registro_observado",
                }
            )
        filtro = "AND e.id_regiao = ANY(%s)"
        params = (seg["id_categoria"], ids)
    else:
        filtro = ""
        params = (seg["id_categoria"],)

    pontos = consulta(
        f"""
        SELECT e.id_estabelecimento AS id, e.nome, e.latitude AS lat, e.longitude AS lng,
               e.endereco, e.id_regiao, r.nome AS regiao
        FROM estabelecimento e JOIN regiao r ON r.id_regiao = e.id_regiao
        WHERE e.id_categoria = %s {filtro}
        ORDER BY e.nome
        """,
        params,
    )
    for p in pontos:
        p["lat"], p["lng"] = float(p["lat"]), float(p["lng"])

    return {
        "segmento": seg,
        "fonte": meta["fonte"],
        "data_referencia": meta["data_referencia"],
        "data_texto": meta["data_referencia"] or SEM_DATA,
        "metrica": "estabelecimentos por 10 mil habitantes",
        "regioes": resumo,
        "estabelecimentos": pontos,
        "qualidade": qualidade_oferta(meta),
        "aviso": AVISO_OFERTA,
    }


def oferta_mapa(id_categoria: int) -> list[dict]:
    seg = segmento_valido(id_categoria)
    linhas = consulta(
        "SELECT id_regiao, quantidade, por_10k_hab FROM vw_oferta_regiao WHERE id_categoria = %s",
        (seg["id_categoria"],),
    )
    return [
        {
            "id_regiao": l["id_regiao"],
            "quantidade": l["quantidade"],
            "por_10k_hab": float(l["por_10k_hab"]) if l["por_10k_hab"] is not None else None,
        }
        for l in linhas
    ]


# ------------------------------------------------------------------ HU-008
def comparacao(id_categoria: int | None, ids: list[int]) -> dict:
    regioes = regioes_validas(ids, 2, "Selecione ao menos duas regiões para comparar")
    ind = indicadores(ids)
    catalogo = catalogo_indicadores()
    linhas = []
    for c in catalogo:
        valores = []
        for r in ind["regioes"]:
            item = next(i for i in r["indicadores"] if i["tipo"] == c["tipo"])
            valores.append(
                {
                    "id_regiao": r["id_regiao"],
                    "valor": item["valor"],
                    "disponivel": item["disponivel"],
                    "fonte": item["fonte"],
                    "data_texto": item["data_texto"],
                }
            )
        linhas.append({**c, "valores": valores})

    oferta_bloco = None
    if id_categoria is not None:
        o = oferta(id_categoria, ids)
        oferta_bloco = {
            "segmento": o["segmento"]["nome"],
            "fonte": o["fonte"],
            "data_texto": o["data_texto"],
            "metrica": o["metrica"],
            "qualidade": o["qualidade"],
            "valores": [
                {k: r[k] for k in ("id_regiao", "quantidade", "por_10k_hab", "mensagem", "status_dado")} for r in o["regioes"]
            ],
        }

    fontes = _fontes(ind, oferta_bloco)
    return {
        # RN04: sem ranking -> as regiões ficam na ordem em que o usuário escolheu
        "regioes": [{"id_regiao": r["id_regiao"], "nome": r["nome"]} for r in regioes],
        "linhas": linhas,
        "oferta": oferta_bloco,
        "fontes": fontes,
        "avisos": [AVISO_APROXIMACAO] + ([AVISO_OFERTA] if oferta_bloco else []),
    }


def _fontes(ind: dict, oferta_bloco: dict | None) -> list[dict]:
    vistas: dict[str, dict] = {}
    for r in ind["regioes"]:
        for i in r["indicadores"]:
            if i["disponivel"]:
                chave = i["fonte"] + "|" + i["data_texto"]
                vistas.setdefault(chave, {"fonte": i["fonte"], "data_texto": i["data_texto"], "usada_em": set()})
                vistas[chave]["usada_em"].add(i["rotulo"])
    if oferta_bloco:
        chave = oferta_bloco["fonte"] + "|" + oferta_bloco["data_texto"]
        vistas.setdefault(chave, {"fonte": oferta_bloco["fonte"], "data_texto": oferta_bloco["data_texto"], "usada_em": set()})
        vistas[chave]["usada_em"].add(f"Estabelecimentos ({oferta_bloco['segmento']})")
    return [{**v, "usada_em": sorted(v["usada_em"])} for v in vistas.values()]


# ------------------------------------------------------------------ HU-009
def analise(id_categoria: int | None, ids: list[int]) -> dict:
    # RN01: exige segmento e ao menos duas regiões
    if id_categoria is None and len(ids) < 2:
        raise erro(422, "Para ver a análise, escolha um segmento e ao menos duas regiões.", "segmento")
    seg = segmento_valido(id_categoria)
    regioes = regioes_validas(ids, 2, "Selecione ao menos duas regiões para ver a análise")

    linhas = consulta(
        "SELECT * FROM fn_analise_demanda_oferta(%s::int, %s::int[], %s::numeric, %s::numeric)",
        (seg["id_categoria"], ids, config.analise_min_esperado, config.analise_cobertura_max),
    )
    por_id = {l["id_regiao"]: l for l in linhas}
    meta = metadados_oferta()
    cobertura_verificada = meta["cobertura"] == "verificada"
    resultados = []
    for r in regioes:
        l = por_id[r["id_regiao"]]
        classificacao_interna = l["classificacao"]
        classificacao = {
            "possivel_lacuna": "oferta_observada_baixa",
            "sem_indicio": "oferta_observada_compativel",
            "oferta_observada_baixa": "oferta_observada_baixa",
            "oferta_observada_compativel": "oferta_observada_compativel",
            "nao_classificada": "nao_classificada",
        }[classificacao_interna]
        resultados.append(
            {
                "id_regiao": r["id_regiao"],
                "nome": r["nome"],
                "populacao": float(l["populacao"]) if l["populacao"] is not None else None,
                "encontrados": l["encontrados"],
                "esperado": float(l["esperado"]) if l["esperado"] is not None else None,
                "cobertura": float(l["cobertura"]) if l["cobertura"] is not None else None,
                "classificacao": classificacao,
                "rotulo": {
                    "oferta_observada_baixa": "Oferta observada abaixo da referência",
                    "oferta_observada_compativel": "Oferta observada próxima ou acima da referência",
                    "nao_classificada": "Comparação indisponível",
                }[classificacao],
                "motivo": l["motivo"].replace(".", ","),
                "status_dado": "observado" if l["encontrados"] else "sem_registro_observado",
                "zero_confirmado": cobertura_verificada,
            }
        )

    pop_fonte = consulta_um(
        "SELECT fonte, data_referencia FROM indicador WHERE tipo = 'populacao' ORDER BY data_referencia DESC LIMIT 1"
    )
    ref = seg["por_10k_hab"]
    criterios = [
        {
            "nome": "Base populacional",
            "regra": "População residente usada apenas para normalizar a comparação",
        },
        {
            "nome": "Oferta observada",
            "regra": f"Registros de {seg['nome'].lower()} encontrados na base para a região",
        },
        {
            "nome": "Referência da cidade",
            "regra": f"{_br(ref, 2)} estabelecimentos por 10 mil habitantes no Recife",
        },
        {
            "nome": "Referência proporcional",
            "regra": "Referência × população ÷ 10 mil",
        },
        {
            "nome": "Oferta observada abaixo da referência",
            "regra": (
                f"Referência proporcional de pelo menos {_br(config.analise_min_esperado, 0)} registros "
                f"e oferta observada de até {int(config.analise_cobertura_max * 100)}% dessa referência"
            ),
        },
    ]
    return {
        "segmento": seg,
        "parametros": {
            "min_esperado": config.analise_min_esperado,
            "cobertura_max": config.analise_cobertura_max,
            "referencia_10k": ref,
        },
        "criterios": criterios,
        "resultados": resultados,
        "qualidade_oferta": qualidade_oferta(meta),
        # RN06: fontes usadas no cálculo
        "fontes": [
            {"fonte": pop_fonte["fonte"], "data_texto": _data(pop_fonte["data_referencia"]) or SEM_DATA, "usada_em": ["População"]},
            {"fonte": meta["fonte"], "data_texto": meta["data_referencia"] or SEM_DATA, "usada_em": [f"Estabelecimentos ({seg['nome']})"]},
        ],
        # RN03 / RN04
        "avisos": [AVISO_NAO_RECOMENDACAO, AVISO_APROXIMACAO, AVISO_OFERTA],
    }


def diagnostico(id_categoria: int | None, ids: list[int]) -> dict:
    """Diagnóstico multidimensional; não substitui a rota legada de análise."""
    seg = segmento_valido(id_categoria)
    regioes = regioes_validas(ids, 1, "Selecione ao menos uma região para ver o diagnóstico")
    indicadores_universo = consulta(
        """
        SELECT id_regiao, tipo, valor, data_referencia, fonte
        FROM vw_indicador_completo
        WHERE fonte IS NOT NULL
        """
    )
    ofertas_universo = consulta(
        """
        SELECT id_regiao, quantidade, populacao, por_10k_hab
        FROM vw_oferta_regiao
        WHERE id_categoria = %s
        """,
        (seg["id_categoria"],),
    )
    return montar_diagnostico(seg, regioes, indicadores_universo, ofertas_universo, metadados_oferta())


def _br(numero: float, casas: int) -> str:
    texto = f"{numero:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
