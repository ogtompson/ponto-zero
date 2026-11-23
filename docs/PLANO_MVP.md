# Plano de estabilização do MVP

**Revisão:** 23 de novembro de 2026

**Marco atual:** estabilização e ensaio para a apresentação final

## 1. Resultado esperado

Na apresentação, o PontoZero precisa demonstrar um ciclo completo e compreensível:

```text
objetivo do usuário
→ segmento
→ território
→ evidências confiáveis
→ comparação explicada
→ próximos passos
→ análise salva
```

O professor deve conseguir reconhecer três qualidades:

- o produto resolve uma pergunta concreta de localização comercial;
- os números têm fonte, cobertura e interpretação defensáveis;
- a aplicação funciona como um sistema integrado, não como uma sequência de telas montadas para demonstração.

## 2. Diagnóstico consolidado

### Feedback da apresentação de 21/11

| Feedback | Decisão | Prioridade |
|---|---|---|
| Testar Google Maps | Fazer um *spike* isolado com Maps JavaScript API e, se necessário, Places API. A API exige chave e faturamento; a franquia gratuita não elimina controle de cota, segurança da chave e custo potencial. Não substituir o mapa atual antes de comparar legibilidade, integração com GeoJSON, licença e custo. | P1 |
| Avaliar Folium | Usar apenas como alternativa para protótipos analíticos, notebooks ou mapas estáticos incorporados. Folium gera Leaflet/HTML no Python e não substitui diretamente o mapa interativo React/Leaflet já integrado ao estado da aplicação. | P2 |
| Retirar CESAR School | Remover marca, nome da instituição e texto de “projeto acadêmico” da experiência do produto. Manter créditos acadêmicos somente na documentação ou no material da disciplina, fora do fluxo do usuário. | P0 |
| Mapa excessivamente azul | Revisar separadamente o mapa-base e as escalas temáticas. Preservar marinho e ouro como identidade da interface, mas adotar paletas cartográficas distintas e acessíveis para população, renda e oferta, sem usar apenas cor para comunicar estado. | P1 |
| Pontos de estabelecimentos desapareceram | Não exibir uma legenda para uma camada vazia. A base municipal continua responsável pelos totais por bairro, mas não sustenta pontos precisos. Restaurar pontos somente com uma fonte georreferenciada identificada, cobertura mensurada e distinção visual entre oferta formal agregada e locais observados. | P0 |

O mapa continua sendo uma superfície cartográfica alimentada pelos dados do PontoZero. Trocar o provedor do mapa-base não resolve a ausência de coordenadas empresariais e não altera, por si só, a metodologia analítica.

### P0 — ameaça a credibilidade ou a demonstração

| Problema | Consequência | Resposta |
|---|---|---|
| OpenStreetMap sustenta a oferta comercial | Amostras pequenas e ausência de registros parecem representar o mercado real | Usar empresas ativas do Recife como fonte principal; manter OSM como contexto e complemento |
| Diagnóstico está atrás de quatro abas | O usuário vê dados antes de entender a leitura | Tornar o resumo diagnóstico a entrada dos resultados e colocar detalhes sob demanda |
| Indicadores genéricos não mudam conforme a decisão | O produto parece um agregador de dados | Organizar evidências por demanda, oferta, polos, acesso e confiança, com regras por segmento |
| `401` de sessão aparece no console do fluxo público | Passa sensação de erro logo na entrada | Tratar sessão anônima como estado normal e silencioso |
| Seletor de bairros permanece aberto após a escolha | Encobre a interface e interrompe o fluxo | Fechar após seleção e limpar a busca |
| Texto ainda apresenta OSM como fonte dos estabelecimentos | Contradiz a metodologia revisada | Atualizar interface, README e documentação junto da nova carga |
| Trabalho analítico está sem commit na branch de experiência | Risco de perda e histórico confuso | Isolar o incremento analítico antes de novas alterações |
| Legenda informa pontos que a camada atual não consegue desenhar | O mapa promete uma evidência inexistente | Ocultar a legenda vazia e explicar a granularidade por bairro; reintroduzir pontos apenas com fonte georreferenciada válida |
| Marca acadêmica aparece no produto | Enfraquece a percepção de startup e expõe texto de bastidor | Remover CESAR School e referências a projeto acadêmico da interface pública |

### P1 — reduz qualidade do MVP, mas não deve bloquear o recorte de amanhã

| Problema | Resposta planejada |
|---|---|
| Bairro é uma unidade ampla para localização comercial | Manter como entrada e preparar análise por raio/setor censitário |
| Renda carregada é de 2010 | Incorporar rendimento do responsável pelo domicílio do Censo 2022 |
| Acesso e centralidade aparecem como insuficientes | Integrar polos oficiais de saúde e educação antes de inferir fluxo |
| Mobile empilha controles, mapa e resultados em uma página longa | Criar navegação móvel entre configurar, mapa e resultados |
| Lista de 94 bairros renderiza todos os itens | Virtualizar ou limitar a lista após estabilizar o fluxo principal |
| Bundle principal tem cerca de 869 kB | Separar rotas e carregar mapa/relatório sob demanda |

