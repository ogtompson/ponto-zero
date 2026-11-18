"""Saúde e status da infraestrutura (usado pelo healthcheck e pela tela Infraestrutura)."""

import os
import platform
import socket
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..config import config
from ..db import conexao

router = APIRouter(tags=["sistema"])

INICIO_API = datetime.now(timezone.utc)

TABELAS = [
    "empresa", "usuario", "analise", "regiao_analise", "relatorio",
    "regiao", "indicador", "estabelecimento", "categoria",
]


@router.get("/health", summary="Healthcheck do container da API")
def health():
    try:
        with conexao() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok"}
    except Exception:  # noqa: BLE001
        return JSONResponse(status_code=503, content={"status": "sem banco"})


@router.get("/status", summary="Status dos containers e do volume de dados")
def status():
    api = {
        "versao": config.versao,
        "container": socket.gethostname(),
        "python": platform.python_version(),
        "iniciada_em": INICIO_API.isoformat(),
        "segundos_no_ar": int((datetime.now(timezone.utc) - INICIO_API).total_seconds()),
        "processo": os.getpid(),
    }
    try:
        with conexao() as conn:
            info = conn.execute(
                """
                SELECT version() AS versao,
                       current_database() AS banco,
                       current_user AS usuario,
                       host(inet_server_addr()) AS ip,
                       pg_postmaster_start_time() AS ligado_em,
                       pg_size_pretty(pg_database_size(current_database())) AS tamanho,
                       shobj_description(
                           (SELECT oid FROM pg_database WHERE datname = current_database()),
                           'pg_database'
                       ) AS comentario
                """
            ).fetchone()
            contagens = {}
            for tabela in TABELAS:
                contagens[tabela] = conn.execute(f"SELECT count(*) AS n FROM {tabela}").fetchone()["n"]
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=503, content={"api": api, "banco": None, "erro": str(exc)[:200]})

    inicializado = None
    for parte in (info["comentario"] or "").split(";"):
        if parte.startswith("inicializado_em="):
            inicializado = parte.split("=", 1)[1]

    return {
        "api": api,
        "banco": {
            "versao": info["versao"].split(" on ")[0],
            "nome": info["banco"],
            "usuario": info["usuario"],
            "ip": info["ip"],
            "ligado_em": info["ligado_em"].isoformat(),
            "volume_inicializado_em": inicializado,
            "tamanho": info["tamanho"],
            "contagens": contagens,
        },
    }
