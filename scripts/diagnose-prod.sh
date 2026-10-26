#!/usr/bin/env bash
# Diagnostico de SOLO LECTURA del stack de produccion.
#
# No cambia nada: corre desde el host, junta estado y clasifica el fallo por
# capa (codigo -> contenedores -> puertos -> DNS -> TLS -> Traefik -> app -> DB).
#
# Uso:
#   make prod-doctor
#   ENV_FILE=otro.env ./scripts/diagnose-prod.sh
#   EXTRA_HOSTS="auxiliosrb.com portal.ejemplo.com" ./scripts/diagnose-prod.sh
set -uo pipefail

cd "$(dirname "$0")/.."
ENV_FILE=${ENV_FILE:-.env}
DC=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)
EXTRA_HOSTS=${EXTRA_HOSTS:-}

FAIL=0
WARN=0

section() { printf '\n\033[1m=== %s ===\033[0m\n' "$*"; }
ok() { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; WARN=$((WARN + 1)); }
bad() { printf '  \033[31m✗\033[0m %s\n' "$*"; FAIL=$((FAIL + 1)); }
info() { printf '    %s\n' "$*"; }

read_env() {
    local key=$1
    if [ -n "${!key+x}" ]; then printf '%s' "${!key}"; return; fi
    [ -f "$ENV_FILE" ] || return 0
    sed -n "s/^[[:space:]]*${key}=//p" "$ENV_FILE" | tail -n 1
}

mask() {
    local value=$1
    if [ -z "$value" ]; then printf 'vacio'; else printf 'set (%d chars)' "${#value}"; fi
}

base=$(read_env SAAS_BASE_DOMAIN | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
provider=$(read_env ACME_DNS_PROVIDER | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
public_ip=""

printf '\033[1mDiagnostico de produccion\033[0m  %s\n' "$(date -Is 2>/dev/null || date)"
info "host: $(hostname 2>/dev/null || echo '?') · repo: $(pwd) · env: $ENV_FILE"

# ---------------------------------------------------------------- 1. codigo
section "1. Codigo y configuracion"
if git rev-parse --git-dir >/dev/null 2>&1; then
    info "commit: $(git rev-parse --short HEAD 2>/dev/null) · branch: $(git branch --show-current 2>/dev/null)"
    dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    if [ "$dirty" = "0" ]; then ok "working tree limpio"; else warn "$dirty archivo(s) locales sin commitear/revisar"; fi
else
    warn "no es un repo git: no puedo verificar si el servidor tiene el codigo al dia"
fi

check_marker() {
    if grep -q "$2" "$1" 2>/dev/null; then
        ok "codigo al dia: $3"
    else
        bad "codigo VIEJO en el servidor: $3 (falta en $1)"
    fi
}
check_marker backend/app/provisioning.py 'domains": \[' 'certificado wildcard pide domains como lista'
check_marker docker-compose.prod.yml 'dnsChallenge=true' 'traefik con dnsChallenge explicito'
check_marker docker-compose.prod.yml 'HOSTINGER_API_TOKEN' 'compose pasa HOSTINGER_API_TOKEN'
check_marker scripts/preflight-prod.sh 'hostinger)' 'preflight reconoce hostinger'
check_marker frontend/app/admin/admin-sidebar.tsx "title: 'Portales'" 'admin renombrado a Portales'
check_marker frontend/lib/env.ts 'BASE_TENANT' 'apex como portal (frontend)'
check_marker backend/app/tenancy.py 'saas_base_tenant' 'apex como portal (backend)'

for key in SAAS_BASE_DOMAIN SAAS_BASE_TENANT ACME_DNS_PROVIDER ACME_EMAIL; do
    printf '    %-22s %s\n' "$key" "$(read_env "$key")"
done
for key in CF_DNS_API_TOKEN CF_DNS_API_KEY HOSTINGER_API_TOKEN AWS_SECRET_ACCESS_KEY; do
    printf '    %-22s %s\n' "$key" "$(mask "$(read_env "$key")")"
done

if [ -z "$base" ]; then
    bad "SAAS_BASE_DOMAIN vacio"
elif printf '%s' "$base" | grep -q '\.localhost$'; then
    bad "SAAS_BASE_DOMAIN=$base: en produccion no hay router para tu dominio real"
else
    ok "dominio base: $base"
fi
if [ -z "$provider" ]; then bad "ACME_DNS_PROVIDER vacio"; else ok "provider DNS-01: $provider"; fi

# ------------------------------------------------------------ 2. contenedores
section "2. Contenedores (config files incluidos)"
if ! "${DC[@]}" ps -a --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}' 2>&1 | sed 's/^/  /'; then
    bad "no pude ejecutar docker compose"
fi

section "2b. Origen de cada contenedor (dev vs prod) y reinicios"
seen=""
for cid in $(docker ps -aq --filter label=com.docker.compose.project=cms-sas 2>/dev/null); do
    svc=$(docker inspect "$cid" --format '{{index .Config.Labels "com.docker.compose.service"}}' 2>/dev/null)
    case " $seen " in *" $svc "*) continue ;; esac
    seen="$seen $svc"
    files=$(docker inspect "$cid" --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}' 2>/dev/null)
    state=$(docker inspect "$cid" --format '{{.State.Status}} exit={{.State.ExitCode}} restarts={{.RestartCount}}' 2>/dev/null)
    printf '    %-16s %-28s %s\n' "$svc" "$state" "$files"
