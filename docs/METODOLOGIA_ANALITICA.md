# Metodologia analítica do PontoZero

> Documento de planejamento. Define o que o produto deve responder, o que os dados atuais sustentam e quais condições precisam ser cumpridas antes de publicar novos indicadores.

O diagnóstico quantitativo, as perguntas respondíveis, os cruzamentos e a metodologia inicial de comparação estão detalhados em [`ANALISE_DADOS_ATUAIS.md`](ANALISE_DADOS_ATUAIS.md). A validação prática da primeira vertical está em [`ESTUDO_VERTICAL_FARMACIAS.md`](ESTUDO_VERTICAL_FARMACIAS.md).

## 1. Tese do produto

O PontoZero não deve apenas reunir dados territoriais. Seu núcleo é transformar dados dispersos em uma leitura comercial simples, rastreável e útil para decidir onde aprofundar uma investigação.

O fluxo analítico pretendido é:

```text
dados brutos → métricas comparáveis → evidências → diagnóstico explicado → próximos passos
```

O produto realiza **triagem territorial**. Ele pode identificar sinais favoráveis, riscos e lacunas de informação, mas não prevê sucesso nem substitui viabilidade financeira, pesquisa de campo ou conhecimento operacional do segmento.

## 2. Perguntas que a análise deve responder

Para cada segmento e região, o produto deve ajudar o usuário a entender:

1. **Demanda potencial:** há uma base residencial compatível com o negócio?
2. **Adequação do público:** o perfil local se aproxima do público esperado pelo segmento?
3. **Pressão da oferta:** há muita ou pouca oferta formal ativa no recorte CNAE em relação ao território?
4. **Acesso e centralidade:** clientes e operação conseguem chegar à região?
5. **Viabilidade territorial:** custos, restrições e características urbanas tornam a hipótese plausível?
6. **Confiança da leitura:** os dados são recentes, completos e adequados para essa conclusão?
7. **Próximo passo:** o que deve ser validado antes de avançar?

Nem todas essas perguntas são respondidas pelos dados atuais. A interface deve distinguir claramente **evidência disponível**, **proxy** e **informação ainda ausente**.

## 3. Inventário dos dados atuais

| Dado | Cobertura | Referência | Uso analítico seguro | Limitação principal |
|---|---:|---|---|---|
| População residente | 94 bairros | Censo 2022 | porte residencial, densidade e normalização | não mede população flutuante |
| Domicílios ocupados | 94 bairros | Censo 2022 | base potencial de lares e densidade domiciliar | não descreve composição ou consumo |
| Moradores por domicílio | 94 bairros | Censo 2022 | característica domiciliar complementar | pouco discriminante isoladamente |
| Renda média domiciliar | 94 bairros | Censo 2010 | somente contexto histórico e proxy sinalizado | defasada e inadequada para valores monetários atuais |
| Área | 94 bairros | Prefeitura do Recife, sem data informada | densidades por km² | bairros não representam áreas comerciais homogêneas |
| Empresas formais ativas | 7.581 registros associados, 6 segmentos | Prefeitura do Recife, atualização de 03/11/2026 | contagem e concentração cadastral por bairro | não inclui informalidade; CNAE de cafeteria é aproximado; coordenadas da edição atual são imprecisas |
| Limites geográficos | 94 bairros | Prefeitura do Recife | seleção e agregação territorial | efeito de borda e granularidade ampla |

| Segmento | CNPJs associados ao bairro |
|---|---:|
| Farmácia | 1.040 |
| Supermercado | 334 |
| Padaria | 1.296 |
| Cafeteria e similares | 3.458 |
| Academia | 792 |
| Pet shop | 661 |

Essas quantidades descrevem o universo cadastral municipal dentro dos CNAEs escolhidos, não todo o mercado real. Três farmácias, doze registros do perímetro de cafeteria, dois de academia, um supermercado e nove padarias ficaram sem associação de bairro. O OpenStreetMap não participa dessas contagens.

### Diagnóstico do estado atual

O sistema calcula concentração de empresas formais por 10 mil habitantes e compara cada bairro com uma referência municipal proporcional do mesmo segmento. Isso é útil como triagem, mas ainda não mede demanda, porte, capacidade, fluxo, custo, acessibilidade ou viabilidade.

## 4. O que já pode ser calculado com responsabilidade

### 4.1 Métricas territoriais derivadas

