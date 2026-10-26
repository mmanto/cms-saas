#!/usr/bin/env bash
# Preflight de PRODUCCION.
#
# Detecta, ANTES de construir/levantar, las dos causas tipicas de
# "no hay certificado" + "404":
#
#   * SAAS_BASE_DOMAIN sigue en *.localhost (el borde solo rutea ese Host, asi
#     que cualquier dominio/IP real responde el 404 de Traefik y LetsEncrypt no
#     puede emitir nada para .localhost);
#   * el resolver ACME no tiene credenciales del provider DNS (el desafio
#     DNS-01 falla y Traefik sirve su certificado self-signed).
#
# Uso:
#   ./scripts/preflight-prod.sh            # falla si hay errores
#   SKIP_PROD_CHECK=1 make prod-up         # saltear el chequeo
#   ENV_FILE=otro.env ./scripts/preflight-prod.sh
set -uo pipefail

cd "$(dirname "$0")/.."
ENV_FILE=${ENV_FILE:-.env}

if [ "${SKIP_PROD_CHECK:-0}" = "1" ]; then
    echo "Preflight salteado (SKIP_PROD_CHECK=1)."
    exit 0
fi

errors=0
warnings=0

ok() { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; warnings=$((warnings + 1)); }
fail() { printf '  \033[31m✗\033[0m %s\n' "$*"; errors=$((errors + 1)); }

# Valor de una variable: el entorno del shell gana sobre el archivo, igual que
# docker compose. No se hace `source`: el .env no tiene que ejecutarse.
read_env() {
    local key=$1
    if [ -n "${!key+x}" ]; then
        printf '%s' "${!key}"
        return 0
    fi
    [ -f "$ENV_FILE" ] || return 0
    sed -n "s/^[[:space:]]*${key}=//p" "$ENV_FILE" | tail -n 1
}

have() { [ -n "$(read_env "$1")" ]; }

echo "Preflight de produccion ($ENV_FILE)"
echo

if [ ! -f "$ENV_FILE" ]; then
    fail "no existe $ENV_FILE. En el servidor: cp .env.example .env"
    echo
    echo "Sin .env no hay dominio base, ni secretos, ni credenciales de ACME."
    exit 1
fi

