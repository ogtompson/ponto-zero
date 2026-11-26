# =====================================================================
# Imagem 1 de 3: banco de dados do PontoZero (PostgreSQL 16)
#
# Partimos da imagem oficial do Postgres e copiamos os scripts de
# criação. O Postgres executa tudo o que está em /docker-entrypoint-initdb.d
# em ordem alfabética, mas só na primeira inicialização (volume vazio).
# =====================================================================
FROM postgres:16-alpine

LABEL org.opencontainers.image.title="pontozero-db" \
      org.opencontainers.image.description="Banco PostgreSQL do PontoZero: modelo, views, função de análise e carga de dados reais" \
      org.opencontainers.image.vendor="Equipe PontoZero - CESAR School"

# valores padrão; o docker-compose.yml pode sobrescrever
ENV POSTGRES_DB=pontozero \
    POSTGRES_USER=pontozero \
    LANG=C.UTF-8

# Ordem de execução (alfabética) na primeira subida com volume vazio:
#   01_ddl.sql                  tabelas, tipos e restrições  (db/ddl.sql)
#   02_indices_e_regras.sql     índices de desempenho e triggers
#   03_views_e_funcoes.sql      views e função da análise
#   04_seed_dml.sql             povoamento inicial            (db/seed_dml.sql)
#   05_usuario_da_aplicacao.sh  usuário da API com permissões mínimas
# ddl.sql e seed_dml.sql são os arquivos de entrega; aqui só ganham o número
# que garante a ordem, sem cópia duplicada no repositório.
COPY ddl.sql      /docker-entrypoint-initdb.d/01_ddl.sql
COPY init/        /docker-entrypoint-initdb.d/
COPY seed_dml.sql /docker-entrypoint-initdb.d/04_seed_dml.sql
# remove o "\r" caso os arquivos tenham passado por um Windows (CRLF quebra o .sh)
RUN sed -i 's/\r$//' /docker-entrypoint-initdb.d/* \
 && chmod 0755 /docker-entrypoint-initdb.d/*.sh

# o compose usa este teste para só ligar a API quando o banco estiver pronto
HEALTHCHECK --interval=5s --timeout=3s --start-period=20s --retries=12 \
  CMD pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h 127.0.0.1 || exit 1

EXPOSE 5432
