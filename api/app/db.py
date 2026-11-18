"""Pool de conexões com o PostgreSQL.

O pool testa cada conexão antes de entregar (check_connection). Assim, se o
container do banco for reiniciado, a API descarta as conexões quebradas e abre
novas sozinha, sem precisar reiniciar a API também.
"""

from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import config

pool = ConnectionPool(
    conninfo=config.database_url,
    min_size=1,
    max_size=10,
    open=False,
    check=ConnectionPool.check_connection,
    kwargs={"row_factory": dict_row, "application_name": "pontozero-api"},
)


def abrir() -> None:
    pool.open(wait=False)


def fechar() -> None:
    pool.close()


@contextmanager
def conexao():
    """Entrega uma conexão em transação: commit no fim, rollback se der erro."""
    with pool.connection() as conn:
        yield conn


def consulta(sql: str, params=None) -> list[dict]:
    with conexao() as conn:
        return conn.execute(sql, params).fetchall()


def consulta_um(sql: str, params=None) -> dict | None:
    with conexao() as conn:
        return conn.execute(sql, params).fetchone()
