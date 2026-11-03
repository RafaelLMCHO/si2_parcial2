\set ON_ERROR_STOP on
\ir 00_reset.sql
\ir ../db/run_all.sql
\ir 01_aislamiento_tenant.sql
\ir 02_stock_concurrente.sql
\ir 03_offline_idempotencia.sql
\ir 04_pagos_devoluciones.sql
\ir 05_rls_auditoria.sql
\ir 06_limites_planes.sql
\ir 07_cobertura_36.sql
\ir 08_cu06_cu09.sql
