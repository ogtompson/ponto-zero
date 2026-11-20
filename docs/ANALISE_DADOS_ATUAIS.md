# Análise dos dados atuais e metodologia de comparação

Este documento responde, com base no banco atual do PontoZero, a quatro questões:

1. quais dados estão realmente disponíveis e qual é sua qualidade;
2. quais perguntas de negócio eles conseguem responder;
3. quais indicadores e cruzamentos são justificáveis;
4. como comparar bairros de maneira explicável.

Os números foram apurados diretamente no PostgreSQL da aplicação em 19/11/2026.

## 1. Inventário e qualidade

### 1.1 Base territorial

O banco possui 94 bairros e cinco indicadores brutos por bairro, totalizando 470 registros. Não há valores ausentes.

| Indicador | Bairros | Referência | Mínimo | Mediana | Máximo | Avaliação |
|---|---:|---|---:|---:|---:|---|
| População residente | 94 | Censo 2022 | 89 | 9.842 | 125.805 | adequado para porte residencial e normalização |
| Domicílios ocupados | 94 | Censo 2022 | 27 | 3.468,5 | 50.663 | adequado para estimar base de lares |
| Moradores por domicílio | 94 | Censo 2022 | 1,89 | 2,74 | 3,30 | adequado, mas pouco discriminante isoladamente |
| Renda média domiciliar | 94 | Censo 2010 | R$ 567,34 | R$ 1.957,55 | R$ 11.339,79 | completo, porém defasado; apenas contexto histórico |
| Área | 94 | data não informada | 0,14 km² | 0,86 km² | 46,06 km² | utilizável com ressalva sobre data e heterogeneidade territorial |

#### Achados de qualidade

- População e domicílios têm correlação de **0,997**. Exibi-los como duas evidências independentes daria peso duplicado ao porte residencial.
- População total e densidade têm correlação de apenas **0,101**. São dimensões diferentes e ambas são úteis.
- A renda de 2010 não deve ser apresentada como poder de compra atual nem combinada diretamente com valores monetários atuais.
- Bairros muito pequenos, muito extensos ou com uso predominantemente não residencial geram extremos legítimos, mas exigem contexto. A densidade varia de 148 a 27.965 habitantes/km².
- Limites administrativos não representam necessariamente áreas reais de influência comercial.

Exemplos de extremos de densidade:

| Bairro | População | Área | Habitantes/km² |
|---|---:|---:|---:|
| Rosarinho | 7.271 | 0,26 | 27.965 |
| Alto José do Pinho | 11.313 | 0,42 | 26.936 |
| Guabiraba | 11.095 | 46,06 | 241 |
| Recife | 541 | 3,14 | 172 |
| Pau Ferro | 89 | 0,60 | 148 |

### 1.2 Oferta observada

Há 532 registros do OpenStreetMap, extraídos em 17/11/2026. A fonte é colaborativa e não assegura cobertura uniforme.

| Segmento | Registros | Bairros com registro | Cobertura espacial observada |
|---|---:|---:|---:|
| Supermercado | 146 | 48 de 94 | 51,1% |
| Farmácia | 146 | 36 de 94 | 38,3% |
| Padaria | 96 | 37 de 94 | 39,4% |
| Academia | 52 | 22 de 94 | 23,4% |
| Cafeteria | 65 | 21 de 94 | 22,3% |
| Pet shop | 27 | 17 de 94 | 18,1% |

Outros achados:

- 265 dos 532 registros, **49,8%**, não possuem endereço preenchido.
- Não foram encontrados pares repetidos de coordenada arredondada a cinco casas e categoria.
- Os cinco bairros com mais registros concentram entre **32,9% e 60,0%** de toda a oferta de cada segmento.
- Boa Viagem aparece em primeiro lugar nos seis segmentos, concentrando de 6 pet shops a 25 farmácias. Isso pode refletir atividade real, maior mapeamento ou ambos.
- Entre 24,4% e 70,0% da população do Recife vive em bairros sem qualquer registro na base, dependendo do segmento.

O caso de farmácias é ilustrativo: Água Fria, Dois Unidos, Torrões, Barro e Jardim São Paulo estão entre bairros populosos sem registro observado. Portanto, zero no banco não pode ser interpretado como zero concorrentes.

### 1.3 Classificação de qualidade por fonte

| Conjunto | Completude | Atualidade | Cobertura | Granularidade | Condição de uso |
|---|---|---|---|---|---|
| População e domicílios | alta | adequada | alta | bairro | adequada |
| Moradores por domicílio | alta | adequada | alta | bairro | adequada, complementar |
| Área | alta | não informada | alta | bairro | aproximada |
| Renda | alta | defasada | alta | bairro | histórica; fora de sínteses atuais |
| Oferta OSM | variável | recente | desconhecida e desigual | ponto | exploratória; nunca ausência confirmada |

