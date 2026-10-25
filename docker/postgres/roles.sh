#!/bin/sh
# Crea/actualiza los roles de Postgres. Idempotente: se ejecuta en cada `up`
# para que los passwords del .env siempre coincidan con los de la base.
#
#   saas_migrator -> duenio del esquema y las tablas. Solo Alembic. Puede
#                    saltear RLS porque es owner (nunca lo usa la API).
#   saas_app      -> rol de la API y del worker. NO es owner y NO puede
#                    saltear RLS: el aislamiento entre tenants depende de esto.
#   saas_platform -> provisioning cross-tenant (BYPASSRLS). Solo alta de
#                    tenants, dominios y usuarios de plataforma.
set -eu

: "${PGHOST:?}"
: "${MIGRATOR_DB_PASSWORD:?}"
: "${APP_DB_PASSWORD:?}"
: "${PLATFORM_DB_PASSWORD:?}"

psql -v ON_ERROR_STOP=1 <<'EOSQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'saas_migrator') THEN
        CREATE ROLE saas_migrator LOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'saas_app') THEN
        CREATE ROLE saas_app LOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'saas_platform') THEN
        CREATE ROLE saas_platform LOGIN;
    END IF;
END
$$;
EOSQL

# Los passwords y atributos van fuera del bloque dollar-quoted: psql no
# interpola variables dentro de $$...$$.
psql -v ON_ERROR_STOP=1 \
     -v migrator_password="$MIGRATOR_DB_PASSWORD" \
     -v app_password="$APP_DB_PASSWORD" \
     -v platform_password="$PLATFORM_DB_PASSWORD" <<'EOSQL'
ALTER ROLE saas_migrator WITH LOGIN PASSWORD :'migrator_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
ALTER ROLE saas_app WITH LOGIN PASSWORD :'app_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
ALTER ROLE saas_platform WITH LOGIN PASSWORD :'platform_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE BYPASSRLS;

-- El migrador es duenio del esquema: es el unico que hace DDL.
ALTER SCHEMA public OWNER TO saas_migrator;

-- DBNAME es la variable especial de psql con la base conectada. Ojo: PGDATABASE
-- es de libpq y NO existe como variable de psql.
GRANT CONNECT ON DATABASE :"DBNAME" TO saas_app, saas_platform;
GRANT USAGE ON SCHEMA public TO saas_app, saas_platform;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Privilegios por defecto: todo lo que cree el migrador queda usable por la
-- API. Si agregas una tabla global (sin tenant_id) acordate de revocarle DML
-- a saas_app en la migracion.
ALTER DEFAULT PRIVILEGES FOR ROLE saas_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO saas_app, saas_platform;
ALTER DEFAULT PRIVILEGES FOR ROLE saas_migrator IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO saas_app, saas_platform;

-- Blindaje: la API nunca debe poder saltear RLS.
ALTER ROLE saas_app NOBYPASSRLS;

-- PostGIS (postgis)
CREATE EXTENSION IF NOT EXISTS postgis;
-- spatial_ref_sys y las vistas de catalogo las crea el superusuario:
-- la app solo las lee (ST_Transform y los visores GIS las consultan).
GRANT SELECT ON spatial_ref_sys TO saas_app, saas_platform;
GRANT SELECT ON geometry_columns, geography_columns TO saas_app, saas_platform;
EOSQL

echo "[roles] ok"
