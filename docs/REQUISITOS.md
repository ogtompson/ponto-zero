# Matriz de requisitos

Cada linha diz onde o requisito está no código e como verificar. Os testes automáticos ficam em [`api/tests/test_api.py`](../api/tests/test_api.py) e rodam contra o banco real.

## Infraestrutura de Software (Prof. Leonardo Farias)

| Requisito | Onde | Como verificar |
|---|---|---|
| Imagem do banco | [`db/Dockerfile`](../db/Dockerfile) | `docker images` mostra `pontozero-db` |
| Imagem da aplicação | [`api/Dockerfile`](../api/Dockerfile) e [`web/Dockerfile`](../web/Dockerfile) | `pontozero-api` e `pontozero-web` |
| Imagens no Docker Hub | [`scripts/publicar.ps1`](../scripts/publicar.ps1) | hub.docker.com/r/ogabrieltenorio/pontozero-db (e -api, -web) |
| Compose sobe aplicação com banco | [`docker-compose.yml`](../docker-compose.yml) | `docker compose up -d` e abrir http://localhost:8080 |
| Sobe sem problemas e roda | healthchecks + `depends_on: service_healthy` | `docker compose ps` mostra os 3 `(healthy)` |
| Desligar e religar várias vezes mantendo os dados | volume `pgdata` | [`scripts/testar-persistencia.ps1`](../scripts/testar-persistencia.ps1) faz 3 ciclos de `down`/`up` e confere login e análise salvos |
| Funcionalidades de Banco de Dados funcionando | ver seção abaixo | tela Explorar e [docs/BANCO.md](BANCO.md) |

Extras que a disciplina cobre: build em duas etapas (api e web), usuário sem root na API, duas redes isoladas, DNS interno entre containers, imagens para amd64 e arm64, tela Infraestrutura com o estado dos containers ao vivo.

## Banco de Dados (Prof. Robson)

| Item | Onde |
|---|---|
| As 9 tabelas do DER, com os mesmos nomes | [`01_schema.sql`](../db/init/01_schema.sql) |
| Chaves primárias, estrangeiras e cardinalidades | `01_schema.sql` (ver tabela de cardinalidades em BANCO.md) |
| Restrições (UNIQUE, CHECK, NOT NULL) | `01_schema.sql` |
| Índices | [`02_indices_e_regras.sql`](../db/init/02_indices_e_regras.sql) |
| Triggers (e-mail em minúsculas, data da análise) | `02_indices_e_regras.sql` |
| Views | [`03_views_e_funcoes.sql`](../db/init/03_views_e_funcoes.sql) |
| Função SQL com a regra de negócio da HU-009 | `fn_analise_demanda_oferta` em `03_views_e_funcoes.sql` |
| Carga de dados reais | [`04_carga_dados.sql`](../db/init/04_carga_dados.sql), gerado por [`tools/gerar_carga.py`](../tools/gerar_carga.py) |
| Usuário com menor privilégio | [`05_usuario_da_aplicacao.sh`](../db/init/05_usuario_da_aplicacao.sh) |
| CRUD pela aplicação | cadastro (C), análises salvas (C, R, D), relatórios (C) |

## Histórias de usuário (Trello)