| Métrica | Cálculo | Leitura permitida |
|---|---|---|
| Densidade populacional | população ÷ área | concentração residencial |
| Densidade domiciliar | domicílios ÷ área | concentração de lares |
| Oferta por 10 mil moradores | empresas formais do recorte ÷ população × 10.000 | intensidade cadastral normalizada por residentes |
| Oferta por km² | empresas formais do recorte ÷ área | concentração cadastral no bairro |
| Moradores por estabelecimento | população ÷ estabelecimentos | pressão populacional aparente; indisponível quando não há registro confiável |
| Relação com a referência municipal | oferta local por 10 mil ÷ oferta municipal por 10 mil | distância relativa da média observada da cidade |
| Massa de renda histórica | domicílios × renda média de 2010 | proxy histórico, nunca poder de compra atual |

As métricas devem apresentar unidade, fonte, data, fórmula, cobertura e motivo quando indisponíveis.

### 4.2 Comparação relativa

Valores absolutos devem ser acompanhados de posição relativa entre os 94 bairros, preferencialmente por percentis. Percentis facilitam a leitura e reduzem a influência de escalas diferentes, mas **não transformam uma variável em oportunidade**.

Exemplo de linguagem correta:

> A densidade residencial está entre as 20% maiores do Recife. A oferta formal do recorte por morador está abaixo da mediana municipal; negócios informais, porte e capacidade ainda precisam ser validados.

Exemplo proibido:

> Este é o melhor bairro para abrir uma padaria.

## 5. Estrutura do futuro motor analítico

Cada análise será organizada em dimensões independentes. Uma dimensão só recebe leitura quando os dados mínimos estiverem disponíveis.

| Dimensão | Evidências desejadas | Situação atual |
|---|---|---|
| Potencial de mercado | população, domicílios, perfil etário, renda atual, consumo e fluxo | parcial |
| Adequação ao segmento | perfil do público e direcionadores específicos do segmento | ausente |
| Pressão competitiva | negócios ativos, categoria, porte, proximidade e concentração | parcial e observacional |
| Acesso e centralidade | transporte, vias, caminhabilidade, tempo de deslocamento e polos geradores | ausente |
| Viabilidade territorial | aluguel, imóveis disponíveis, zoneamento e restrições | ausente |
| Confiança dos dados | atualidade, cobertura, granularidade e consistência | parcialmente implementada |

### 5.1 Saída esperada

Em vez de uma nota opaca, a primeira versão madura deve entregar:

- resumo do território em linguagem direta;
- evidências favoráveis;
- pontos de atenção;
- dados ausentes ou frágeis;
- comparação com referências coerentes;
- perguntas e validações recomendadas;
- memória de cálculo e fontes.

Uma pontuação composta só poderá ser adotada após definição e validação dos pesos por segmento. Mesmo nesse caso, dimensões e explicações continuam visíveis.

## 6. Especificidade por segmento

Os mesmos dados não têm o mesmo significado para todos os negócios. O motor precisa de um perfil analítico por segmento contendo:

- público e ocasião de consumo esperados;
- variáveis relevantes e direção esperada de cada relação;
- raio de influência adequado;
- pesos ou regras, quando houver justificativa;
- alertas e dados indispensáveis;
- perguntas de validação em campo.

Exemplos de hipóteses a validar, e não regras prontas:

- farmácias podem depender de população residente, perfil etário, serviços de saúde e concorrência próxima;
- cafeterias podem depender mais de fluxo diurno, polos de trabalho/estudo e centralidade do que de população residente;
- supermercados podem exigir leitura de domicílios, renda, concorrência por porte, acesso viário e área de influência;
- academias podem depender de perfil etário, renda, densidade, mobilidade e concorrência em raio próximo.

A equipe deve aprovar cada perfil antes de transformá-lo em cálculo de produção.

## 7. Qualidade e confiança

Toda evidência deve receber uma condição de uso:

- **adequada:** fonte, data, cobertura e granularidade sustentam a leitura;
- **aproximada:** dado útil como proxy, com ressalva explícita;
- **insuficiente:** não deve participar de síntese ou classificação.

A confiança da análise deve considerar, no mínimo:

1. cobertura territorial;
2. atualidade;
3. compatibilidade entre datas;
4. granularidade;
5. completude;
6. adequação ao segmento.

Baixa confiança não é uma nota ruim para o bairro; é uma limitação da evidência.

## 8. Dados prioritários a investigar

### Prioridade 1 — sustentar demanda e adequação

