-- =====================================================================
-- PontoZero | testes_integridade.sql - Prova que as restrições funcionam
--
-- Roda depois do ddl.sql e do seed_dml.sql. Tenta gravar dados inválidos
-- e confere se o banco recusa cada um PELA RESTRIÇÃO CERTA (pelo nome).
-- Também confere que dados válidos de borda são aceitos.
--
-- Tudo roda numa transação que termina em ROLLBACK: o banco não muda.
--
--   psql -U pontozero -d pontozero -v ON_ERROR_STOP=1 -f db/testes_integridade.sql
--   (no Docker:  docker compose exec -T db psql -U pontozero -d pontozero \
--                  -v ON_ERROR_STOP=1 < db/testes_integridade.sql)
--
-- Cada teste imprime "ok". Se algum falhar, o script para com "FALHOU".
-- =====================================================================

\set QUIET on
\pset tuples_only on
\pset format unaligned
SET client_min_messages = warning;
BEGIN;

-- ---------------------------------------------------------------------
-- deve_falhar(rótulo, comando, esperado)
--   esperado = nome da restrição (ex.: 'ck_usuario_senha'),
--              'not_null:<coluna>' para NOT NULL, 'trigger' para erro de
--              trigger, ou 'tipo:varchar' para texto maior que a coluna
-- ---------------------------------------------------------------------
CREATE FUNCTION pg_temp.deve_falhar(rotulo TEXT, comando TEXT, esperado TEXT)
RETURNS TEXT LANGUAGE plpgsql AS $$
DECLARE
    estado     TEXT;
    restricao  TEXT;
    coluna     TEXT;
    obtido     TEXT;
BEGIN
    BEGIN
        EXECUTE comando;
    EXCEPTION WHEN integrity_constraint_violation OR raise_exception OR string_data_right_truncation THEN
        GET STACKED DIAGNOSTICS estado    = RETURNED_SQLSTATE,
                                restricao = CONSTRAINT_NAME,
                                coluna    = COLUMN_NAME;
        obtido := CASE
                      WHEN estado = '23502' THEN 'not_null:' || coluna
                      WHEN estado = 'P0001' THEN 'trigger'
                      WHEN estado = '22001' THEN 'tipo:varchar'
                      ELSE restricao
                  END;
        IF obtido IS DISTINCT FROM esperado THEN
            RAISE EXCEPTION 'FALHOU  %: barrado por "%", esperado "%"', rotulo, obtido, esperado;
        END IF;
        RETURN format('ok  recusa  %s  [%s]', rotulo, obtido);
    END;
    RAISE EXCEPTION 'FALHOU  %: o banco ACEITOU um dado inválido', rotulo;
END;
$$;

-- deve_passar(rótulo, comando): dado válido de borda precisa ser aceito
CREATE FUNCTION pg_temp.deve_passar(rotulo TEXT, comando TEXT)
RETURNS TEXT LANGUAGE plpgsql AS $$
BEGIN
    EXECUTE comando;
    RETURN 'ok  aceita  ' || rotulo;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'FALHOU  %: recusou um dado válido (%)', rotulo, SQLERRM;
END;
$$;

CREATE FUNCTION pg_temp.falhou(msg TEXT) RETURNS TEXT LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'FALHOU  %', msg;
END;
$$;

-- atalhos para os IDs usados nos testes (buscados pelo nome, nunca fixos)
CREATE TEMP TABLE ref AS
SELECT (SELECT id_empresa   FROM empresa   WHERE nome = 'Rede Farma Nordeste (demonstração)') AS empresa,
       (SELECT id_regiao    FROM regiao    WHERE nome = 'Boa Viagem' AND cidade = 'Recife')   AS regiao,
       (SELECT id_categoria FROM categoria WHERE nome = 'Farmácia')                            AS categoria,
       (SELECT min(id_analise) FROM analise)                                                   AS analise;

CREATE FUNCTION pg_temp.r(campo TEXT) RETURNS TEXT LANGUAGE plpgsql AS $$
DECLARE v TEXT;
BEGIN
    EXECUTE format('SELECT %I::text FROM ref', campo) INTO v;
    RETURN v;
END;
$$;

\echo
\echo '== 1. Estrutura: toda tabela tem chave primária e pelo menos 3 linhas'
CREATE FUNCTION pg_temp.confere_estrutura() RETURNS SETOF TEXT LANGUAGE plpgsql AS $$
DECLARE
    t TEXT;
    n BIGINT;
