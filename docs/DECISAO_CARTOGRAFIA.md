# Decisão cartográfica do PontoZero

**Data:** 23 de novembro de 2026  
**Estado:** decisão provisória para o MVP

## Decisão

O mapa principal continuará em React-Leaflet no próximo ciclo. Google Maps será avaliado em um experimento isolado quando a equipe disponibilizar uma chave restrita com faturamento e cotas configuradas. Folium permanece como ferramenta auxiliar para exploração de dados e geração de mapas em relatórios, não como componente da aplicação React.

Essa decisão não torna o provedor atual definitivo. Ela evita que uma troca de biblioteca seja confundida com a correção dos dados ou com a evolução da metodologia analítica.

## O que cada alternativa resolve

| Alternativa | Resolve bem | Não resolve sozinha |
|---|---|---|
| React-Leaflet atual | GeoJSON dos bairros, eventos, filtros, seleção sincronizada e funcionamento sem credencial do Google | Coordenadas ausentes dos estabelecimentos e análises territoriais |
| Google Maps JavaScript API | Base cartográfica familiar, estilos do Google e integração com o ecossistema Maps | Não fornece automaticamente a camada empresarial oficial nem transforma dados em diagnóstico |
| Google Places API | Busca de locais conhecidos pelo Google e detalhes de estabelecimentos | Não equivale ao cadastro formal completo, possui custos e regras próprias e não deve ser misturada silenciosamente aos totais oficiais |
| Folium | Prototipação em Python, notebooks, coropléticos e mapas HTML para estudos | Estado interativo do React, fluxo do produto e sincronização direta com os painéis |

## Custo e operação do Google Maps

A Maps JavaScript API exige projeto Google Cloud, chave de API e faturamento habilitado. A tabela global consultada em 23/11/2026 informa franquia mensal de 10 mil carregamentos para o SKU Dynamic Maps; o excedente segue cobrança por uso. Places possui SKUs, eventos faturáveis e limites próprios.

Uma prova de conceito só será considerada válida quando usar:

1. chave separada para desenvolvimento;
2. restrição à Maps JavaScript API e aos domínios autorizados;
3. cota diária compatível com teste;
4. alerta de orçamento;
5. chave fornecida por variável de ambiente e nunca versionada;
6. comparação com o mesmo GeoJSON, indicador e seleção usados no Leaflet.

Referências oficiais:

- [Configuração da Maps JavaScript API](https://developers.google.com/maps/documentation/javascript/get-api-key)
- [Uso e faturamento da Maps JavaScript API](https://developers.google.com/maps/documentation/javascript/usage-and-billing)
- [Tabela global de preços](https://developers.google.com/maps/billing-and-pricing/pricing)

## Pontos de estabelecimentos

Trocar o mapa-base não recupera os pontos. A edição atual da base municipal sustenta contagens formais por bairro, mas não localizações pontuais confiáveis. Por isso:

- os totais oficiais continuam agregados por bairro;
- a interface não anuncia marcadores que não consegue desenhar;
- pontos futuros devem informar fonte, data, cobertura e natureza da observação;
- uma camada de Places ou OpenStreetMap deve aparecer como complementar, sem alterar silenciosamente os totais cadastrais;
- geocodificação de endereços só entra após medir acurácia e revisar resultados ambíguos.

## Critérios para reconsiderar a decisão

Google Maps substitui o provedor atual apenas se o experimento demonstrar ganho material em legibilidade ou tarefa do usuário e se custo, credencial, licença e comportamento de contingência forem aceitáveis. Folium entra no produto somente se houver um caso de relatório ou análise gerada no backend em que um HTML ou mapa estático seja uma saída deliberada.