done

traefik=$(docker ps -q -f label=com.docker.compose.service=traefik 2>/dev/null | head -n1)
if [ -z "$traefik" ]; then
    bad "traefik no esta corriendo (por eso no responde nada en 80/443)"
else
    ok "traefik corriendo"
    section "3. Traefik en ejecucion"
    cmd=$(docker inspect "$traefik" --format '{{range .Config.Cmd}}{{println .}}{{end}}' 2>/dev/null || true)
    printf '%s' "$cmd" | grep -E 'dnsChallenge|entrypoints\.(web|websecure)\.address|api\.insecure' \
        | sed 's/^/    /'
    running_provider=$(printf '%s' "$cmd" | sed -n 's/^--certificatesresolvers\.[^=]*\.dnsChallenge\.provider=//p' | head -n1)
    if [ -z "$running_provider" ]; then
        bad "el traefik corriendo no tiene DNS-01 (¿se levanto sin docker-compose.prod.yml?)"
    elif [ "$running_provider" != "$provider" ]; then
        bad "traefik corre con provider '$running_provider', el .env dice '$provider' (no se recreo)"
    else
        ok "provider en ejecucion: $running_provider"
    fi
fi

# ----------------------------------------------------------------- 3. puertos
section "4. Puertos 80/443"
if command -v ss >/dev/null 2>&1; then
    listeners=$(ss -H -ltn 2>/dev/null | awk '{print $4}' | grep -E ':(80|443)$' | sort -u)
    if [ -n "$listeners" ]; then
        ok "escuchando: $(printf '%s' "$listeners" | tr '\n' ' ')"
    else
        bad "nada escucha en 80/443"
    fi
else
    warn "sin ss: no pude verificar puertos"
fi

# ------------------------------------------------------------------- 4. rutas
if [ -n "$traefik" ]; then
    dyn=$(docker inspect "$traefik" --format '{{range .Mounts}}{{if eq .Destination "/etc/traefik/dynamic"}}{{.Name}}{{end}}{{end}}' 2>/dev/null || true)
    if [ -n "$dyn" ]; then
        section "5. routes.yml (volume $dyn)"
        docker run --rm -i -v "$dyn":/d:ro alpine:3.22 sh -s <<'SH' 2>/dev/null | sed 's/^/    /'
ls -l /d
echo "-- hosts --"
grep -o 'Host(`[^`]*`)' /d/routes.yml 2>/dev/null | sort -u
echo "-- certResolver --"
grep -o '"certResolver": "[^"]*"' /d/routes.yml 2>/dev/null | sort | uniq -c
SH
        if [ -z "$(docker run --rm -v "$dyn":/d:ro alpine:3.22 sh -c 'test -s /d/routes.yml && echo si' 2>/dev/null)" ]; then
            bad "routes.yml no existe o esta vacio: el borde no tiene routers"
        fi
    else
        warn "no encontre el volumen de /etc/traefik/dynamic"
    fi
fi

# --------------------------------------------------------------------- 5. DNS
section "6. DNS"
if command -v getent >/dev/null 2>&1; then
    for host in "$base" "admin.$base" "doctor.$base" $EXTRA_HOSTS; do
        [ -n "$host" ] || continue
        if getent ahosts "$host" >/dev/null 2>&1; then
            ips=$(getent ahosts "$host" | awk '$2=="STREAM"{print $1}' | sort -u | tr '\n' ' ')
            ok "$host -> $ips"
        else
            bad "$host no resuelve (NXDOMAIN)"
        fi
    done
else
    warn "sin getent: no pude verificar DNS"
fi
if command -v curl >/dev/null 2>&1; then
    public_ip=$(curl -4 -s --max-time 5 https://api.ipify.org 2>/dev/null || true)
    [ -n "$public_ip" ] && info "IP publica del servidor: $public_ip"
fi

# --------------------------------------------------------------- 6. HTTP/TLS
section "7. Borde HTTP/HTTPS"
if command -v curl >/dev/null 2>&1 && [ -n "$base" ]; then
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 -H "Host: $base" http://127.0.0.1/ 2>/dev/null || true)
    case "$code" in
        301 | 302 | 307 | 308) ok "http://$base -> $code (redirige a https)" ;;
        000) bad "nada respondio en http://127.0.0.1:80" ;;
        *) bad "http://$base -> $code (se esperaba 3xx)" ;;
    esac

    code=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 8 --resolve "$base:443:127.0.0.1" "https://$base/" 2>/dev/null || true)
    case "$code" in
        200 | 301 | 302 | 307 | 308) ok "https://$base/ -> $code" ;;
        404) bad "https://$base/ -> 404: ningun router de Traefik matchea ese Host" ;;
        000) bad "https://$base/ no completo el handshake" ;;
        *) bad "https://$base/ -> $code" ;;
    esac

    code=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 8 --resolve "admin.$base:443:127.0.0.1" "https://admin.$base/admin" 2>/dev/null || true)
    case "$code" in
        200 | 301 | 302 | 307 | 308) ok "https://admin.$base/admin -> $code" ;;
        *) bad "https://admin.$base/admin -> ${code:-000}" ;;
    esac
