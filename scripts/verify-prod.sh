#!/usr/bin/env bash
# Verificacion de PRODUCCION ya levantada.
#
# Distingue los dos fallos que se confunden en el navegador:
#   * el certificado no se emitio (Traefik sirve su default self-signed), y
#   * el Host no matchea ningun router (Traefik responde 404).
#
# Corre desde el host del stack. No usa DNS publico: pega contra 127.0.0.1 con
# --resolve, asi que el resultado no depende de la propagacion.
set -uo pipefail

cd "$(dirname "$0")/.."
ENV_FILE=${ENV_FILE:-.env}
DC=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)

errors=0

ok() { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
fail() { printf '  \033[31m✗\033[0m %s\n' "$*"; errors=$((errors + 1)); }
info() { printf '    %s\n' "$*"; }

read_env() {
    local key=$1
    if [ -n "${!key+x}" ]; then printf '%s' "${!key}"; return 0; fi
    [ -f "$ENV_FILE" ] || return 0
    sed -n "s/^[[:space:]]*${key}=//p" "$ENV_FILE" | tail -n 1
}

base=$(read_env SAAS_BASE_DOMAIN | tr '[:upper:]' '[:lower:]')
base=${base#http://}; base=${base#https://}; base=${base%%/*}; base=${base%%:*}

echo "Verificacion de produccion (${base:-SAAS_BASE_DOMAIN vacio})"
echo

if [ -z "$base" ]; then
    echo "  SAAS_BASE_DOMAIN vacio en $ENV_FILE: nada que verificar."
    exit 1
fi

if ! "${DC[@]}" ps --services --status running 2>/dev/null | grep -qx traefik; then
    fail "traefik no esta corriendo. Levantá el stack: make prod-up"
    exit 1
fi
ok "contenedor traefik corriendo"

# --- 80: redireccion al entrypoint TLS ------------------------------------
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 -H "Host: $base" http://127.0.0.1/ 2>/dev/null || true)
case "$code" in
    301 | 302 | 307 | 308) ok "http://$base -> $code (redirige a https)" ;;
    000) fail "nada escucha en 127.0.0.1:80 (¿otro proxy lo ocupa?)." ;;
    *) fail "http://$base respondio $code; se esperaba un redirect 3xx." ;;
esac

# --- 443: ruteo por Host (independiente de DNS) ---------------------------
https_code() {
    curl -sk -o /dev/null -w '%{http_code}' --max-time 10 \
        --resolve "$1:443:127.0.0.1" "https://$1$2" 2>/dev/null || true
}

code=$(https_code "$base" "/")
case "$code" in
    200 | 301 | 302 | 307 | 308) ok "https://$base/ -> $code" ;;
    404)
        fail "https://$base/ -> 404: ningun router de Traefik matchea ese Host."
        info "Revisá SAAS_BASE_DOMAIN y routes.yml (ver abajo)."
        ;;
    000) fail "https://$base/ no completo el handshake TLS." ;;
    *) fail "https://$base/ -> $code" ;;
esac

admin_code=$(https_code "admin.$base" "/admin")
case "$admin_code" in
    200 | 301 | 302 | 307 | 308) ok "https://admin.$base/admin -> $admin_code" ;;
    404) fail "https://admin.$base/admin -> 404: falta el router saas-admin-web." ;;
    *) fail "https://admin.$base/admin -> $admin_code" ;;
esac

# --- Certificado servido --------------------------------------------------
pem=$(echo | timeout 10 openssl s_client -connect 127.0.0.1:443 -servername "$base" 2>/dev/null || true)
issuer=$(printf '%s' "$pem" | openssl x509 -noout -issuer 2>/dev/null | tr -d '\r' || true)
subject=$(printf '%s' "$pem" | openssl x509 -noout -subject 2>/dev/null | tr -d '\r' || true)
sans=$(printf '%s' "$pem" | openssl x509 -noout -text 2>/dev/null | grep -A1 'Subject Alternative Name' | tr -d ' \n\r' || true)

if [ -z "$issuer" ]; then
    fail "no pude leer el certificado de 127.0.0.1:443."
elif printf '%s' "$issuer" | grep -qi 'TRAEFIK DEFAULT CERT'; then
    fail "TLS con el certificado default de Traefik: ACME no emitio."
    info "El navegador lo marca invalido; al continuar, el 404 depende del Host."
else
    ok "$issuer"
    info "$subject"
    if printf '%s' "$sans" | grep -q "DNS:$base" || printf '%s' "$sans" | grep -q 'DNS:\*\.'; then
        [ -n "$sans" ] && info "${sans#SubjectAlternativeName:}"
    fi
fi

# --- ACME store -----------------------------------------------------------
cid=$("${DC[@]}" ps -q traefik 2>/dev/null | head -n1)
acme_vol=""
if [ -n "$cid" ]; then
    acme_vol=$(docker inspect "$cid" --format '{{range .Mounts}}{{if eq .Destination "/acme"}}{{.Name}}{{end}}{{end}}' 2>/dev/null || true)
fi

if [ -n "$acme_vol" ]; then
    raw=$(docker run --rm -v "$acme_vol":/acme:ro alpine:3.22 sh -c 'cat /acme/acme.json 2>/dev/null' 2>/dev/null || true)
    if [ -z "$raw" ]; then
        fail "acme.json esta vacio o no existe en el volumen $acme_vol."
        info "No hay ningun certificado emitido todavia."
    else
        mains=$(printf '%s' "$raw" | grep -o '"main":"[^"]*"' | cut -d'"' -f4 | sort -u | tr '\n' ' ')
        if printf '%s' "$raw" | grep -q "\"main\":\"$base\""; then
            ok "acme.json tiene certificado para $base"
        else
            fail "acme.json no tiene certificado para $base (emitidos: ${mains:-ninguno})."
        fi
    fi
else
    warn "no encontre el volumen /acme montado en traefik."
fi

# --- Logs de ACME ---------------------------------------------------------
if [ "$errors" -gt 0 ]; then
    echo
    echo "Ultimos errores de Traefik/ACME:"
    "${DC[@]}" logs --tail=400 traefik 2>&1 \
        | grep -iE 'acme|certificate|error' \
        | tail -n 15 \
        | sed 's/^/    /'
    cat <<EOF

Sugerencias:
  * DNS: $base y *.$base tienen que resolver al servidor (o al proxy que llega a el).
  * Credenciales del provider DNS: necesitan editar la zona $base.
  * Si acabás de corregir credenciales o DNS:
      make prod-down && make prod-up
  * Detalle completo:
      ${DC[*]} logs --tail=300 traefik | grep -iE 'acme|error'
      make prod-check
EOF
    exit 1
fi

echo
printf '\033[32m✓ Produccion OK\033[0m\n'
