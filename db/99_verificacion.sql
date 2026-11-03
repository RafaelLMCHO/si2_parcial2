DO $$
DECLARE
    v_tablas integer;
    v_particionadas integer;
BEGIN
    SELECT count(*)
      INTO v_tablas
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
       AND c.relkind IN ('r', 'p')
       AND c.relispartition = false;

    SELECT count(*)
      INTO v_particionadas
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
       AND c.relkind = 'p'
       AND c.relispartition = false;

    IF v_tablas <> 56 THEN
        RAISE EXCEPTION 'Se esperaban 56 tablas, se encontraron %', v_tablas;
    END IF;

    IF v_particionadas <> 3 THEN
        RAISE EXCEPTION 'Se esperaban 3 tablas particionadas, se encontraron %', v_particionadas;
    END IF;
END $$;

SELECT
    (SELECT count(*)
       FROM pg_class c
       JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = 'public'
        AND c.relkind IN ('r', 'p')
        AND c.relispartition = false) AS tablas,
    (SELECT count(*)
       FROM pg_class c
       JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = 'public'
        AND c.relkind = 'p'
        AND c.relispartition = false) AS tablas_particionadas,
    (SELECT count(*) FROM pg_policy) AS politicas_rls,
    (SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal) AS triggers;
