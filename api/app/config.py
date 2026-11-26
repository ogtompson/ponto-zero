"""Configurações lidas das variáveis de ambiente (definidas no docker-compose.yml)."""

import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Config:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://pontozero_app:pontozero_app@db:5432/pontozero"
    )
    jwt_segredo: str = os.getenv("JWT_SECRET", "pontozero-dev-local-troque-em-producao-2026")
    sessao_horas: int = int(os.getenv("SESSAO_HORAS", "8"))
    cookie_seguro: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    versao: str = os.getenv("APP_VERSION", "1.0.0")
    fuso: ZoneInfo = ZoneInfo(os.getenv("TZ", "America/Recife") or "America/Recife")

    # Regra da HU-009 (limiares visíveis na tela e no relatório)
    analise_min_esperado: float = float(os.getenv("ANALISE_MIN_ESPERADO", "2"))
    analise_cobertura_max: float = float(os.getenv("ANALISE_COBERTURA_MAX", "0.5"))


config = Config()

METODOLOGIA_VERSAO = "2026.11.4"

AVISO_APROXIMACAO = (
    "População, renda e número de estabelecimentos são aproximações e, sozinhos, "
    "não demonstram demanda não atendida."
)
AVISO_OFERTA = (
    "A oferta contabiliza empresas formais ativas nos CNAEs definidos para cada segmento. "
    "Ela não inclui informalidade e o recorte CNAE pode abranger atividades similares."
)
AVISO_NAO_RECOMENDACAO = (
    "Este resultado não é recomendação definitiva de investimento e não substitui "
    "um estudo de viabilidade."
)
SEM_DATA = "data de referência não informada"