BEGIN
    FOREACH t IN ARRAY ARRAY['empresa', 'usuario', 'categoria', 'regiao', 'indicador',
                             'estabelecimento', 'analise', 'regiao_analise', 'relatorio'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conrelid = t::regclass AND contype = 'p') THEN
            RAISE EXCEPTION 'FALHOU  tabela % sem chave primária', t;
        END IF;
        EXECUTE format('SELECT count(*) FROM %I', t) INTO n;
        IF n < 3 THEN
            RAISE EXCEPTION 'FALHOU  tabela % tem só % linha(s)', t, n;
        END IF;
        RETURN NEXT format('ok  %s PK presente, %s linhas', rpad(t, 16), n);
    END LOOP;
END;
$$;
SELECT pg_temp.confere_estrutura();

\echo
\echo '== 2. PRIMARY KEY'
SELECT pg_temp.deve_falhar('empresa com id repetido',
    format('INSERT INTO empresa (id_empresa, nome) VALUES (%s, %L)', pg_temp.r('empresa'), 'Outra'),
    'pk_empresa');
SELECT pg_temp.deve_falhar('mesma região duas vezes na mesma análise',
    format('INSERT INTO regiao_analise SELECT id_analise, id_regiao FROM regiao_analise WHERE id_analise = %s LIMIT 1',
           pg_temp.r('analise')),
    'pk_regiao_analise');

\echo
\echo '== 3. FOREIGN KEY'
SELECT pg_temp.deve_falhar('usuário de empresa que não existe',
    $q$INSERT INTO usuario (nome, email, senha, id_empresa)
       VALUES ('X', 'x@teste.com', '$2b$12$abcdefghijklmnopqrstuuMOcLk6Bv/9cYOmcqjSV5J2Ldpf1hO3S', -1)$q$,
    'fk_usuario_empresa');
SELECT pg_temp.deve_falhar('análise de empresa que não existe',
    $q$INSERT INTO analise (nome, id_empresa) VALUES ('X', -1)$q$, 'fk_analise_empresa');
SELECT pg_temp.deve_falhar('indicador de região que não existe',
    $q$INSERT INTO indicador (tipo, valor, fonte, id_regiao) VALUES ('populacao', 1, 'IBGE', -1)$q$,
    'fk_indicador_regiao');
SELECT pg_temp.deve_falhar('estabelecimento de região que não existe',
    format('INSERT INTO estabelecimento (nome, latitude, longitude, id_regiao, id_categoria) VALUES (%L, 0, 0, -1, %s)',
           'X', pg_temp.r('categoria')),
    'fk_estabelecimento_regiao');
SELECT pg_temp.deve_falhar('estabelecimento de categoria que não existe',
    format('INSERT INTO estabelecimento (nome, latitude, longitude, id_regiao, id_categoria) VALUES (%L, 0, 0, %s, -1)',
           'X', pg_temp.r('regiao')),
    'fk_estabelecimento_categoria');
SELECT pg_temp.deve_falhar('análise ligada a região que não existe',
    format('INSERT INTO regiao_analise VALUES (%s, -1)', pg_temp.r('analise')), 'fk_regiao_analise_regiao');
SELECT pg_temp.deve_falhar('região ligada a análise que não existe',
    format('INSERT INTO regiao_analise VALUES (-1, %s)', pg_temp.r('regiao')), 'fk_regiao_analise_analise');
SELECT pg_temp.deve_falhar('relatório de análise que não existe',
    $q$INSERT INTO relatorio (formato, id_analise) VALUES ('PDF', -1)$q$, 'fk_relatorio_analise');
-- ON DELETE RESTRICT: não se apaga o que ainda é usado
SELECT pg_temp.deve_falhar('apagar empresa que tem usuários (RESTRICT)',
    format('DELETE FROM empresa WHERE id_empresa = %s', pg_temp.r('empresa')), 'fk_usuario_empresa');
SELECT pg_temp.deve_falhar('apagar categoria que tem estabelecimentos (RESTRICT)',
    format('DELETE FROM categoria WHERE id_categoria = %s', pg_temp.r('categoria')), 'fk_estabelecimento_categoria');
SELECT pg_temp.deve_falhar('apagar região usada em análise (RESTRICT)',
    'DELETE FROM regiao WHERE id_regiao = (SELECT min(id_regiao) FROM regiao_analise)', 'fk_regiao_analise_regiao');