- renda e distribuição de renda mais recentes em granularidade compatível;
- faixas etárias e composição domiciliar;
- negócios ativos por atividade econômica, com data e situação cadastral;
- classificação mais precisa de estabelecimentos e deduplicação da oferta atual.

### Prioridade 2 — explicar movimento e acesso

- polos geradores de fluxo: trabalho, educação, saúde, comércio e lazer;
- transporte público, malha viária e tempos de deslocamento;
- população flutuante ou proxies de fluxo;
- análise por raio e áreas de influência, não apenas por limite de bairro.

### Prioridade 3 — aproximar viabilidade

- preço e disponibilidade de imóveis comerciais;
- zoneamento e restrições urbanísticas;
- custos operacionais territorializados;
- dados próprios fornecidos por redes, quando disponíveis.

Cada nova fonte deve passar por avaliação de licença, atualização, cobertura, granularidade, custo e possibilidade de reprodução acadêmica.

## 9. Fases de entrega

### Fase A — fundação analítica com os dados atuais

1. criar catálogo formal de métricas e fórmulas;
2. calcular densidade domiciliar, oferta por km², moradores por registro e percentis;
3. criar diagnóstico textual determinístico e explicável;
4. expor qualidade e limitações junto de cada evidência;
5. substituir a navegação por abas isoladas por uma leitura orientada a perguntas.

**Resultado:** o produto interpreta melhor o que já possui, sem prometer mais do que os dados permitem.

### Fase B — perfis analíticos dos segmentos

1. escolher dois segmentos prioritários;
2. documentar seus direcionadores de localização;
3. validar regras com referências e entrevistas;
4. implementar indicadores específicos e áreas de influência;
5. comparar resultados com casos conhecidos.

**Resultado:** análises diferentes para negócios diferentes.

### Fase C — ampliação da base

1. incorporar dados demográficos e empresariais atualizados;
2. adicionar acesso, centralidade e polos geradores;
3. avaliar custos e imóveis;
4. versionar dados e metodologia.

**Resultado:** leitura multidimensional com maior poder de orientação.

### Fase D — síntese decisória

1. testar pesos e sensibilidade;
2. criar cenários conforme objetivo do usuário;
3. apresentar fatores que mais influenciaram cada resultado;
4. gerar plano de validação e relatório completo.

**Resultado:** priorização explicável, nunca uma recomendação automática de investimento.

## 10. Critérios para publicar um indicador

Um indicador só entra no produto quando:

- responde a uma pergunta de decisão definida;
- possui fórmula e unidade documentadas;
- tem fonte, data e cobertura conhecidas;
- trata valores ausentes sem convertê-los em zero;
- é comparável entre as regiões apresentadas;
- tem interpretação e limitações explícitas;
- possui teste de cálculo e caso de referência;
- não duplica outro indicador sem benefício claro.

## 11. Decisões que a equipe precisa tomar

1. Quais dois segmentos serão aprofundados primeiro?
2. A unidade principal continuará sendo bairro ou o produto migrará para raios/áreas de influência?
3. O MVP deve priorizar descoberta de regiões ou comparação de candidatas já escolhidas?
4. A equipe aceita ranking explicável ou prefere trabalhar inicialmente com faixas e evidências?
5. Quais fontes externas são viáveis dentro do prazo, da licença e da capacidade de atualização?
6. Quem valida as hipóteses de cada segmento: empreendedores, especialistas, professores ou literatura?

## 12. Próximo recorte de implementação

Antes de alterar a interface, o próximo trabalho técnico deve produzir:

1. um dicionário versionado das métricas da Fase A;
2. consultas reproduzíveis para os indicadores derivados;
3. uma resposta de API com evidências, qualidade e memória de cálculo;
4. testes com bairros de perfis contrastantes;
5. um protótipo de diagnóstico textual para avaliação da equipe.

Esse recorte permite provar o valor analítico antes de investir em pontuação composta ou em novas telas.

## 13. Contrato implementado

A primeira versão do diagnóstico multidimensional está disponível em:

```http
GET /api/diagnostico?segmento={id}&regioes={id1,id2}
```

A resposta usa a metodologia `2026.11.2` e mantém cinco dimensões independentes:

1. demanda residente;
2. adequação do público;
3. pressão da oferta;
4. acesso e centralidade;
5. confiança dos dados.

Cada evidência inclui valor, unidade, percentil entre os bairros, faixa relativa, fonte, data, qualidade, interpretação e limitações. Dimensões sem dados aparecem como insuficientes. A resposta declara `sem_score: true`, portanto não soma percentis nem produz recomendação automática.
