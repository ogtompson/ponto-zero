BEGIN;

ALTER TABLE analise ADD COLUMN IF NOT EXISTS id_categoria INT;
ALTER TABLE analise ADD COLUMN IF NOT EXISTS versao_metodologia VARCHAR(30) NOT NULL DEFAULT 'legado';
ALTER TABLE analise ADD COLUMN IF NOT EXISTS capturado_em TIMESTAMPTZ;
ALTER TABLE analise ADD COLUMN IF NOT EXISTS snapshot JSONB;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'analise_id_categoria_fkey') THEN
    ALTER TABLE analise
      ADD CONSTRAINT analise_id_categoria_fkey
      FOREIGN KEY (id_categoria) REFERENCES categoria (id_categoria) ON DELETE RESTRICT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'analise_snapshot_objeto') THEN
    ALTER TABLE analise
      ADD CONSTRAINT analise_snapshot_objeto
      CHECK (snapshot IS NULL OR jsonb_typeof(snapshot) = 'object');
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_analise_categoria ON analise (id_categoria);

CREATE OR REPLACE FUNCTION fn_preserva_snapshot_analise()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.snapshot IS NOT NULL AND (
       NEW.snapshot IS DISTINCT FROM OLD.snapshot
    OR NEW.id_categoria IS DISTINCT FROM OLD.id_categoria
    OR NEW.versao_metodologia IS DISTINCT FROM OLD.versao_metodologia
    OR NEW.capturado_em IS DISTINCT FROM OLD.capturado_em
  ) THEN
    RAISE EXCEPTION 'snapshot de análise é imutável';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_analise_snapshot_imutavel ON analise;
CREATE TRIGGER trg_analise_snapshot_imutavel
BEFORE UPDATE OF snapshot, id_categoria, versao_metodologia, capturado_em ON analise
FOR EACH ROW EXECUTE FUNCTION fn_preserva_snapshot_analise();

CREATE OR REPLACE VIEW vw_resumo_analise AS
SELECT a.id_analise,
       a.nome,
       a.data_criacao,
       a.objetivo,
       a.id_empresa,
       e.nome AS empresa,
       COALESCE(c.nome, e.segmento) AS segmento,
       (SELECT count(*) FROM regiao_analise ra WHERE ra.id_analise = a.id_analise)::int AS qtd_regioes,
       (SELECT count(*) FROM relatorio rl WHERE rl.id_analise = a.id_analise)::int AS qtd_relatorios,
       (SELECT max(rl.data_geracao) FROM relatorio rl WHERE rl.id_analise = a.id_analise) AS ultimo_relatorio,
       a.id_categoria,
       a.versao_metodologia,
       a.capturado_em,
       (a.snapshot IS NOT NULL) AS snapshot_disponivel
FROM analise a
JOIN empresa e ON e.id_empresa = a.id_empresa
LEFT JOIN categoria c ON c.id_categoria = a.id_categoria;

COMMIT;