\echo
\echo '== 4. UNIQUE'
SELECT pg_temp.deve_falhar('CNPJ repetido',
    $q$INSERT INTO empresa (nome, cnpj) VALUES ('X', (SELECT cnpj FROM empresa WHERE cnpj IS NOT NULL LIMIT 1))$q$,
    'uq_empresa_cnpj');
SELECT pg_temp.deve_falhar('e-mail repetido, mesmo com outras maiúsculas',
    format($q$INSERT INTO usuario (nome, email, senha, id_empresa)
              VALUES ('X', 'DEMO@PontoZero.app', '$2b$12$abcdefghijklmnopqrstuuMOcLk6Bv/9cYOmcqjSV5J2Ldpf1hO3S', %s)$q$,
           pg_temp.r('empresa')),
    'uq_usuario_email');
SELECT pg_temp.deve_falhar('categoria com nome repetido',
    $q$INSERT INTO categoria (nome) VALUES ('Farmácia')$q$, 'uq_categoria_nome');
SELECT pg_temp.deve_falhar('mesmo bairro duas vezes na mesma cidade',
    $q$INSERT INTO regiao (nome, tipo, cidade, estado) VALUES ('Boa Viagem', 'Bairro', 'Recife', 'PE')$q$,
    'uq_regiao_local');
SELECT pg_temp.deve_falhar('dois valores do mesmo indicador e data na região',
    format($q$INSERT INTO indicador (tipo, valor, data_referencia, fonte, id_regiao)
              VALUES ('populacao', 1, '2022-07-31', 'IBGE', %s)$q$, pg_temp.r('regiao')),
    'uq_indicador_regiao_tipo_data');
SELECT pg_temp.deve_falhar('dois valores "sem data" do mesmo indicador (NULLS NOT DISTINCT)',
    format($q$INSERT INTO indicador (tipo, valor, data_referencia, fonte, id_regiao)
              VALUES ('area_km2', 1, NULL, 'Prefeitura', %s)$q$, pg_temp.r('regiao')),
    'uq_indicador_regiao_tipo_data');

\echo
\echo '== 5. NOT NULL'
SELECT pg_temp.deve_falhar('empresa sem nome',       $q$INSERT INTO empresa (nome) VALUES (NULL)$q$, 'not_null:nome');
SELECT pg_temp.deve_falhar('usuário sem e-mail',
    format($q$INSERT INTO usuario (nome, senha, id_empresa)
              VALUES ('X', '$2b$12$abcdefghijklmnopqrstuuMOcLk6Bv/9cYOmcqjSV5J2Ldpf1hO3S', %s)$q$, pg_temp.r('empresa')),
    'not_null:email');
SELECT pg_temp.deve_falhar('usuário sem senha',
    format($q$INSERT INTO usuario (nome, email, id_empresa) VALUES ('X', 'x@teste.com', %s)$q$, pg_temp.r('empresa')),
    'not_null:senha');
SELECT pg_temp.deve_falhar('usuário sem empresa',
    $q$INSERT INTO usuario (nome, email, senha)
       VALUES ('X', 'x@teste.com', '$2b$12$abcdefghijklmnopqrstuuMOcLk6Bv/9cYOmcqjSV5J2Ldpf1hO3S')$q$,
    'not_null:id_empresa');
SELECT pg_temp.deve_falhar('indicador sem fonte (HU-007)',
    format($q$INSERT INTO indicador (tipo, valor, id_regiao) VALUES ('domicilios', 1, %s)$q$, pg_temp.r('regiao')),
    'not_null:fonte');
SELECT pg_temp.deve_falhar('indicador sem valor',
    format($q$INSERT INTO indicador (tipo, fonte, id_regiao) VALUES ('domicilios', 'IBGE', %s)$q$, pg_temp.r('regiao')),
    'not_null:valor');
SELECT pg_temp.deve_falhar('estabelecimento sem latitude',
    format('INSERT INTO estabelecimento (nome, longitude, id_regiao, id_categoria) VALUES (%L, 0, %s, %s)',
           'X', pg_temp.r('regiao'), pg_temp.r('categoria')),
    'not_null:latitude');
SELECT pg_temp.deve_falhar('região sem estado',
    $q$INSERT INTO regiao (nome, tipo, cidade) VALUES ('X', 'Bairro', 'Olinda')$q$, 'not_null:estado');
