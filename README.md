<p align="center">
  <img src="web/public/marca/pontozero.png" alt="PontoZero" width="220" />
</p>

<p align="center">
  Compare bairros do Recife e investigue como a oferta observada do seu segmento se relaciona com a referência municipal.
</p>

<p align="center">
  Projeto final de <b>Infraestrutura de Software</b> e <b>Banco de Dados</b>, CESAR School, 2026.2
</p>

![Oferta observada e referência municipal](docs/img/analise.png)

## Rodar em um comando

Com o Docker Desktop aberto, na pasta do projeto:

```bash
docker compose up -d
```

Abra **http://localhost:8080**. Na primeira vez o Docker baixa as três imagens do Docker Hub e o banco é criado com os dados reais (leva uns 30 segundos).

| Para | Comando |
|---|---|
| Ver se está tudo saudável | `docker compose ps` |
| Ver os logs | `docker compose logs -f` |
| Desligar (os dados ficam) | `docker compose down` |
| Desligar e apagar os dados | `docker compose down -v` |
| Construir a partir do código | `docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build` |

Conta de demonstração: `demo@pontozero.app`, senha `pontozero2026`. Explorar o mapa não exige conta.

O banco também fica acessível no pgAdmin/DBeaver em `localhost:55432` (banco `pontozero`, usuário `pontozero`, senha `pontozero_admin`).

## O que o professor avalia, e onde está

| Requisito | Como está atendido |
|---|---|
| No mínimo 2 imagens: banco e aplicação | 3 imagens: [`db`](db/Dockerfile), [`api`](api/Dockerfile) e [`web`](web/Dockerfile) |
| Imagens no Docker Hub | `ogabrieltenorio/pontozero-db`, `-api` e `-web`, publicadas por [`scripts/publicar.ps1`](scripts/publicar.ps1) |
| Compose que sobe aplicação + banco | [`docker-compose.yml`](docker-compose.yml): sobe só com as imagens, sem precisar do código |
| Subir sem problemas e rodar | `healthcheck` nos 3 serviços e `depends_on: service_healthy`: a API espera o banco, o site espera a API |
| Desligar e religar mantendo os dados | volume nomeado `pgdata`; testado por [`scripts/testar-persistencia.ps1`](scripts/testar-persistencia.ps1) |
| Funcionalidades de Banco de Dados | modelo da equipe com as 9 tabelas, restrições, índices, triggers, views e função de análise: veja [docs/BANCO.md](docs/BANCO.md) |

A matriz completa, com as 10 histórias de usuário do Trello, está em [docs/REQUISITOS.md](docs/REQUISITOS.md). O guia de Docker para a equipe estudar está em [docs/DOCKER.md](docs/DOCKER.md).

## Arquitetura do projeto

```mermaid
flowchart LR
    nav([Navegador]) -->|porta 8080| web["web<br/>Nginx + React"]
    web -->|"/api para api:8000<br/>(rede-app)"| api["api<br/>Python + FastAPI"]
    api -->|"db:5432<br/>(rede-dados)"| db[("db<br/>PostgreSQL 16")]
    db --- vol[("volume pgdata")]
```

- **web** entrega as telas e repassa `/api` para a API. Não enxerga o banco.
- **api** é a única que fala com o banco, com um usuário de permissões mínimas (`pontozero_app`).
- **db** cria tudo sozinho na primeira vez (scripts em [`db/init`](db/init)) e grava no volume `pgdata`.

Pastas:

```
db/        imagem do PostgreSQL: modelo, índices, triggers, views, função e carga de dados
api/       imagem da API (FastAPI): rotas, regras das histórias e testes
web/       imagem do front (React + Vite + Tailwind) servida pelo Nginx
scripts/   publicar no Docker Hub e testar a persistência (Windows e Linux/Mac)
tools/     script que gera a carga de dados a partir das fontes abertas
docs/      documentação do banco, do Docker e da matriz de requisitos
```

## Modelagem do banco

As 9 tabelas seguem o DER da equipe sem mudança de nomes. Detalhes, dicionário de dados e consultas de exemplo em [docs/BANCO.md](docs/BANCO.md).

```mermaid
erDiagram
    EMPRESA ||--o{ USUARIO : possui
    EMPRESA ||--o{ ANALISE : realiza
    ANALISE ||--|{ REGIAO_ANALISE : inclui
    REGIAO ||--o{ REGIAO_ANALISE : "aparece em"
    ANALISE ||--o{ RELATORIO : gera
    REGIAO ||--o{ INDICADOR : possui
    REGIAO ||--o{ ESTABELECIMENTO : possui
    CATEGORIA ||--o{ ESTABELECIMENTO : classifica
```

## Dados reais

| O quê | Fonte | Referência |
|---|---|---|
| Limites e área dos 94 bairros | Prefeitura do Recife, Portal de Dados Abertos | não informada pela fonte |
| População e domicílios por bairro | IBGE, Censo Demográfico 2022 (SIDRA 9923 e 9922) | 31/07/2022 |
| Renda média domiciliar por bairro | IBGE, Censo Demográfico 2010 (SIDRA 3345) | 31/07/2010 |
| 532 estabelecimentos de 6 segmentos | OpenStreetMap, licença ODbL | extração de 17/11/2026 |

A cobertura do OpenStreetMap é parcial, e a tela avisa isso. Os dados brutos coletados estão em `tools/dados/`; para regenerar a carga do banco, rode `pip install shapely bcrypt` e depois [`python tools/gerar_carga.py`](tools/gerar_carga.py).

## Desenvolvimento sem Docker

```bash
# banco: qualquer Postgres 16 com os scripts de db/init
cd api && pip install -r requirements-dev.txt
DATABASE_URL=postgresql://pontozero_app:pontozero_app@localhost:55432/pontozero uvicorn app.main:app --reload
python -m pytest -q tests          # 14 testes, um por critério das histórias

cd web && npm install && npm run dev   # http://localhost:5173 (repassa /api para :8000)
```

Documentação interativa da API: http://localhost:8080/api/docs

## Interface

Componentes do registro **[21st.dev](https://21st.dev)**: `shadcn/button`, `dialog`, `tabs`, `tooltip`, `popover`, `command`, `dropdown-menu`, `toggle-group`, `scroll-area`, `sonner` e outros, mais `number-ticker` e `animated-beam` da Magic UI. Cada arquivo em [`web/src/components/ui`](web/src/components/ui) cita a origem. Para trazer outro:

```bash
cd web
npx shadcn@latest add "https://21st.dev/r/dillionverma/number-ticker"
```

Tipografia: Archivo (variável, com eixo de largura). Cores da marca: marinho `#19214A` e ouro `#DDBA43`.

## Equipe 2

| Pessoa | Papel |
|---|---|
| Davi Nogueira | Product Owner |
| Guilherme Agra | Scrum Master |
| Renato Lopes | Banco de dados, dados e full stack |
| Vinícius Cardoso | Back-end |
| Leandro Langlois | Back-end |
| Gabriel Tenório | Docker e back-end |
| Pedro Paes | Front-end |
| Caio Marques | Front-end e QA |
| Paulo Henrique | Desenvolvimento |

<p>
  <img src="web/public/marca/cesar-school.png" alt="CESAR School" width="56" />
</p>
