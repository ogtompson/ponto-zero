# Docker no PontoZero, explicado para a equipe

Cada parte abaixo corresponde a uma aula de Infraestrutura de Software e aponta onde ela aparece no projeto.

## 1. Imagem e container (aula "Trabalhando com imagens")

Uma **imagem** é um pacote pronto, com sistema, dependências e código. Um **container** é essa imagem rodando. Temos três imagens:

| Imagem | Base | O que tem dentro |
|---|---|---|
| `pontozero-db` | `postgres:16-alpine` | Postgres + scripts de criação do banco |
| `pontozero-api` | `python:3.12-slim` | Python, FastAPI, Uvicorn, Psycopg e o código da API |
| `pontozero-web` | `nginx:1.27-alpine` | Nginx + o React já compilado |

```bash
docker images | grep pontozero      # imagens baixadas
docker compose ps                   # containers rodando e se estão saudáveis
```

## 2. Construindo imagens (aula "Construindo imagens")

Cada pasta tem um `Dockerfile`:

- [`db/Dockerfile`](../db/Dockerfile): parte do Postgres oficial e copia [`db/init`](../db/init) para `/docker-entrypoint-initdb.d`. O Postgres executa esses scripts sozinho, uma vez, quando o volume está vazio.
- [`api/Dockerfile`](../api/Dockerfile): **build em duas etapas**. A primeira instala as bibliotecas do `requirements.txt`; a segunda copia só o resultado. A imagem roda com um usuário comum, sem root.
- [`web/Dockerfile`](../web/Dockerfile): também em duas etapas. O Node compila o React; a imagem final leva só os arquivos prontos e o Nginx. O Node não vai para a imagem final.

As bibliotecas do Python (FastAPI, Uvicorn, Psycopg, Pydantic) não são do Docker: elas ficam no `requirements.txt` e o Docker instala dentro da imagem da API durante o build.

## 3. Volumes (aula "Volumes de armazenamento")

Container é descartável: o que ele grava some quando é removido. Por isso o banco grava num **volume nomeado**:

```yaml
volumes:
  - pgdata:/var/lib/postgresql/data
```

| Comando | O que acontece com os dados |
|---|---|
| `docker compose stop` / `start` | ficam |
| `docker compose down` / `up -d` | ficam (os containers são recriados, o volume não) |
| `docker compose down -v` | **apagados**: o `-v` remove o volume |

Prova: a tela **Infraestrutura** mostra "volume criado em" (fixo) e "banco ligado desde" (muda a cada religada). O script [`scripts/testar-persistencia.ps1`](../scripts/testar-persistencia.ps1) faz isso automaticamente 3 vezes.

```bash
docker volume ls                       # o volume aparece como pontozero_pgdata
docker volume inspect pontozero_pgdata
```

## 4. Comunicação entre containers (aula "Comunicação entre containers")

O Compose cria redes e um DNS interno: cada serviço é encontrado pelo **nome**.

- O Nginx do `web` repassa `/api` para `http://api:8000` ([`web/nginx.conf`](../web/nginx.conf)).
- A API conecta em `postgresql://...@db:5432/pontozero`.

São duas redes: `rede-app` (web e api) e `rede-dados` (api e db). O `web` não consegue falar com o banco, só a API consegue.

```bash
docker network ls | grep pontozero
docker compose exec api python -c "import socket; print(socket.gethostbyname('db'))"
```

## 5. Docker Compose (aula "Docker Compose")

O [`docker-compose.yml`](../docker-compose.yml) descreve os três serviços persistentes e o job efêmero `migrate`. Pontos que garantem que sobe sem erro:

- `healthcheck` em cada serviço: o Docker pergunta de tempos em tempos se ele está bem.
- `migrate` aplica alterações idempotentes também em volumes existentes e termina antes de a API iniciar.
- `depends_on` com `condition: service_healthy` e `service_completed_successfully`: a API só liga quando banco e schema estão prontos, e o site só liga quando a API responde.
- `restart: unless-stopped`: se um processo cair, o Docker religa.
- Todos os valores têm padrão (`${VAR:-padrão}`), então não precisa de `.env`.

```bash
docker compose up -d          # liga
docker compose ps             # STATUS deve mostrar (healthy)
docker compose logs -f api    # acompanha a API
docker compose restart api    # religa só a API; o site continua respondendo depois
docker compose down           # desliga
```

## 6. Publicar no Docker Hub

Uma vez: crie a conta em hub.docker.com e rode `docker login`.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\publicar.ps1
```

O script constrói as 3 imagens para Intel/AMD e para Mac com chip Apple (arm64) e envia. Depois disso, qualquer pessoa sobe o projeto só com o `docker-compose.yml`, sem o código.

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `port is already allocated` | outro programa usa a 8080 ou a 55432 | crie um arquivo `.env` com `WEB_PORTA=8081` (veja `.env.example`) e suba de novo |
| `pull access denied` | imagens ainda não publicadas | rode o `publicar.ps1` ou suba com `docker-compose.build.yml` |
| api fica `unhealthy` | banco ainda criando ou senha diferente | `docker compose logs db api` |
| mudei os scripts do banco e nada mudou | os scripts só rodam com volume vazio | `docker compose down -v` e `up -d` de novo |
| mapa sem o fundo das ruas | sem internet (o fundo vem do CARTO/OpenStreetMap) | os bairros e dados aparecem mesmo assim |