SELECT pg_temp.deve_falhar('relatório sem formato',
    format('INSERT INTO relatorio (id_analise) VALUES (%s)', pg_temp.r('analise')), 'not_null:formato');

\echo
\echo '== 6. CHECK'
SELECT pg_temp.deve_falhar('empresa com nome só de espaços',
    $q$INSERT INTO empresa (nome) VALUES ('   ')$q$, 'ck_empresa_nome');
SELECT pg_temp.deve_falhar('CNPJ com pontuação',
    $q$INSERT INTO empresa (nome, cnpj) VALUES ('X', '11.222.333/000')$q$, 'ck_empresa_cnpj');
SELECT pg_temp.deve_falhar('CNPJ com mais de 14 caracteres (tipo VARCHAR(14))',
    $q$INSERT INTO empresa (nome, cnpj) VALUES ('X', '11.222.333/0001-81')$q$, 'tipo:varchar');
SELECT pg_temp.deve_falhar('CNPJ com 13 dígitos',
    $q$INSERT INTO empresa (nome, cnpj) VALUES ('X', '1122233300018')$q$, 'ck_empresa_cnpj');
SELECT pg_temp.deve_falhar('segmento vazio',
    $q$INSERT INTO empresa (nome, segmento) VALUES ('X', '')$q$, 'ck_empresa_segmento');
SELECT pg_temp.deve_falhar('senha em texto puro',
    format($q$INSERT INTO usuario (nome, email, senha, id_empresa) VALUES ('X', 'x@teste.com', '12345678', %s)$q$,
           pg_temp.r('empresa')),
    'ck_usuario_senha');
SELECT pg_temp.deve_falhar('senha que só começa como bcrypt',
    format($q$INSERT INTO usuario (nome, email, senha, id_empresa)
              VALUES ('X', 'x@teste.com', '$2' || repeat('a', 60), %s)$q$, pg_temp.r('empresa')),
    'ck_usuario_senha');
SELECT pg_temp.deve_falhar('e-mail sem @',
    format($q$INSERT INTO usuario (nome, email, senha, id_empresa)
              VALUES ('X', 'nao-e-email', '$2b$12$abcdefghijklmnopqrstuuMOcLk6Bv/9cYOmcqjSV5J2Ldpf1hO3S', %s)$q$,
           pg_temp.r('empresa')),
    'ck_usuario_email');
SELECT pg_temp.deve_falhar('perfil fora da lista',
    format($q$INSERT INTO usuario (nome, email, senha, perfil, id_empresa)
              VALUES ('X', 'x@teste.com', '$2b$12$abcdefghijklmnopqrstuuMOcLk6Bv/9cYOmcqjSV5J2Ldpf1hO3S', 'root', %s)$q$,
           pg_temp.r('empresa')),
    'ck_usuario_perfil');
SELECT pg_temp.deve_falhar('categoria com nome vazio',
    $q$INSERT INTO categoria (nome) VALUES ('')$q$, 'ck_categoria_nome');
SELECT pg_temp.deve_falhar('estado em minúsculas',
    $q$INSERT INTO regiao (nome, tipo, cidade, estado) VALUES ('X', 'Bairro', 'Olinda', 'pe')$q$, 'ck_regiao_estado');
SELECT pg_temp.deve_falhar('estado com 1 letra',
    $q$INSERT INTO regiao (nome, tipo, cidade, estado) VALUES ('X', 'Bairro', 'Olinda', 'P')$q$, 'ck_regiao_estado');
SELECT pg_temp.deve_falhar('região com tipo vazio',
    $q$INSERT INTO regiao (nome, tipo, cidade, estado) VALUES ('X', ' ', 'Olinda', 'PE')$q$, 'ck_regiao_tipo');
SELECT pg_temp.deve_falhar('indicador de tipo desconhecido',
    format($q$INSERT INTO indicador (tipo, valor, fonte, id_regiao) VALUES ('felicidade', 1, 'X', %s)$q$,
           pg_temp.r('regiao')),
    'ck_indicador_tipo');
SELECT pg_temp.deve_falhar('densidade guardada (é calculada na view)',
    format($q$INSERT INTO indicador (tipo, valor, fonte, id_regiao) VALUES ('densidade', 1, 'X', %s)$q$,
           pg_temp.r('regiao')),
    'ck_indicador_tipo');
