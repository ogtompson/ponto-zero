-- =====================================================================
-- PontoZero | 03 - Views e função de análise
--
-- As views deixam as consultas da aplicação curtas e legíveis, e a regra
-- de "possível lacuna" (HU-009) fica escrita em SQL, num só lugar, onde
-- qualquer pessoa da equipe consegue ler e conferir.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Catálogo dos tipos de indicador: rótulo, unidade e ordem de exibição
-- (HU-005 RN02: todo indicador mostra nome, valor e unidade)
-- ---------------------------------------------------------------------
CREATE VIEW vw_catalogo_indicador AS
SELECT *
FROM (VALUES
    ('populacao',               'População residente',     'habitantes', 1),
    ('domicilios',              'Domicílios ocupados',     'domicílios', 2),
    ('moradores_por_domicilio', 'Moradores por domicílio', 'pessoas',    3),
    ('renda_media_domiciliar',  'Renda média domiciliar',  'R$ por mês', 4),
    ('area_km2',                'Área',                    'km²',        5),
    ('densidade',               'Densidade demográfica',   'hab/km²',    6)
) AS c (tipo, rotulo, unidade, ordem);

-- ---------------------------------------------------------------------
-- Valor mais recente de cada indicador por região
-- ---------------------------------------------------------------------
CREATE VIEW vw_indicador_atual AS
SELECT DISTINCT ON (i.id_regiao, i.tipo)
       i.id_regiao, i.tipo, i.valor, i.data_referencia, i.fonte
FROM indicador i
ORDER BY i.id_regiao, i.tipo, i.data_referencia DESC NULLS LAST;

-- ---------------------------------------------------------------------
-- Indicadores guardados + densidade calculada (população ÷ área).
-- A densidade não é armazenada: é derivada, então sempre bate com a base.
-- ---------------------------------------------------------------------
CREATE VIEW vw_indicador_completo AS
WITH base AS (
    SELECT id_regiao, tipo, valor, data_referencia, fonte, false AS derivado
    FROM vw_indicador_atual
    UNION ALL
    SELECT p.id_regiao,
           'densidade',
           round(p.valor / NULLIF(a.valor, 0), 2),
           p.data_referencia,
           'Cálculo PontoZero: população (IBGE) ÷ área (Prefeitura)',
           true
    FROM vw_indicador_atual p
    JOIN vw_indicador_atual a ON a.id_regiao = p.id_regiao AND a.tipo = 'area_km2'
    WHERE p.tipo = 'populacao' AND a.valor > 0
)
SELECT b.id_regiao, b.tipo, c.rotulo, c.unidade, c.ordem,
       b.valor, b.data_referencia, b.fonte, b.derivado
FROM base b
JOIN vw_catalogo_indicador c ON c.tipo = b.tipo;

-- ---------------------------------------------------------------------
-- Oferta por região e segmento, inclusive quando a contagem é zero
-- ---------------------------------------------------------------------
CREATE VIEW vw_oferta_regiao AS
SELECT r.id_regiao,
       c.id_categoria,
       count(e.id_estabelecimento)::int AS quantidade,
       p.valor AS populacao,
       CASE WHEN p.valor > 0
            THEN round(count(e.id_estabelecimento) * 10000.0 / p.valor, 2)
       END AS por_10k_hab
FROM regiao r
CROSS JOIN categoria c
LEFT JOIN estabelecimento e
       ON e.id_regiao = r.id_regiao AND e.id_categoria = c.id_categoria
LEFT JOIN vw_indicador_atual p
       ON p.id_regiao = r.id_regiao AND p.tipo = 'populacao'
GROUP BY r.id_regiao, c.id_categoria, p.valor;

-- ---------------------------------------------------------------------
-- Referência da cidade: estabelecimentos do segmento por 10 mil habitantes
-- ---------------------------------------------------------------------
CREATE VIEW vw_referencia_categoria AS
SELECT c.id_categoria,
       c.nome,
       (SELECT count(*) FROM estabelecimento e WHERE e.id_categoria = c.id_categoria)::int AS total_estabelecimentos,
       (SELECT sum(valor) FROM vw_indicador_atual WHERE tipo = 'populacao') AS populacao_total,
       round(
           (SELECT count(*) FROM estabelecimento e WHERE e.id_categoria = c.id_categoria) * 10000.0
           / NULLIF((SELECT sum(valor) FROM vw_indicador_atual WHERE tipo = 'populacao'), 0),
           3
       ) AS por_10k_hab
FROM categoria c;

