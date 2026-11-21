"""Coleta e qualifica a oferta formal dos segmentos do PontoZero.

A fonte é o recurso "Empresas Ativas do Recife", da Secretaria de Finanças.
O script consulta somente os CNAEs declarados no catálogo do produto, preserva
uma cópia bruta ignorada pelo Git e gera um snapshot compacto e reproduzível.

Uso:
    python tools/coletar_empresas_recife.py
    python tools/coletar_empresas_recife.py --cache
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from shapely.geometry import Point, shape
from shapely.strtree import STRtree


RAIZ = Path(__file__).resolve().parents[1]
CATALOGO = RAIZ / "api" / "app" / "data" / "catalogo-segmentos.json"
DADOS_BASE = RAIZ / "tools" / "dados" / "pontozero-dados.json"
SAIDA = RAIZ / "tools" / "dados" / "empresas-recife-segmentos.json"
SAIDA_QUALIDADE_API = RAIZ / "api" / "app" / "data" / "qualidade-oferta.json"
CACHE = RAIZ / "tools" / "dados" / "externos" / "empresas-recife"

PORTAL = "https://dados.recife.pe.gov.br"
PACOTE = "empresas-da-cidade-do-recife"
RECURSO = "6d5e72aa-3f4b-4dc3-817c-0e0305cef538"
URL_RECURSO = f"{PORTAL}/pt_PT/dataset/{PACOTE}/resource/{RECURSO}"
LIMITE = 5000
CAMPOS = (
    "cnpj",
    "razao_social",
    "nome_fantasia",
    "nome_logradouro",
    "numero_residencia",
    "numero_lote",
    "nome_bairro",
    "situacao_empresa",
    "data_abertura_empresa",
    "cnae",
    "desc_atividade",
    "atividade_principal",
    "latitude",
    "longitude",
)

_APELIDOS_BAIRRO = {
    "cohab": "cohab ibura de cima",
    "cohab ibura de cima": "cohab ibura de cima",
    "recife antigo": "recife",
}


def normalizar(texto: str | None) -> str:
    valor = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    chave = re.sub(r"[^a-z0-9]+", " ", valor).strip()
    return _APELIDOS_BAIRRO.get(chave, chave)


def codigo_numerico(codigo: str) -> int:
    return int(re.sub(r"\D", "", codigo))


def _obter_json(url: str) -> dict:
    pedido = urllib.request.Request(url, headers={"User-Agent": "PontoZero/1.0 (projeto academico)"})
    with urllib.request.urlopen(pedido, timeout=120) as resposta:
        return json.load(resposta)


def metadados_recurso() -> dict:
    url = f"{PORTAL}/api/3/action/package_show?id={urllib.parse.quote(PACOTE)}"
    resposta = _obter_json(url)
    recurso = next(item for item in resposta["result"]["resources"] if item["id"] == RECURSO)
    return {
        "titulo": recurso["name"].strip(),
        "resource_id": RECURSO,
        "url": URL_RECURSO,
        "licenca": "Open Data Commons Open Database License (ODbL)",
        "atualizado_em": recurso["last_modified"],
        "tamanho_bytes": recurso.get("size"),
        "frequencia": "mensal",
        "responsavel": "Secretaria de Finanças do Recife",
    }


def coletar_cnae(cnae: int, usar_cache: bool = False) -> list[dict]:
    arquivo = CACHE / f"{cnae}.json"
    if usar_cache and arquivo.exists():
        return json.loads(arquivo.read_text(encoding="utf-8"))

    registros: list[dict] = []
    offset = 0
    while True:
        filtros = json.dumps({"cnae": cnae}, separators=(",", ":"))
        parametros = urllib.parse.urlencode(
            {
                "resource_id": RECURSO,
                "limit": LIMITE,
                "offset": offset,
                "fields": ",".join(CAMPOS),
                "filters": filtros,
            }
        )
        resultado = _obter_json(f"{PORTAL}/api/3/action/datastore_search?{parametros}")["result"]
        lote = resultado["records"]
        registros.extend(lote)
        offset += len(lote)
        if not lote or offset >= resultado["total"]:
            break

    CACHE.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps(registros, ensure_ascii=False), encoding="utf-8")
    return registros


def carregar_bairros() -> tuple[list[dict], STRtree, dict[str, int]]:
    bruto = json.loads(DADOS_BASE.read_text(encoding="utf-8"))
    bairros = []
    for feicao in bruto["bairros_geojson"]["features"]:
        propriedades = feicao["properties"]
        nome = (propriedades.get("EBAIRRNOMEOF") or propriedades.get("EBAIRRNOME")).strip()
        geometria = shape(feicao["geometry"])
        if not geometria.is_valid:
            geometria = geometria.buffer(0)
        bairros.append({"nome": nome, "chave": normalizar(nome), "geom": geometria})
    arvore = STRtree([bairro["geom"] for bairro in bairros])
    por_nome = {bairro["chave"]: indice for indice, bairro in enumerate(bairros)}
    return bairros, arvore, por_nome


def bairro_do_ponto(
    latitude: float | int | None,
    longitude: float | int | None,
    bairros: list[dict],
    arvore: STRtree,
) -> tuple[int | None, float | None, float | None]:
    def casas_decimais(valor: object) -> int:
        texto = str(valor)
        return len(texto.rsplit(".", 1)[1]) if "." in texto else 0

    try:
        lat, lon = float(latitude), float(longitude)
    except (TypeError, ValueError):
        return None, None, None
    # O recurso municipal de novembro/2026 expõe muitas coordenadas com apenas
    # uma casa decimal. Elas localizam a cidade, mas não um estabelecimento.
    if casas_decimais(latitude) < 3 or casas_decimais(longitude) < 3:
        return None, None, None
    if not (-8.2 <= lat <= -7.9 and -35.1 <= lon <= -34.8):
        return None, None, None
    ponto = Point(lon, lat)
    for indice in arvore.query(ponto):
        if bairros[indice]["geom"].covers(ponto):
            return int(indice), round(lat, 6), round(lon, 6)
    return None, None, None


def _melhor_registro(registros: Iterable[dict]) -> dict:
    def prioridade(item: dict) -> tuple[bool, bool, bool]:
        coordenada = bool(item.get("latitude") and item.get("longitude"))
        return item.get("atividade_principal") == "S", coordenada, bool(item.get("nome_fantasia"))

    return max(registros, key=prioridade)


def _nome(registro: dict) -> str:
    def utilizavel(valor: object) -> bool:
        texto = str(valor or "").strip()
        return len(texto) >= 2 and texto not in {"-", ".", "..", "N/A"}

    fantasia = registro.get("nome_fantasia")
    razao = registro.get("razao_social")
    return str(fantasia if utilizavel(fantasia) else razao if utilizavel(razao) else "Empresa sem nome fantasia").strip()


def _endereco(registro: dict) -> str | None:
    logradouro = (registro.get("nome_logradouro") or "").strip()
    numero = (registro.get("numero_residencia") or registro.get("numero_lote") or "").strip()
    if not logradouro:
        return None
    return f"{logradouro}, {numero}" if numero else logradouro


def processar_segmento(
    perfil: dict,
    registros: list[dict],
    bairros: list[dict],
    arvore: STRtree,
    bairros_por_nome: dict[str, int],
) -> tuple[list[dict], dict]:
    ativos = [item for item in registros if item.get("situacao_empresa") == "ATIVO"]
    por_cnpj: dict[str, list[dict]] = defaultdict(list)
    invalidos = 0
    for item in ativos:
        cnpj = re.sub(r"\D", "", item.get("cnpj") or "")
        if len(cnpj) != 14:
            invalidos += 1
            continue
        por_cnpj[cnpj].append(item)

    saida = []
    qualidade = {
        "linhas_fonte": len(registros),
        "linhas_ativas": len(ativos),
        "cnpjs_unicos": len(por_cnpj),
        "cnpjs_invalidos": invalidos,
        "coordenadas_informadas": 0,
        "coordenadas_precisas": 0,
        "associados_espacialmente": 0,
        "associados_por_bairro_declarado": 0,
        "divergencias_bairro": 0,
        "descartados_sem_bairro": 0,
        "registros_carregados": 0,
    }

    for cnpj, atividades in por_cnpj.items():
        registro = _melhor_registro(atividades)
        if registro.get("latitude") and registro.get("longitude"):
            qualidade["coordenadas_informadas"] += 1
        indice_espacial, lat, lon = bairro_do_ponto(
            registro.get("latitude"), registro.get("longitude"), bairros, arvore
        )
        indice_declarado = bairros_por_nome.get(normalizar(registro.get("nome_bairro")))
        if indice_espacial is not None:
            indice = indice_espacial
            qualidade["coordenadas_precisas"] += 1
            qualidade["associados_espacialmente"] += 1
            if indice_declarado is not None and indice_declarado != indice_espacial:
                qualidade["divergencias_bairro"] += 1
        elif indice_declarado is not None:
            indice = indice_declarado
            qualidade["associados_por_bairro_declarado"] += 1
        else:
            qualidade["descartados_sem_bairro"] += 1
            continue

        nome = _nome(registro)
        cnaes = sorted({int(item["cnae"]) for item in atividades})
        saida.append(
            {
                "cnpj": cnpj,
                "nome": nome[:100],
                "endereco": (_endereco(registro) or "")[:255] or None,
                "bairro": bairros[indice]["nome"],
                "bairro_declarado": (registro.get("nome_bairro") or "").strip() or None,
                "latitude": lat,
                "longitude": lon,
                "data_abertura": (registro.get("data_abertura_empresa") or "")[:10] or None,
                "cnaes": cnaes,
                "atividade_principal": next(
                    (int(item["cnae"]) for item in atividades if item.get("atividade_principal") == "S"), None
                ),
                "segmento": perfil["nome"],
            }
        )

    saida.sort(key=lambda item: (normalizar(item["bairro"]), normalizar(item["nome"]), item["cnpj"]))
    qualidade["registros_carregados"] = len(saida)
    return saida, qualidade


def executar(usar_cache: bool = False) -> dict:
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    perfis = [item for item in catalogo["segmentos"] if item.get("disponibilidade") == "piloto"]
    bairros, arvore, por_nome = carregar_bairros()
    codigos = sorted(
        {codigo_numerico(cnae["codigo"]) for perfil in perfis for cnae in perfil.get("cnaes_oferta", [])}
    )
    por_cnae = {codigo: coletar_cnae(codigo, usar_cache) for codigo in codigos}

    estabelecimentos = []
    qualidade = {}
    for perfil in perfis:
        registros = [
            registro
            for cnae in perfil["cnaes_oferta"]
            for registro in por_cnae[codigo_numerico(cnae["codigo"])]
        ]
        processados, metricas = processar_segmento(perfil, registros, bairros, arvore, por_nome)
        estabelecimentos.extend(processados)
        qualidade[perfil["slug"]] = metricas

    meta = metadados_recurso()
    documento = {
        "metadados": {
            **meta,
            "coletado_em": datetime.now(UTC).isoformat(timespec="seconds"),
            "catalogo_segmentos": catalogo["versao"],
            "metodologia": "CNPJ único por categoria; bairro por junção espacial quando há coordenada válida, senão bairro declarado pela fonte.",
            "observacao": "OpenStreetMap não participa das contagens; permanece apenas como fonte cartográfica complementar.",
        },
        "qualidade": qualidade,
        "estabelecimentos": estabelecimentos,
    }
    SAIDA.write_text(json.dumps(documento, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    SAIDA_QUALIDADE_API.write_text(
        json.dumps(
            {
                "metadados": documento["metadados"],
                "segmentos": qualidade,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return documento


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", action="store_true", help="reutiliza respostas brutas já coletadas")
    argumentos = parser.parse_args()
    resultado = executar(argumentos.cache)
    print(f"snapshot: {SAIDA}")
    print(f"estabelecimentos carregáveis: {len(resultado['estabelecimentos'])}")
    for segmento, metricas in resultado["qualidade"].items():
        print(
            f"{segmento}: {metricas['cnpjs_unicos']} CNPJs; "
            f"{metricas['registros_carregados']} associados; "
            f"{metricas['coordenadas_precisas']} com coordenada precisa"
        )


if __name__ == "__main__":
    main()