SELECT pg_temp.deve_falhar('indicador com valor negativo',
    format($q$INSERT INTO indicador (tipo, valor, data_referencia, fonte, id_regiao)
              VALUES ('domicilios', -5, '2030-01-01', 'IBGE', %s)$q$, pg_temp.r('regiao')),
    'ck_indicador_valor');
SELECT pg_temp.deve_falhar('indicador com fonte só de espaços',
    format($q$INSERT INTO indicador (tipo, valor, data_referencia, fonte, id_regiao)
              VALUES ('domicilios', 1, '2030-01-01', '  ', %s)$q$, pg_temp.r('regiao')),
    'ck_indicador_fonte');
SELECT pg_temp.deve_falhar('indicador com data antes de 1900',
    format($q$INSERT INTO indicador (tipo, valor, data_referencia, fonte, id_regiao)
              VALUES ('domicilios', 1, '1800-01-01', 'IBGE', %s)$q$, pg_temp.r('regiao')),
    'ck_indicador_data');
SELECT pg_temp.deve_falhar('latitude acima de 90',
    format('INSERT INTO estabelecimento (nome, latitude, longitude, id_regiao, id_categoria) VALUES (%L, 91, 0, %s, %s)',
           'X', pg_temp.r('regiao'), pg_temp.r('categoria')),
    'ck_estabelecimento_latitude');
SELECT pg_temp.deve_falhar('longitude abaixo de -180',
    format('INSERT INTO estabelecimento (nome, latitude, longitude, id_regiao, id_categoria) VALUES (%L, 0, -181, %s, %s)',
           'X', pg_temp.r('regiao'), pg_temp.r('categoria')),
    'ck_estabelecimento_longitude');
SELECT pg_temp.deve_falhar('estabelecimento com nome vazio',
    format('INSERT INTO estabelecimento (nome, latitude, longitude, id_regiao, id_categoria) VALUES (%L, 0, 0, %s, %s)',
           '', pg_temp.r('regiao'), pg_temp.r('categoria')),
    'ck_estabelecimento_nome');
SELECT pg_temp.deve_falhar('endereço só de espaços',
    format('INSERT INTO estabelecimento (nome, latitude, longitude, endereco, id_regiao, id_categoria) VALUES (%L, 0, 0, %L, %s, %s)',
           'X', '  ', pg_temp.r('regiao'), pg_temp.r('categoria')),
    'ck_estabelecimento_endereco');
SELECT pg_temp.deve_falhar('análise com nome vazio',
    format($q$INSERT INTO analise (nome, id_empresa) VALUES ('', %s)$q$, pg_temp.r('empresa')), 'ck_analise_nome');
SELECT pg_temp.deve_falhar('análise com data absurda (antes de 2020)',
    format($q$INSERT INTO analise (nome, data_criacao, id_empresa) VALUES ('X', '1999-12-31', %s)$q$,
           pg_temp.r('empresa')),
    'ck_analise_data');
SELECT pg_temp.deve_falhar('relatório em formato DOCX',
    format($q$INSERT INTO relatorio (formato, id_analise) VALUES ('DOCX', %s)$q$, pg_temp.r('analise')),
    'ck_relatorio_formato');
SELECT pg_temp.deve_falhar('relatório com formato em minúsculas',
    format($q$INSERT INTO relatorio (formato, id_analise) VALUES ('pdf', %s)$q$, pg_temp.r('analise')),
    'ck_relatorio_formato');

\echo
\echo '== 7. Dados válidos de borda continuam aceitos'
SELECT pg_temp.deve_passar('empresa sem CNPJ e sem segmento (campos opcionais)',
    $q$INSERT INTO empresa (nome) VALUES ('Empresa só com nome')$q$);
SELECT pg_temp.deve_passar('várias empresas sem CNPJ (UNIQUE aceita vários NULL)',
    $q$INSERT INTO empresa (nome) VALUES ('Outra sem CNPJ'), ('Mais uma sem CNPJ')$q$);
SELECT pg_temp.deve_passar('mesmo nome de bairro em outra cidade',
    $q$INSERT INTO regiao (nome, tipo, cidade, estado) VALUES ('Boa Viagem', 'Bairro', 'Natal', 'RN')$q$);
