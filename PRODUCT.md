# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

O PontoZero atende pessoas que avaliam onde abrir o primeiro negócio e equipes de empresas, franquias ou redes que estudam uma nova unidade. Esses usuários precisam reduzir o trabalho de reunir dados dispersos e entender quais regiões merecem investigação mais profunda.

## Product Purpose

O produto apoia a triagem de localização comercial em Recife. Ele organiza evidências territoriais, compara regiões com critérios consistentes e explica sinais favoráveis, riscos, limitações e próximos passos.

O produto tem sucesso quando o usuário consegue selecionar um segmento e um território, entender por que os locais diferem e sair com uma hipótese clara para validar antes da decisão de investimento.

## Positioning

O PontoZero combina dados territoriais e empresariais em uma leitura espacial explicável. O produto não entrega apenas registros no mapa: transforma fontes públicas em indicadores comparáveis e mostra a qualidade das evidências usadas.

## Operating Context

- O piloto cobre o município do Recife.
- O usuário pode explorar sem conta; a conta serve para salvar análises e preservar snapshots.
- O mapa é a superfície de exploração e apresentação das camadas analíticas, não a fonte principal das conclusões.
- A entrega acadêmica também precisa demonstrar banco de dados, Docker, persistência e rastreabilidade das fontes.
- A apresentação ao professor ocorrerá em 21 de novembro de 2026.

## Capabilities and Constraints

- Aplicação React com API FastAPI e PostgreSQL, distribuída com Docker Compose.
- Seleção de segmento e de bairros, comparação territorial, diagnóstico, salvamento e exportação.
- O produto realiza triagem territorial. Não prevê sucesso, não recomenda investimento e não substitui estudo de viabilidade ou validação em campo.
- O OpenStreetMap deve fornecer contexto cartográfico e dados complementares. A oferta formal deve vir prioritariamente de cadastros oficiais.
- O bairro continuará como entrada de navegação no curto prazo. Áreas de influência e setores censitários são evoluções planejadas.
- Decisão aberta: quais 2 segmentos receberão validação analítica aprofundada primeiro.
- Decisão aberta: qual regra de área de influência será adotada por segmento.

## Brand Commitments

- Nome: PontoZero.
- Identidade existente em marinho e ouro, com tipografia Archivo e marca já fornecida pela equipe.
- Linguagem direta, sóbria e explicável; sem promessas de sucesso comercial.
- A interface deve parecer um produto de inteligência territorial, não um painel genérico nem uma coleção de componentes.

## Evidence on Hand

- População e domicílios do Censo 2022.
- Limites oficiais dos bairros do Recife.
- Renda de 2010 atualmente carregada, a ser substituída pelo rendimento de 2022 disponível por setor censitário.
- 532 pontos do OpenStreetMap, úteis apenas como camada observacional complementar.
- Base oficial de empresas ativas e inativas do Recife, com CNAE, endereço, datas e coordenadas, identificada e ainda não incorporada ao produto.
- Implementação atual de diagnóstico multidimensional sem score composto.
- Não há casos reais validados, depoimentos, taxas de acerto ou resultados de clientes. A interface não deve fabricar essas provas.

## Product Principles

1. Começar pela decisão que o usuário precisa tomar.
2. Explicar cada leitura com fonte, data, cálculo e limitação.
3. Tratar ausência de dado como incerteza, nunca como zero.
4. Priorizar poucas evidências úteis sobre muitas métricas desconectadas.
5. Manter o caminho principal curto: configurar, comparar, entender e validar.

## Accessibility & Inclusion

A experiência deve funcionar por teclado, preservar foco visível, respeitar redução de movimento e manter leitura e controles utilizáveis em telas estreitas. Cores não podem carregar significado sozinhas.
