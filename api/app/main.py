"""PontoZero API: inteligência territorial para escolher onde abrir um negócio.

Todas as rotas ficam sob /api. O Nginx do container web encaminha /api para
este container pela rede interna do Docker Compose.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import db
from .config import config
from .rotas import analises, auth, exportacao, sistema, territorio


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    db.abrir()
    yield
    db.fechar()


app = FastAPI(
    title="PontoZero API",
    version=config.versao,
    description="Mapa, indicadores, oferta comercial, comparação e análise de demanda x oferta dos bairros do Recife.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
    lifespan=ciclo_de_vida,
)


@app.exception_handler(RequestValidationError)
async def validacao(_: Request, exc: RequestValidationError):
    primeiro = exc.errors()[0] if exc.errors() else {}
    campo = str(primeiro.get("loc", ["", ""])[-1]) if primeiro else None
    return JSONResponse(
        status_code=422,
        content={"detail": {"mensagem": "Confira os dados enviados.", "campo": campo}},
    )


for modulo in (sistema, territorio, auth, analises, exportacao):
    app.include_router(modulo.router, prefix="/api")
