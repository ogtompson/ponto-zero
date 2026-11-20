# Estudo de viabilidade — vertical de farmácias

## Decisão

A vertical é viável para um primeiro diagnóstico territorial, mas ainda não para recomendar automaticamente a abertura de uma unidade. O MVP pode comparar demanda residente e oferta formal por dimensão, com evidências e confiança explícitas. Não deve produzir um score único nesta etapa.

## Recorte e fontes

- Recife, 94 bairros e 2.835 setores censitários.
- Censo 2022/IBGE: população, domicílios, área, população com 60 anos ou mais e rendimento nominal médio mensal das pessoas responsáveis com rendimento.
- Receita Federal, acessada provisoriamente pelo índice aberto Minha Receita: estabelecimentos ativos com CNAE principal 4771-7/01, 4771-7/02 ou 4771-7/03.
- OpenStreetMap: camada complementar para pontos no mapa, nomes e conferência visual.
- Data da consulta empresarial: novembro de 2026. Extração OSM existente no projeto: 17 de novembro de 2026.

Os arquivos brutos não são versionados. O recorte é reproduzido por `python tools/estudo_vertical_farmacias.py tudo`, após baixar os insumos indicados no próprio estudo.

Referências de origem: [Agregados por setores do Censo 2022](https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html?edicao=41852&t=downloads), [cadastros da Receita Federal](https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/cadastros), [classificação CNAE/CONCLA](https://concla.ibge.gov.br/images/concla/documentacao/ResConcla1-2006.pdf) e [documentação da API Minha Receita](https://docs.minhareceita.org/como-usar/).

## Inventário e qualidade

### Demanda

| Campo | Cobertura | Uso permitido |
|---|---:|---|
| População e domicílios | 2.835 setores | Dimensionar demanda residente |
| Renda e demografia | 2.814 setores (99,3%) | Comparar poder de compra e presença relativa de pessoas 60+ |
| Área territorial | 2.835 setores | Calcular densidade |

A população somada é 1.488.920. A diferença de 21 setores sem renda/demografia deve aparecer como confiança da dimensão, e não ser preenchida silenciosamente.

A renda usada é a média nominal da pessoa responsável com rendimento, ponderada pelo número de responsáveis do setor. Ela não equivale a renda domiciliar, renda disponível ou consumo farmacêutico.

### Oferta

Foram encontrados 5.137 registros em que os CNAEs aparecem como atividade principal ou secundária. Destes:

- 1.045 estão ativos;
- 917 estão ativos e têm farmácia como atividade principal;
- 758 dos 917 (82,7%) têm logradouro, número, CEP e bairro;
- todos os 917 têm CEP e bairro, mas a fonte não fornece coordenadas.

O geocoding é tecnicamente possível para a maioria, com qualidade registrável por endereço exato, CEP ou centroide do bairro. Os 17,3% sem logradouro/número não devem receber precisão de ponto.

O OSM contém 146 farmácias, 129 com nome, 55 com bairro e 51 com rua e número. Portanto, cobre somente 15,9% do volume da oferta formal principal e não pode sustentar sozinho densidade ou saturação. Seu papel correto é visualização e validação complementar.

## Perguntas que o MVP consegue responder

1. Como população, presença de pessoas 60+, renda e oferta formal se posicionam em relação aos demais bairros?
2. A oferta cadastrada por 10 mil residentes está relativamente alta ou baixa?
3. A leitura muda quando se observa concentração espacial por km²?
4. Quais evidências favorecem e quais contrariam uma hipótese de oportunidade?
5. Qual é a cobertura e a confiança de cada evidência?

Ainda não é possível responder com rigor: “onde abrir”, faturamento provável, demanda flutuante, capacidade dos concorrentes, aluguel, acessibilidade por tempo ou chance de sucesso.

## Indicadores justificáveis

As dimensões permanecem separadas:

- **escala residente:** população e domicílios;
- **perfil de demanda:** percentual de moradores com 60 anos ou mais;
- **poder de compra (proxy):** renda média ponderada da pessoa responsável;
- **pressão competitiva residente:** farmácias ativas de CNAE principal por 10 mil habitantes;
- **concentração física:** farmácias ativas por km²;
- **qualidade:** cobertura setorial e qualidade do endereço/geocoding.

“Farmácias por 10 mil habitantes” não mede capacidade, qualidade, fluxo de clientes nem vendas. “Farmácias por km²” é sensível ao tamanho e ao desenho do bairro. Os dois devem ser exibidos juntos.

## Metodologia de comparação

1. Agregar os setores censitários no bairro oficial.
2. Somar população, domicílios, população 60+ e área.
3. Ponderar a renda média pelo número de responsáveis com rendimento.
4. Contar somente estabelecimentos ativos cujo CNAE principal pertence à vertical.
5. Converter cada indicador em posição percentílica entre os 94 bairros.
6. Exibir valores absolutos, percentis, fonte, data e cobertura.
7. Produzir uma leitura por dimensão: evidência favorável, desfavorável ou inconclusiva.

Não há soma de percentis nem pesos ocultos. O usuário recebe um diagnóstico comparativo e as ressalvas necessárias para investigar o ponto.

## Três diagnósticos manuais

### Boa Viagem — demanda alta e oferta também alta

- 125.805 moradores; 29.987 com 60+ (23,84%).
- Renda proxy: R$ 9.664; percentil 88.
- 101 farmácias ativas; 8,03 por 10 mil habitantes (percentil 68) e 13,01/km² (percentil 82).

Leitura: a escala, o envelhecimento relativo e a renda sustentam demanda potencial, mas a oferta formal e sua concentração já são altas. O dado não justifica “oportunidade” sem analisar microárea, fluxo, posicionamento e concorrentes próximos.

### Campo Grande — demanda relevante e baixa oferta relativa

- 31.783 moradores; 5.551 com 60+ (17,47%).
- Renda proxy: R$ 2.678; percentil 53.
- 8 farmácias ativas; 2,52 por 10 mil (percentil 16) e 3,56/km² (percentil 24).

Leitura: população alta (percentil 90) combinada a baixa oferta relativa cria uma hipótese de espaço não atendido. A renda mediana e a ausência de dados sobre fluxo/capacidade impedem tratar a hipótese como recomendação.

### Rosarinho — renda alta, bairro pequeno e efeito de fronteira

- 7.271 moradores; 1.228 com 60+ (16,89%).
- Renda proxy: R$ 10.289; percentil 92.
- 2 farmácias ativas; 2,75 por 10 mil (percentil 18), mas 7,84/km² (percentil 61).

Leitura: renda alta e baixa oferta por residente parecem favoráveis, enquanto a densidade física é intermediária. A divergência mostra por que bairro não basta: concorrentes logo após a fronteira e a pequena área podem alterar completamente a leitura. Este caso é prioritário para testar raio ou isócrona.

## Conclusão e próximo incremento

O estudo valida um MVP honesto de diagnóstico por dimensões. O próximo incremento deve geocodificar a oferta com nível de confiança, aplicar áreas de influência e levar esses indicadores ao backend. Antes de qualquer score, os três casos precisam ser conferidos em microárea e comparados com observações reais de operação ou fechamento.