-- ---------------------------------------------------------------------
-- Resumo das análises salvas (tela "Minhas análises")
-- ---------------------------------------------------------------------
CREATE VIEW vw_resumo_analise AS
SELECT a.id_analise,
       a.nome,
       a.data_criacao,
       a.objetivo,
       a.id_empresa,
       e.nome     AS empresa,
       COALESCE(c.nome, e.segmento) AS segmento,
       (SELECT count(*) FROM regiao_analise ra WHERE ra.id_analise = a.id_analise)::int AS qtd_regioes,
       (SELECT count(*) FROM relatorio rl WHERE rl.id_analise = a.id_analise)::int     AS qtd_relatorios,
       (SELECT max(rl.data_geracao) FROM relatorio rl WHERE rl.id_analise = a.id_analise) AS ultimo_relatorio,
       a.id_categoria,
       a.versao_metodologia,
       a.capturado_em,
       (a.snapshot IS NOT NULL) AS snapshot_disponivel
FROM analise a
JOIN empresa e ON e.id_empresa = a.id_empresa
LEFT JOIN categoria c ON c.id_categoria = a.id_categoria;

-- ---------------------------------------------------------------------
-- HU-009: comparação da oferta observada com a referência municipal
--
-- Regra (simples e transparente, exibida na tela):
--   referência  = estabelecimentos do segmento por 10 mil hab. no Recife
--   esperado    = referência × população da região ÷ 10 mil
--   cobertura   = encontrados ÷ esperado
--   "oferta observada baixa" quando esperado ≥ p_min_esperado
--                              e cobertura ≤ p_cobertura_max
--   "não classificada" quando falta dado necessário (motivo informado)
-- Nada aqui é ranking nem recomendação de investimento (RN07).
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_analise_demanda_oferta(
    p_id_categoria  INT,
    p_regioes       INT[],
    p_min_esperado  NUMERIC DEFAULT 2,
    p_cobertura_max NUMERIC DEFAULT 0.5
)
RETURNS TABLE (
    id_regiao      INT,
    regiao         VARCHAR,
    populacao      NUMERIC,
    encontrados    INT,
    referencia_10k NUMERIC,
    esperado       NUMERIC,
    cobertura      NUMERIC,
    classificacao  TEXT,
    motivo         TEXT
)
LANGUAGE sql STABLE AS $$
    WITH ref AS (
        SELECT por_10k_hab FROM vw_referencia_categoria WHERE id_categoria = p_id_categoria
    ),
    base AS (
        SELECT r.id_regiao,
               r.nome,
               p.valor AS populacao,
               o.quantidade AS encontrados,
               ref.por_10k_hab AS referencia_10k,
               CASE WHEN p.valor IS NOT NULL AND ref.por_10k_hab IS NOT NULL
                    THEN ref.por_10k_hab * p.valor / 10000 END AS esperado
        FROM regiao r
        CROSS JOIN ref
        LEFT JOIN vw_indicador_atual p ON p.id_regiao = r.id_regiao AND p.tipo = 'populacao'
        LEFT JOIN vw_oferta_regiao o   ON o.id_regiao = r.id_regiao AND o.id_categoria = p_id_categoria
        WHERE r.id_regiao = ANY (p_regioes)
    )
    SELECT b.id_regiao,
           b.nome,
           b.populacao,
           b.encontrados,
           b.referencia_10k,
           round(b.esperado, 1),
           CASE WHEN b.esperado > 0 THEN round(b.encontrados / b.esperado, 2) END,
           CASE
               WHEN b.populacao IS NULL                     THEN 'nao_classificada'
               WHEN b.referencia_10k IS NULL
                 OR b.referencia_10k = 0                    THEN 'nao_classificada'
               WHEN b.esperado < p_min_esperado              THEN 'oferta_observada_compativel'
               WHEN b.encontrados <= p_cobertura_max * b.esperado THEN 'oferta_observada_baixa'
               ELSE 'oferta_observada_compativel'
           END,
           CASE
               WHEN b.populacao IS NULL
                   THEN 'População indisponível para esta região'
               WHEN b.referencia_10k IS NULL OR b.referencia_10k = 0
                   THEN 'Segmento sem estabelecimentos na base de referência'
               WHEN b.esperado < p_min_esperado
                   THEN format('Demanda esperada baixa: %s estabelecimento(s) esperado(s)',
                               to_char(b.esperado, 'FM990D0'))
               WHEN b.encontrados <= p_cobertura_max * b.esperado
                   THEN format('%s encontrado(s) para %s esperado(s)',
                               b.encontrados, to_char(b.esperado, 'FM990D0'))
               ELSE format('%s encontrado(s) para %s esperado(s)',
                           b.encontrados, to_char(b.esperado, 'FM990D0'))
           END
    FROM base b;
$$;

COMMENT ON FUNCTION fn_analise_demanda_oferta(INT, INT[], NUMERIC, NUMERIC)
    IS 'HU-009: compara oferta observada e referência municipal; não mede demanda nem confirma ausência de oferta';
