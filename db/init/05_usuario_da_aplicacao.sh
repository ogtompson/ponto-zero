#!/bin/sh
# =====================================================================
# PontoZero | 05 - Usuário do banco usado pela API (menor privilégio)
#
# A API não usa o superusuário do Postgres. Ela conecta com um usuário
# próprio que só lê os dados de referência e só escreve nas tabelas que
# a aplicação realmente altera (empresa, usuario, analise, regiao_analise
# e relatorio). Nome e senha vêm das variáveis de ambiente do compose.
# =====================================================================
set -e

APP_USER="${APP_DB_USER:-pontozero_app}"
APP_PASS="${APP_DB_PASSWORD:-pontozero_app}"

psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" \
     --dbname "$POSTGRES_DB" \
     -v app_user="$APP_USER" \
     -v app_pass="$APP_PASS" \
     -v db_name="$POSTGRES_DB" <<'EOSQL'
CREATE ROLE :"app_user" LOGIN PASSWORD :'app_pass';

GRANT CONNECT ON DATABASE :"db_name" TO :"app_user";
GRANT USAGE ON SCHEMA public TO :"app_user";

-- leitura de tudo (tabelas e views)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO :"app_user";

-- escrita só onde a aplicação grava
GRANT INSERT, UPDATE, DELETE ON empresa, usuario, analise, regiao_analise, relatorio TO :"app_user";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO :"app_user";

-- função da análise (HU-009)
GRANT EXECUTE ON FUNCTION fn_analise_demanda_oferta(INT, INT[], NUMERIC, NUMERIC) TO :"app_user";
EOSQL

# Marca no próprio banco quando o volume foi criado. A tela Infraestrutura
# mostra essa data: ela não muda quando os containers são desligados e
# religados, o que prova que os dados vêm do volume persistente.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -c "COMMENT ON DATABASE \"$POSTGRES_DB\" IS 'inicializado_em=$(date -u +%Y-%m-%dT%H:%M:%SZ)'"

echo "PontoZero: usuário da aplicação '$APP_USER' criado com permissões mínimas."