fi

if command -v openssl >/dev/null 2>&1 && [ -n "$base" ]; then
    issuer=$(echo | timeout 10 openssl s_client -connect 127.0.0.1:443 -servername "$base" 2>/dev/null \
        | openssl x509 -noout -issuer 2>/dev/null | tr -d '\r')
    if [ -z "$issuer" ]; then
        bad "no pude leer el certificado de 127.0.0.1:443"
    elif printf '%s' "$issuer" | grep -qi 'TRAEFIK DEFAULT CERT'; then
        bad "TLS con el certificado default: ACME no emitio"
    else
        ok "$issuer"
    fi
fi

# ------------------------------------------------------- 7. servicios internos
section "8. Servicios internos"
for svc in fastapi nextjs arq-worker postgres redis-broker redis-cache; do
    cid=$(docker ps -q -f label=com.docker.compose.service="$svc" 2>/dev/null | head -n1)
    if [ -z "$cid" ]; then
        bad "$svc no esta corriendo"
        continue
    fi
    case "$svc" in
        fastapi)
            docker exec "$cid" curl -fsS --max-time 4 http://127.0.0.1:8000/health >/dev/null 2>&1 \
                && ok "fastapi /health" || bad "fastapi /health fallo"
            docker exec "$cid" curl -fsS --max-time 4 http://127.0.0.1:8000/ready >/dev/null 2>&1 \
                && ok "fastapi /ready (DB + Redis)" || bad "fastapi /ready fallo (DB/roles/migraciones)"
            ;;
        nextjs)
            docker exec "$cid" wget -q -O /dev/null http://127.0.0.1:3000/ 2>/dev/null \
                && ok "nextjs responde" || bad "nextjs no responde en :3000"
            ;;
        arq-worker)
            docker exec "$cid" arq app.worker.WorkerSettings --check >/dev/null 2>&1 \
                && ok "arq-worker health" || warn "arq-worker health fallo"
            ;;
        postgres)
            docker exec "$cid" pg_isready -U "$(read_env POSTGRES_SUPERUSER)" -d "$(read_env POSTGRES_DB)" >/dev/null 2>&1 \
                && ok "postgres acepta conexiones" || bad "postgres no acepta conexiones"
            ;;
        redis-broker | redis-cache)
            docker exec "$cid" redis-cli ping 2>/dev/null | grep -q PONG \
                && ok "$svc responde PONG" || bad "$svc no responde"
            ;;
    esac
done

# ------------------------------------------------------------------ 8. ACME
if [ -n "$traefik" ]; then
    section "9. ACME"
    acme=$(docker inspect "$traefik" --format '{{range .Mounts}}{{if eq .Destination "/acme"}}{{.Name}}{{end}}{{end}}' 2>/dev/null || true)
    if [ -z "$acme" ]; then
        warn "traefik no monta /acme"
    else
        docker run --rm -i -v "$acme":/a:ro alpine:3.22 sh -s <<'SH' 2>/dev/null | sed 's/^/    /'
ls -l /a 2>/dev/null
echo "-- certificados --"
grep -o '"main":"[^"]*"' /a/acme.json 2>/dev/null | cut -d'"' -f4 | sort -u
SH
    fi
    echostr=$("${DC[@]}" logs --since=15m --tail=400 traefik 2>&1 | grep -iE 'acme|certificate|dns01|unable to obtain|rateLimit|no domain' | tail -n 12)
    if [ -n "$echostr" ]; then printf '%s\n' "$echostr" | sed 's/^/    /'; fi
fi

# ------------------------------------------------------------------ 9. logs
section "10. Errores recientes"
for svc in fastapi nextjs migrate; do
    lines=$("${DC[@]}" logs --since=15m --tail=200 "$svc" 2>&1 | grep -iE 'error|fatal|panic|traceback|refused|denied' | tail -n 8)
    if [ -n "$lines" ]; then
        info "-- $svc --"
        printf '%s\n' "$lines" | sed 's/^/    /'
    fi
done

# ---------------------------------------------------------------- resumen
section "Resumen"
printf '  fallos: %d · advertencias: %d\n' "$FAIL" "$WARN"
if [ "$FAIL" -eq 0 ]; then
    printf '  Sin fallos detectados en las capas revisadas.\n'
else
    printf '  Empezá por el PRIMER ✗ de arriba: las capas dependen en orden.\n'
    printf '  Si el stack no está levantado, corré primero:\n'
    printf '    make prod-check && make prod-up 2>&1 | tee /tmp/prod-up.log\n'
fi
printf '  Pasá este informe completo (sin tokens) para seguir.\n'