## 2. Perguntas de negócio respondíveis

### 2.1 Podemos responder com segurança

| Pergunta | Resposta possível |
|---|---|
| Qual bairro possui maior base residencial? | população e domicílios, em valor e percentil municipal |
| Onde a população está mais concentrada espacialmente? | densidade populacional |
| Onde há maior concentração de lares? | densidade domiciliar |
| Como bairros candidatos diferem em porte, densidade e estrutura domiciliar? | comparação padronizada dos indicadores territoriais |
| Onde a base possui mais registros de um segmento? | quantidade e densidade da **oferta observada** |
| A oferta observada está concentrada ou dispersa? | registros por km², por 10 mil moradores e participação municipal observada |

### 2.2 Podemos responder apenas como hipótese

| Pergunta | Resposta responsável |
|---|---|
| Há pouca concorrência? | a base possui baixa oferta observada; concorrência real precisa ser validada |
| Há espaço para mais uma unidade? | há combinação de base residencial e pressão observada que merece investigação |
| O público tem renda compatível? | a renda histórica sugere um perfil relativo; é necessário dado atual |
| O bairro parece residencial ou central? | densidade e relação entre população e oferta sugerem um padrão, sem confirmar fluxo |

### 2.3 Não conseguimos responder hoje

- qual bairro é o melhor para abrir;
- demanda efetiva, consumo ou faturamento potencial;
- quantidade real e porte dos concorrentes;
- população flutuante e fluxo de pedestres ou veículos;
- adequação demográfica específica ao segmento;
- aluguel, imóveis disponíveis, zoneamento e custos;
- distância, tempo de viagem e área de influência;
- probabilidade de sucesso ou retorno do investimento.

## 3. Indicadores e cruzamentos justificáveis

### 3.1 Indicadores territoriais principais

| Indicador | Fórmula | Papel na análise | Confiança |
|---|---|---|---|
| Porte residencial | população | tamanho da base residente | alta |
| Base de lares | domicílios | quantidade de unidades domiciliares | alta, mas redundante com população |
| Densidade residencial | população ÷ área | concentração de moradores | média-alta |
| Densidade domiciliar | domicílios ÷ área | concentração de lares | média-alta |
| Estrutura domiciliar | população ÷ domicílios | tamanho médio domiciliar | alta |
| Renda relativa histórica | percentil da renda de 2010 | contexto socioeconômico histórico | baixa para decisão atual |

População e domicílios devem integrar uma única dimensão chamada **base residencial**, evitando dupla contagem.

### 3.2 Indicadores de oferta observada

| Indicador | Fórmula | Interpretação permitida |
|---|---|---|
| Registros observados | contagem de pontos | presença encontrada na base |
| Registros por 10 mil residentes | registros ÷ população × 10.000 | intensidade observada em relação à base residente |
| Registros por km² | registros ÷ área | concentração espacial observada |
| Moradores por registro | população ÷ registros | pressão residencial aparente; indisponível quando não há registro |
| Relação com referência municipal | taxa local ÷ taxa municipal | distância da média da própria base observada |
| Participação observada | registros do bairro ÷ registros municipais | concentração do inventário no bairro |

Todos devem carregar o termo **observado**. Quando a contagem for zero, taxas derivadas devem aparecer como indisponíveis, e não como concorrência zero.

### 3.3 Cruzamento central do MVP

O cruzamento mais justificável com os dados atuais é **base residencial × intensidade da oferta observada**.

| Base residencial | Oferta observada | Leitura permitida |
|---|---|---|
| alta | alta | mercado observado ativo; investigar saturação, porte e diferenciação |
| alta | baixa | sinal para validar cobertura e possível espaço de mercado |
| baixa | alta | possível centralidade, fluxo externo ou concentração comercial |
| baixa | baixa | pouca evidência; demanda e cobertura precisam ser verificadas |

Esse cruzamento gera uma **hipótese de investigação**, não uma classificação de oportunidade.

### 3.4 Cruzamentos complementares

- **porte × densidade:** diferencia bairros grandes e espalhados de bairros compactos;
- **oferta por morador × oferta por km²:** diferencia pressão sobre residentes de aglomeração comercial;
- **estrutura domiciliar × segmento:** só deve ganhar interpretação específica após validar hipóteses do segmento;
- **renda histórica × demais métricas:** contexto separado, visualmente marcado como 2010 e excluído de qualquer síntese atual.

## 4. Metodologia de comparação explicável

### 4.1 Unidade e referência