### P2 — evolução de produto

- página institucional “Sobre o PontoZero”;
- área administrativa completa, mantendo infraestrutura fora da navegação comum;
- áreas de influência por tempo de deslocamento;
- IPTU, fluxo viário e riscos urbanos após validação de uso;
- score composto somente depois de calibrar pesos e sensibilidade;
- pipeline contínuo de atualização das fontes;
- relatórios analíticos completos e cenários com dados do próprio cliente.

## 3. Recorte de entrega para a apresentação final

### Bloco A — proteger a linha de base

1. Criar a branch `HU012/tompson-diagnostico-explicavel` a partir do estado atual.
2. Separar o trabalho já feito em commits de serviço, API, testes e documentação.
3. Registrar build, typecheck, saúde do compose e roteiro manual antes de alterar a base.
4. Não misturar a ingestão empresarial com ajustes visuais no mesmo commit.

**Pronto quando:** o trabalho atual está recuperável e cada mudança seguinte pode ser revertida de forma independente.

### Bloco B — corrigir a evidência principal — concluído em 20/11/2026

**Resultado:** 7.581 CNPJs ativos associados aos bairros em seis recortes de segmento, com catálogo CNAE versionado, deduplicação, relatório de qualidade, snapshot reproduzível e migração que preserva contas e análises existentes. A base municipal não possui coordenadas precisas na edição atual; por isso ela alimenta contagens por bairro, enquanto o OSM não participa dos totais.

1. Baixar e versionar metadados da base oficial de empresas ativas do Recife.
2. Criar configuração declarativa de CNAEs para os 6 segmentos atuais.
3. Deduplicar por CNPJ e categoria; uma empresa com várias atividades não pode inflar a contagem.
4. Validar coordenadas, bairro, situação cadastral e data de abertura.
5. Associar espacialmente quando houver coordenada precisa; caso contrário, usar o bairro cadastral sem fabricar ponto.
6. Manter os registros OSM em camada separada, identificados como complementares.
7. Expor contagens de qualidade: total oficial, coordenadas válidas, registros associados e descartados.

**Pronto quando:** as contagens de oferta exibidas usam a base municipal, possuem cobertura conhecida e podem ser reproduzidas pela equipe.

**Plano de contingência:** se a carga completa não ficar validada, demonstrar apenas um snapshot oficial processado dos segmentos atuais. Não misturar silenciosamente números oficiais e OSM.

### Bloco C — transformar análise em decisão

**Estado em 23/11:** sínteses individual e comparativa implementadas na HU014; testes unitários aprovados e validação integrada pendente do Docker.

1. [x] Fazer “Leitura” abrir como resultado principal.
2. [x] Mostrar, antes das tabelas:
   - leitura curta da região;
   - até 3 sinais observados, sem rotulá-los automaticamente como favoráveis;
   - até 3 pontos de atenção;
   - confiança e cobertura;
   - próximo passo verificável.
3. [x] Colocar evidências, fontes e limitações sob demanda após a síntese.
4. [x] Manter fórmula, fonte e data acessíveis sem repetir longos avisos em todos os cartões.
5. [x] Trocar linguagem genérica por frases que mencionem segmento, região, valor e referência.
6. [x] Não publicar ranking geral nem “melhor bairro”.

**Pronto quando:** alguém consegue explicar a diferença entre dois bairros sem abrir todas as abas nem interpretar sozinho uma tabela.

### Bloco C1 — estabilizar a experiência cartográfica

**Estado em 23/11:** correções de coerência implementadas na HU016; validação visual pelo responsável ainda pendente. A decisão provisória de arquitetura está registrada em [`DECISAO_CARTOGRAFIA.md`](DECISAO_CARTOGRAFIA.md).

1. [x] Remover imediatamente a legenda de estabelecimentos quando não houver pontos georreferenciados.
2. [x] Manter contagem absoluta e taxa por 10 mil moradores nos bairros, com fonte e granularidade explícitas.
3. [x] Criar uma escala cartográfica por indicador, com contraste acessível e menos predominância do azul.
4. [x] Retirar CESAR School e demais textos de bastidor da interface pública.
5. Executar um comparativo curto entre a solução atual e Google Maps, usando o mesmo GeoJSON e o mesmo caso de demonstração.
6. Registrar custo, exigência de chave, franquia, restrições e comportamento sem internet antes de decidir por migração.
7. Prototipar Folium fora do produto somente se ele acelerar a validação de uma análise ou relatório.

**Pronto quando:** mapa, legenda e fonte dizem a mesma coisa; nenhuma camada vazia é anunciada; a identidade visual não prejudica a leitura temática; e a escolha do provedor cartográfico está apoiada em teste, não em aparência isolada.

### Bloco D — hardening e acabamento

**Estado em 23/11:** primeiro pacote implementado na HU015; validação integrada e inspeção visual em 390 px continuam pendentes do ambiente Docker.

