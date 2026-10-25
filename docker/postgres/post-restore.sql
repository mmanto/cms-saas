-- ============================================================================
-- post-restore.sql — re-aplica el hardening de ACLs despues de un pg_restore
--
-- Por que existe:
--   `docker/backup/backup.sh` hace `pg_dump --no-privileges` (no guarda
--   GRANT/REVOKE). Al restaurar, las tablas las recrea `saas_migrator` y los
--   `ALTER DEFAULT PRIVILEGES` de `roles.sh` vuelven a dar DML a `saas_app`
--   sobre TODAS las tablas, incluido `platform_users` y el registro global
--   (`tenants`/`tenant_domains`). Las policies de RLS si sobreviven (son DDL),
--   pero se pierde el resto del aislamiento / defensa en profundidad.
--
-- Uso (rol superusuario, con la API/worker detenidos para no escribir durante
-- el restore):
--   DC="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
--   $DC exec -T postgres sh -c \
--     'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f -' \
--     < docker/postgres/post-restore.sql
--
-- Idempotente: se puede correr las veces que haga falta (tambien en cada `up`).
-- La ejecuta el superusuario porque `ALTER ROLE ... (NO)BYPASSRLS` solo la puede
-- hacer un superusuario (un owner de tablas no alcanza).
-- ============================================================================

BEGIN;

-- 1) El rol de la API (RLS, NOBYPASSRLS) no escribe el registro global.
REVOKE INSERT, UPDATE, DELETE ON tenants, tenant_domains FROM saas_app;
REVOKE ALL ON platform_users FROM saas_app;
GRANT SELECT ON tenants, tenant_domains TO saas_app;

-- 2) DML de la API SOLO en las tablas tenant-scoped (RLS en migraciones 0001-0003).
GRANT SELECT, INSERT, UPDATE, DELETE
    ON tenant_users, tenant_credentials, tenant_branding, tenant_assets
    TO saas_app;

-- 3) El rol de plataforma (BYPASSRLS) necesita provisioning cross-tenant.
GRANT SELECT, INSERT, UPDATE, DELETE
    ON tenants, tenant_domains, tenant_users, tenant_credentials,
       tenant_branding, tenant_assets, platform_users
    TO saas_platform;

-- 4) Secuencias: con --no-privileges el restore tampoco trae sus ACLs.
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO saas_app, saas_platform;

-- 5) Default privileges para las tablas que cree el migrador de ahora en mas.
--    OJO: esto es fail-open a proposito (mismo criterio que roles.sh): toda
--    tabla nueva con tenant_id DEBE crear su policy de RLS en la migracion.
ALTER DEFAULT PRIVILEGES FOR ROLE saas_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO saas_app, saas_platform;
ALTER DEFAULT PRIVILEGES FOR ROLE saas_migrator IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO saas_app, saas_platform;

-- 6) Blindaje de RLS: la API nunca debe poder saltearlo; plataforma si.
ALTER ROLE saas_app NOBYPASSRLS;
ALTER ROLE saas_platform BYPASSRLS;

COMMIT;

-- 7) Canario: ninguna tabla con tenant_id puede quedar sin RLS.
--    Va FUERA de la transaccion anterior: si falla, el hardening ya commiteado
--    queda aplicado y el error avisa igual.
DO $$
DECLARE
    sin_rls text;
BEGIN
    SELECT string_agg(c.relname, ', ' ORDER BY c.relname)
      INTO sin_rls
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
       AND c.relkind = 'r'
       AND EXISTS (
             SELECT 1
               FROM information_schema.columns col
              WHERE col.table_schema = 'public'
                AND col.table_name = c.relname
                AND col.column_name = 'tenant_id'
           )
       AND NOT c.relrowsecurity;

    IF sin_rls IS NOT NULL THEN
        RAISE EXCEPTION 'tablas con tenant_id y SIN RLS: %', sin_rls;
    END IF;

    RAISE NOTICE 'post-restore ok: ACLs/roles restaurados y toda tabla con tenant_id tiene RLS';
END $$;
