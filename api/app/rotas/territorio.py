"""Rotas públicas de exploração (HU-003 a HU-009 funcionam sem login)."""

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Query, Response

from ..servicos import territorio as t
from ..servicos.perfis_segmento import listar_perfis

router = APIRouter(tags=["território"])

GEOJSON = Path(__file__).resolve().parents[1] / "data" / "bairros-recife.geojson"


@router.get("/segmentos", summary="Segmentos com dados no piloto (HU-004)")
def segmentos():
    return t.listar_segmentos()


@router.get("/segmentos/catalogo", summary="Catálogo e maturidade analítica dos segmentos")
def catalogo_segmentos():
    return listar_perfis()


@router.get("/regioes", summary="Regiões disponíveis, com população e renda")
def regioes():
    return t.listar_regioes()


@lru_cache(maxsize=1)
def _mapa_texto() -> str:
    geo = json.loads(GEOJSON.read_text(encoding="utf-8"))
    por_nome = {r["nome"]: r for r in t.listar_regioes()}
    for f in geo["features"]:
        r = por_nome.get(f["properties"]["nome"])
        f["properties"]["id_regiao"] = r["id_regiao"] if r else None
    return json.dumps(geo, ensure_ascii=False, separators=(",", ":"))


@router.get("/mapa/bairros", summary="Polígonos dos bairros para o mapa (HU-003)")
def mapa_bairros():
    return Response(
        content=_mapa_texto(),
        media_type="application/geo+json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/indicadores", summary="Indicadores das regiões selecionadas (HU-005 e HU-007)")
def indicadores(regioes: str = Query(..., description="ids separados por vírgula")):
    return t.indicadores(t.ids_da_query(regioes))


@router.get("/oferta", summary="Estabelecimentos do segmento e concentração (HU-006)")
def oferta(segmento: int | None = None, regioes: str | None = None):
    return t.oferta(segmento, t.ids_da_query(regioes))


@router.get("/oferta/mapa", summary="Oferta por 10 mil habitantes em todos os bairros")
def oferta_mapa(segmento: int):
    return t.oferta_mapa(segmento)


@router.get("/comparacao", summary="Comparação lado a lado (HU-008)")
def comparacao(regioes: str, segmento: int | None = None):
    return t.comparacao(segmento, t.ids_da_query(regioes))


@router.get("/analise", summary="Oferta formal e referência municipal (HU-009)")
def analise(segmento: int | None = None, regioes: str | None = None):
    return t.analise(segmento, t.ids_da_query(regioes))


@router.get("/diagnostico", summary="Diagnóstico territorial por dimensões")
def diagnostico(segmento: int | None = None, regioes: str | None = None):
    return t.diagnostico(segmento, t.ids_da_query(regioes))