1. [x] Corrigir sessão anônima e seletor de bairros.
2. Revisar loading, vazio, erro, sucesso, dados ausentes e números extremos.
3. [x] Garantir foco visível, nomes acessíveis e navegação por teclado no caminho principal.
4. Reduzir animações que atrasam o primeiro contato; manter `prefers-reduced-motion`.
5. [x] Remover cópias com tom genérico, frases redundantes e menções internas como “componentes do 21st.dev” na experiência do usuário.
6. Testar desktop da apresentação e uma largura móvel de 390 px.
7. [x] Eliminar o `401` esperado da sessão anônima e avisos de acessibilidade dos diálogos.

**Pronto quando:** o fluxo principal não apresenta erro visível, sobreposição, controle sem resposta ou texto de bastidor.

### Bloco E — ensaio de entrega

1. Subir o projeto do zero com `docker compose up -d --build`.
2. Confirmar os 3 serviços saudáveis.
3. Criar uma análise com o usuário de demonstração.
4. Salvar e exportar.
5. Executar `docker compose down` e subir novamente.
6. Confirmar persistência da análise e do volume.
7. Preparar um caso guiado com 1 segmento e 2 bairros contrastantes.
8. Levar uma captura/PDF de contingência caso a internet falhe.

**Pronto quando:** outra pessoa consegue seguir o roteiro sem ajuda do desenvolvedor.

## 4. Ordem de execução

```text
A. proteção do trabalho
→ B. base empresarial
→ C1. estabilização cartográfica
→ C. leitura decisória
→ D. hardening
→ E. ensaio completo
```

Se o tempo apertar, reduzir o número de segmentos validados antes de cortar qualidade, rastreabilidade ou estabilidade. Uma vertical consistente convence mais do que seis segmentos com números frágeis.

## 5. Fluxo de trabalho no Git

| Branch | Objetivo | Commits esperados |
|---|---|---|
| `HU012/tompson-diagnostico-explicavel` | preservar o motor analítico já iniciado | `feat(analise)`, `test(analise)`, `docs(metodologia)` |
| `HU013/tompson-base-empresas-recife` | substituir OSM como fonte principal da oferta | `feat(dados)`, `feat(banco)`, `test(dados)`, `docs(fontes)` |
| `HU014/tompson-fluxo-decisao` | reorganizar Explorar e resultados | `feat(explorar)`, `style(explorar)`, `fix(a11y)` |
| `HU015/tompson-hardening-demo` | corrigir bloqueadores e preparar entrega | `fix(auth)`, `fix(filtros)`, `fix(responsividade)`, `docs(demo)` |
| `HU016/tompson-estabilizacao-cartografica` | incorporar o feedback sobre mapa, marca e camadas | `docs(produto)`, `fix(mapa)`, `style(mapa)`, `chore(marca)` |

Cada branch parte de `dev`, recebe build e testes antes do merge e entra em `dev` por incremento completo. `main` recebe apenas a versão ensaiada para a apresentação.

## 6. Fontes seguintes, na ordem de valor

1. **Empresas ativas e inativas do Recife:** oferta, abertura, encerramento e permanência.
2. **IBGE 2022 por setor censitário:** idade, domicílios, composição e rendimento.
3. **CNES e INEP:** polos de saúde e educação, com localização oficial.
4. **CTTU:** fluxo veicular apenas onde houver sensor e cobertura identificada.
5. **IPTU:** características do estoque imobiliário; nunca apresentado como aluguel.
6. **OSM:** contexto urbano e POIs complementares, sempre identificado como colaborativo.

Uma fonte só entra no produto quando tiver licença, referência temporal, granularidade, cobertura, regra de ausência e teste de transformação documentados.

## 7. Critério de aceite do MVP próximo

- [ ] Oferta formal não depende do OSM.
- [ ] Cada número mostra fonte e data.
- [ ] Ausência de registro não aparece como zero confirmado.
- [ ] O diagnóstico é a leitura principal, não a última aba.
- [ ] Pelo menos 2 segmentos têm direcionadores próprios documentados.
- [ ] Pelo menos 2 bairros contrastantes foram verificados manualmente.
- [ ] Conta, salvamento, snapshot e exportação funcionam.
- [ ] Compose sobe do zero e preserva dados após reinício.
- [ ] Fluxo público não produz erro no console.
- [ ] A experiência principal funciona por teclado e em 390 px.
- [ ] Infraestrutura aparece apenas na área administrativa.
- [ ] README, interface e metodologia descrevem as mesmas fontes.

## 8. Itens deliberadamente fora do recorte da apresentação final

- score de oportunidade;
- previsão de sucesso ou recomendação automática;
- tela institucional completa;
- expansão para outros municípios;
- isócronas e roteamento;
- dashboard administrativo completo;
- reforma total da identidade visual;
- integração de todas as fontes listadas.

Esses itens voltam ao backlog depois do feedback do professor. O próximo ciclo deve usar esse feedback para escolher os 2 segmentos prioritários e a primeira regra de área de influência.