SELECT pg_temp.deve_passar('indicador sem data de referência (fonte não informa)',
    $q$INSERT INTO indicador (tipo, valor, data_referencia, fonte, id_regiao)
       SELECT 'area_km2', 10, NULL, 'Prefeitura de Natal', id_regiao FROM regiao WHERE cidade = 'Natal'$q$);
SELECT pg_temp.deve_passar('mesmo indicador em outra data (série histórica)',
    format($q$INSERT INTO indicador (tipo, valor, data_referencia, fonte, id_regiao)
              VALUES ('populacao', 1, '2030-07-31', 'IBGE', %s)$q$, pg_temp.r('regiao')));
SELECT pg_temp.deve_passar('coordenadas exatamente nos limites (-90/180)',
    format('INSERT INTO estabelecimento (nome, latitude, longitude, id_regiao, id_categoria) VALUES (%L, -90, 180, %s, %s)',
           'Borda', pg_temp.r('regiao'), pg_temp.r('categoria')));
SELECT pg_temp.deve_passar('perfil padrão é analista',
    format($q$INSERT INTO usuario (nome, email, senha, id_empresa)
              VALUES ('Novo', 'novo@teste.com', '$2b$12$abcdefghijklmnopqrstuuMOcLk6Bv/9cYOmcqjSV5J2Ldpf1hO3S', %s)$q$,
           pg_temp.r('empresa')));
SELECT CASE WHEN perfil = 'analista' THEN 'ok  confere  perfil gravado como analista'
            ELSE pg_temp.falhou('perfil padrão não é analista') END
FROM usuario WHERE lower(email) = 'novo@teste.com';

\echo
\echo '== 8. Ações das chaves estrangeiras (CASCADE)'
CREATE FUNCTION pg_temp.confere_cascade() RETURNS SETOF TEXT LANGUAGE plpgsql AS $$
DECLARE
    a INT := (SELECT min(id_analise) FROM analise a
              WHERE EXISTS (SELECT 1 FROM relatorio r WHERE r.id_analise = a.id_analise));
BEGIN
    DELETE FROM analise WHERE id_analise = a;
    IF EXISTS (SELECT 1 FROM regiao_analise WHERE id_analise = a)
       OR EXISTS (SELECT 1 FROM relatorio WHERE id_analise = a) THEN
        RAISE EXCEPTION 'FALHOU  apagar análise não levou junto regiões e relatórios';
    END IF;
    RETURN NEXT 'ok  cascade  apagar análise apaga suas regiões (N:N) e relatórios';

    DELETE FROM regiao WHERE cidade = 'Natal';
    IF EXISTS (SELECT 1 FROM indicador WHERE fonte = 'Prefeitura de Natal') THEN
        RAISE EXCEPTION 'FALHOU  apagar região não levou junto seus indicadores';
    END IF;
    RETURN NEXT 'ok  cascade  apagar região apaga seus indicadores';
END;
$$;
SELECT pg_temp.confere_cascade();

\echo
\echo '== 9. Triggers (só quando 02_indices_e_regras.sql foi carregado)'
CREATE FUNCTION pg_temp.confere_triggers() RETURNS SETOF TEXT LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_usuario_email') THEN
        RETURN NEXT '--  triggers não carregados neste banco: pulando (rode db/init/02_indices_e_regras.sql)';
        RETURN;
    END IF;

    INSERT INTO usuario (nome, email, senha, id_empresa)
    VALUES ('Caixa', '  Caixa.Alta@Teste.COM ', '$2b$12$abcdefghijklmnopqrstuuMOcLk6Bv/9cYOmcqjSV5J2Ldpf1hO3S',
            (SELECT min(id_empresa) FROM empresa));
    IF NOT EXISTS (SELECT 1 FROM usuario WHERE email = 'caixa.alta@teste.com') THEN
        RAISE EXCEPTION 'FALHOU  trigger não normalizou o e-mail';
    END IF;
    RETURN NEXT 'ok  trigger  e-mail gravado em minúsculas e sem espaços';

    RETURN NEXT pg_temp.deve_falhar('análise com data no futuro',
        format('INSERT INTO analise (nome, data_criacao, id_empresa) VALUES (%L, CURRENT_DATE + 1, %s)',
               'Futuro', (SELECT min(id_empresa) FROM empresa)),
        'trigger');
END;
$$;
SELECT pg_temp.confere_triggers();

\echo
\echo 'Todos os testes passaram. Desfazendo tudo (ROLLBACK): o banco continua igual.'
ROLLBACK;
