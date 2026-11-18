-- =====================================================================
-- PontoZero | 02 - Índices e regras automáticas (triggers)
-- =====================================================================

-- E-mail único sem diferenciar maiúsculas/minúsculas (HU-001 RN03)
CREATE UNIQUE INDEX ux_usuario_email ON usuario (lower(email));

-- Índices nas chaves estrangeiras usadas nos JOINs da aplicação
CREATE INDEX ix_usuario_empresa            ON usuario (id_empresa);
CREATE INDEX ix_analise_empresa            ON analise (id_empresa);
CREATE INDEX ix_regiao_analise_regiao      ON regiao_analise (id_regiao);
CREATE INDEX ix_relatorio_analise          ON relatorio (id_analise);
CREATE INDEX ix_indicador_regiao_tipo      ON indicador (id_regiao, tipo);
CREATE INDEX ix_estabelecimento_regiao_cat ON estabelecimento (id_regiao, id_categoria);
CREATE INDEX ix_estabelecimento_categoria  ON estabelecimento (id_categoria);

-- ---------------------------------------------------------------------
-- Trigger: guarda o e-mail sempre em minúsculas e sem espaços nas pontas
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_normaliza_email()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.email := lower(trim(NEW.email));
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_usuario_email
BEFORE INSERT OR UPDATE OF email ON usuario
FOR EACH ROW EXECUTE FUNCTION fn_normaliza_email();

-- ---------------------------------------------------------------------
-- Trigger: uma análise precisa ser criada com data de hoje ou passada
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_valida_data_analise()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.data_criacao > CURRENT_DATE THEN
        RAISE EXCEPTION 'data_criacao (%) não pode estar no futuro', NEW.data_criacao;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_analise_data
BEFORE INSERT OR UPDATE OF data_criacao ON analise
FOR EACH ROW EXECUTE FUNCTION fn_valida_data_analise();