- unidade inicial: bairro oficial do Recife;
- referência principal: distribuição dos 94 bairros;
- referência da oferta: somente a base observada do mesmo segmento;
- comparação temporal: proibida enquanto houver apenas uma observação por indicador.

### 4.2 Padronização

Cada métrica deve mostrar:

1. valor bruto e unidade;
2. percentil entre os 94 bairros;
3. faixa descritiva;
4. fonte, data e confiança.

Faixas iniciais, baseadas na distribuição e não em metas arbitrárias:

- percentil 0–24: **menor que a maior parte dos bairros**;
- percentil 25–74: **faixa intermediária do Recife**;
- percentil 75–100: **maior que a maior parte dos bairros**.

O percentil não representa qualidade. Percentil alto de oferta pode significar mercado ativo ou maior pressão competitiva, conforme o contexto.

### 4.3 Dimensões sem nota única

A comparação inicial deve manter três blocos independentes:

1. **Base residencial:** população, domicílios e densidade;
2. **Estrutura territorial:** área e moradores por domicílio;
3. **Oferta observada:** presença, intensidade por moradores e concentração por área.

A renda histórica aparece como contexto separado. Não haverá soma, peso nem ranking geral nesta fase.

### 4.4 Regra de evidência

Cada conclusão deve ser gerada por regras determinísticas e exibir os fatos que a ativaram.

Modelo:

> **Sinal:** base residencial elevada e poucos registros observados.
>
> **Evidências:** população no percentil 94; densidade no percentil 92; nenhum registro de farmácia na base.
>
> **Limite:** a cobertura do OpenStreetMap não é verificada neste bairro.
>
> **Próximo passo:** confirmar concorrentes em campo e em fonte empresarial antes de avaliar a hipótese.

### 4.5 Confiança da conclusão

| Nível | Regra inicial |
|---|---|
| alta | usa somente população, domicílios ou moradores por domicílio de 2022 |
| média | depende de área sem data ou de métrica derivada dela |
| baixa | depende de renda de 2010 ou da completude da oferta OSM |
| insuficiente | exige dado que não existe ou interpreta zero observado como ausência real |

A confiança descreve a evidência, não o bairro.

### 4.6 Exemplo real

| Bairro | População (percentil) | Densidade (percentil) | Renda 2010 (percentil) | Cafeterias observadas | Farmácias observadas |
|---|---:|---:|---:|---:|---:|
| Boa Viagem | 125.805 (100) | 15.085/km² (75) | R$ 7.109 (88) | 12 | 25 |
| Rosarinho | 7.271 (35) | 27.965/km² (100) | R$ 6.548 (86) | 1 | 2 |
| Água Fria | 39.012 (94) | 20.213/km² (92) | R$ 1.190 (27) | 0 | 0 |

Leituras explicáveis:

- Boa Viagem combina o maior porte residencial com forte presença observada; isso indica mercado mapeado, não oportunidade superior.
- Rosarinho tem porte menor e a maior densidade da cidade; população total e concentração precisam permanecer separadas.
- Água Fria combina porte e densidade elevados com ausência de registros nos dois segmentos. Pela baixa cobertura espacial do OSM, isso deve gerar uma tarefa de validação, não um selo de lacuna de mercado.

## 5. Especificação da primeira entrega analítica

A primeira implementação deve produzir, para cada bairro selecionado:

```text
resumo territorial
├── base residencial: valor, percentil e faixa
├── densidade: valor, percentil e faixa
├── estrutura domiciliar: valor e percentil
├── oferta observada: contagem, por 10 mil e por km²
├── cruzamento: sinal + evidências que o sustentam
├── confiança: nível e justificativa
└── próximo passo de validação
```

Critérios de aceite:

- nenhuma ausência de registro é tratada como oferta zero;
- população e domicílios não são pontuados duas vezes;
- renda de 2010 não participa de síntese atual;
- valores brutos permanecem visíveis junto dos percentis;
- toda frase analítica é reproduzível por regra documentada;
- não há ranking geral nem recomendação automática de abertura;
- testes cobrem bairros extremos e o caso de alta população sem oferta observada.

## 6. Lacunas que impedem uma análise de oportunidade

Antes de evoluir de hipótese territorial para oportunidade comercial, são indispensáveis:

1. fonte mais completa de estabelecimentos ativos;
2. perfil demográfico e renda atualizados;
3. fluxo e polos geradores de viagens;
4. áreas de influência por distância ou tempo, não apenas bairro;
5. dados de custo, imóveis e restrições;
6. hipóteses validadas para cada segmento.

Até lá, a proposta honesta e útil do PontoZero é: **priorizar territórios para investigação e explicar por quê**.