# --- Dominio base ---------------------------------------------------------
base=$(read_env SAAS_BASE_DOMAIN | tr '[:upper:]' '[:lower:]')
base=${base#http://}
base=${base#https://}
base=${base%%/*}
base=${base%%:*}

case "$base" in
    "")
        fail "SAAS_BASE_DOMAIN esta vacio: el borde no genera ningun router."
        ;;
    *.localhost | *.local | localhost | *.test | *.invalid | *.example)
        fail "SAAS_BASE_DOMAIN=$base no sirve en produccion."
        echo "      Traefik solo rutea Host(\`$base\`), \`admin.$base\` y \`*.$base\`:
      cualquier dominio real o la IP del servidor responde 404."
        echo "      Ademas LetsEncrypt no emite certificados para esa TLD."
        echo "      Poné el dominio real (ej. SAAS_BASE_DOMAIN=cms-saas.pro)."
        ;;
    *[[:space:]]*)
        fail "SAAS_BASE_DOMAIN tiene espacios: '$base'."
        ;;
    *)
        if printf '%s' "$base" | grep -Eq '^[0-9]+(\.[0-9]+){3}$'; then
            fail "SAAS_BASE_DOMAIN=$base es una IP: el ruteo es por Host, no por IP."
        elif ! printf '%s' "$base" | grep -Eq '^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$'; then
            fail "SAAS_BASE_DOMAIN=$base no es un dominio valido."
        else
            ok "dominio base: $base"
        fi
        ;;
esac

# --- ACME -----------------------------------------------------------------
email=$(read_env ACME_EMAIL)
if printf '%s' "$email" | grep -Eq '^[^@[:space:]]+@[^@[:space:]]+\.[a-z]{2,}$'; then
    ok "ACME_EMAIL: $email"
else
    fail "ACME_EMAIL='$email' no es un email valido (LetsEncrypt lo pide)."
fi

provider=$(read_env ACME_DNS_PROVIDER | tr '[:upper:]' '[:lower:]')
if [ -z "$provider" ]; then
    fail "ACME_DNS_PROVIDER vacio: sin DNS-01 no se puede emitir el wildcard *.$base."
else
    ok "provider DNS-01: $provider"
fi

case "$provider" in
    cloudflare)
        if have CF_DNS_API_TOKEN; then
            ok "CF_DNS_API_TOKEN definido"
        elif have CF_DNS_API_EMAIL && have CF_DNS_API_KEY; then
            ok "CF_DNS_API_EMAIL + CF_DNS_API_KEY definidos"
        else
            fail "Cloudflare sin credenciales: CF_DNS_API_TOKEN (recomendado) o CF_DNS_API_EMAIL+CF_DNS_API_KEY."
            echo "      Token con permiso Zone:DNS:Edit sobre la zona $base (y *.$base)."
        fi
        ;;
    route53)
        if have AWS_ACCESS_KEY_ID && have AWS_SECRET_ACCESS_KEY; then
            ok "AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY definidos"
            have AWS_REGION || warn "AWS_REGION vacio (lego puede inferirlo de la zona)."
        else
            fail "Route53 sin AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY."
        fi
        ;;
    gandiv5)
        have GANDIV5_API_KEY && ok "GANDIV5_API_KEY definido" || fail "GANDIV5_API_KEY vacio."
        ;;
    hetzner)
        have HETZNER_API_KEY && ok "HETZNER_API_KEY definido" || fail "HETZNER_API_KEY vacio."
        ;;
    "")
        ;;
    *)
        warn "provider '$provider': este preflight no conoce sus variables; verificá que el contenedor traefik las reciba."
        ;;
esac

# --- DNS ------------------------------------------------------------------
# Sin registros no hay validacion DNS-01 (ni navegador que llegue al borde).
# `cert-probe.$base` prueba el wildcard DNS; el apex prueba el dominio base.
if [ -n "$base" ] && command -v getent >/dev/null 2>&1; then
    if getent ahosts "$base" >/dev/null 2>&1; then
        ips=$(getent ahosts "$base" | awk '$2=="STREAM"{print $1}' | sort -u | tr '\n' ' ')
        ok "DNS $base -> ${ips:-?}"
        if printf '%s' "$ips" | grep -Eq '(^| )(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|0\.0\.0\.0|::1)'; then
            warn "$base resuelve a una IP privada/loopback: LetsEncrypt no va a poder validar."
        fi
    else
        fail "DNS $base no resuelve: el certificado no se emite y el navegador no llega al borde."
    fi

    probe="cert-probe.$base"
    if getent ahosts "$probe" >/dev/null 2>&1; then
        ok "DNS wildcard *.$base resuelve ($probe)"
    else
        fail "no hay wildcard DNS *.$base (probé $probe)."
        echo "      Sin ese registro el subdominio de cada club y admin.$base no resuelven."
    fi
else
    warn "sin getent: no pude verificar DNS."
fi

# --- Restos de configuracion de desarrollo --------------------------------
if [ -n "$base" ] && ! printf '%s' "$base" | grep -q '\.localhost$'; then
    for key in PLATFORM_ADMIN_EMAIL FIRST_TENANT_ADMIN_EMAIL; do
        value=$(read_env "$key")
        case "$value" in
            *@*.localhost | *@localhost)
                warn "$key=$value sigue apuntando a desarrollo (el dominio base es $base)."
                ;;
        esac
    done
fi

echo
if [ "$errors" -gt 0 ]; then
    printf '\033[31m✗ %d error(es)\033[0m: no se levanta produccion.\n' "$errors"
    echo "  Corregí $ENV_FILE y volvé a correr 'make prod-up'."
    echo "  Para saltear este chequeo: SKIP_PROD_CHECK=1 make prod-up"
    exit 1
fi

if [ "$warnings" -gt 0 ]; then
    printf '\033[33m! %d advertencia(s)\033[0m: revisá lo marcado arriba.\n' "$warnings"
fi
printf '\033[32m✓ Preflight OK\033[0m\n'