| HU | Critério de aceite | Onde | Teste |
|---|---|---|---|
| 001 Cadastro | e-mail e senha válidos criam a conta | `POST /api/auth/cadastro`, aba "Criar conta" | `test_conta_completa` |
| 001 | e-mail já cadastrado é recusado com "Este e-mail já está em uso." | rota + índice único em `lower(email)` | `test_conta_completa` |
| 001 | e-mail inválido e senha com menos de 8 caracteres mostram o erro no campo | validação na tela e na API | `test_conta_completa` |
| 001 RN01 | cadastro opcional: nada do mapa depende dele | rotas de território são públicas | todos os testes de território rodam sem login |
| 002 Login | credenciais corretas entram | `POST /api/auth/login` (sessão em cookie httpOnly) | `test_conta_completa` |
| 002 | credenciais erradas: "E-mail ou senha inválidos", sem dizer qual campo | mesma mensagem nos dois casos | `test_conta_completa` |
| 002 | sair encerra a sessão | `POST /api/auth/logout` apaga o cookie | `test_conta_completa` |
| 002 | campos vazios bloqueiam o envio e indicam o campo | `DialogoConta.tsx` | manual |
| 003 Mapa | mapa com os 94 bairros, clicar seleciona | `Mapa.tsx`, `GET /api/mapa/bairros` | `test_mapa_tem_todos_os_bairros_com_id` |
| 004 Filtros | só segmentos com dados | `GET /api/segmentos` | `test_segmentos_so_com_dados` |
| 004 | trocar o segmento atualiza oferta e análise sem recarregar | estado na URL + React Query | manual |
| 004 | regiões escolhidas no filtro aparecem destacadas no mapa (e vice-versa) | mesma seleção em `selecao.tsx` | manual |
| 004 | sem segmento: oferta e análise pedem para escolher um | abas Oferta e Oferta x referência | `test_oferta_exige_segmento` |
| 005 Indicadores | nome, valor e unidade | `vw_indicador_completo`, aba Indicadores | `test_indicadores_tem_valor_unidade_fonte_e_data` |
| 005 | sem dado aparece "indisponível", nunca zero | API devolve `null` + texto na tela | `test_indicador_sem_dado_aparece_indisponivel` |
| 005 | aviso de aproximação visível | topo da aba Indicadores e na Comparação | `test_indicadores_tem_valor_unidade_fonte_e_data` |
| 006 Oferta | estabelecimentos do segmento no mapa | camada dourada no mapa, `GET /api/oferta` | `test_oferta_mesma_metrica_e_mensagem_sem_estabelecimento` |
| 006 | concentração com a mesma métrica para todas as regiões | "por 10 mil habitantes" | mesmo teste |
| 006 | sem registro observado: informa cobertura parcial e não apresenta zero como ausência confirmada | aba Oferta | mesmo teste |
| 006 | fonte, data e aviso de cobertura | lateral da aba Oferta | mesmo teste |
| 007 Fontes | cada indicador mostra fonte e data, ou "data de referência não informada" | botão (i) ao lado de cada valor | `test_indicadores_tem_valor_unidade_fonte_e_data` |
| 007 | a análise lista as fontes e a qualidade da cobertura usadas no cálculo | aba Oferta x referência | `test_analise_qualifica_oferta_observada_e_mostra_fontes` |
| 007 | sem fonte o indicador não aparece | `fonte NOT NULL` no banco | restrição do banco |
| 008 Comparação | duas ou mais regiões lado a lado | aba Comparar | `test_comparacao_mantem_ordem_sem_ranking` |
| 008 | uma região só: "Selecione ao menos duas regiões para comparar" | aba e API | `test_comparacao_bloqueia_uma_regiao` |
| 008 | sem ranking nem pontuação | colunas na ordem em que o usuário escolheu | `test_comparacao_mantem_ordem_sem_ranking` |
| 008 | limite de regiões (era pendente) | definido em 8 | `MAX_REGIOES` na API e no front |
| 009 Análise | exige segmento e duas regiões | aba e API | `test_analise_exige_segmento_e_duas_regioes` |
| 009 | regras e critérios visíveis | painel "Como a análise é feita" | `test_analise_qualifica_oferta_observada_e_mostra_fontes` |
| 009 | resultado descreve somente a oferta observada em relação à referência municipal | `fn_analise_demanda_oferta` + API | mesmo teste |
| 009 | aviso de que não é recomendação de investimento | destaque no topo da aba, no PDF e no CSV | mesmo teste |
| 009 | região com dado faltando: "não classificada" com o motivo | função SQL | regra na função |
| 009 | sem ranking, recomendação, previsão ou alegação de demanda | nenhuma ordenação ou nota | revisão |
| 009 | limiares (eram pendentes) | esperado ≥ 2 e cobertura ≤ 50%, configuráveis por variável de ambiente | `config.py` |
| 010 Exportar | gera arquivo com a tela, fontes e avisos | botão Exportar: PDF ou CSV | `test_exportacao_csv_tem_fontes_e_avisos` |
| 010 | sem análise na tela, a ação fica indisponível | botão desabilitado + API recusa | `test_exportacao_sem_analise_fica_indisponivel` |
| 010 | falha na geração: mensagem e nova tentativa | aviso com botão "Tentar de novo" | manual |
| 010 | exportar uma análise salva registra em RELATORIO | `POST /api/exportacoes` com `id_analise` | `test_conta_completa` |
| 010 | análise salva preserva segmento, dados, fontes e versão da metodologia | `analise.snapshot` em JSONB | `test_conta_completa` |
| 010 | exportação de análise salva usa o snapshot, mesmo se os filtros enviados forem diferentes | API prioriza `id_analise` autenticado | `test_conta_completa` |

## Decisões que a equipe pode querer rever

- **Segmento da análise salva.** `ANALISE.id_categoria` registra o segmento estudado sem limitar a empresa a um único tipo de pesquisa.
- **Rastreabilidade.** Novas análises guardam um snapshot JSONB e a versão da metodologia. Registros anteriores à migração são identificados como legados e continuam consultáveis.
- **Unidade do indicador.** O DER não tem coluna de unidade; ela vem da view `vw_catalogo_indicador`.
- **Fonte da oferta.** ESTABELECIMENTO não tem coluna de fonte; a fonte e a data da extração ficam no comentário da tabela (`COMMENT ON TABLE`), lido pela API.
