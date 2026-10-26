# Makefile del stack cms-sas (generado por generate_infra.py).
# `make` (o `make help`) lista los comandos y muestra las URLs de acceso local.

.DEFAULT_GOAL := help

# Accesos en desarrollo (ver .env: SAAS_BASE_DOMAIN, FIRST_TENANT_SLUG).
DEV_DOMAIN := cms-sas.localhost
DEMO_SLUG  := demo
ADMIN_URL  := http://admin.$(DEV_DOMAIN)/admin
DEMO_URL   := http://$(DEMO_SLUG).$(DEV_DOMAIN)

help:
	@echo "Uso: make <target>"
	@echo
	@echo "  up        Levanta el stack (build + up -d)"
	@echo "  down      Baja el stack (conserva los datos)"
	@echo "  reset     Baja el stack y borra los datos (down -v)"
	@echo "  logs      Sigue los logs"
	@echo "  ps        Estado de los servicios"
	@echo "  urls      Muestra las URLs de acceso local"
	@echo "  test      Corre los tests del backend"
	@echo "  prod-check   Valida el .env de produccion (dominio, DNS, credenciales ACME)"
	@echo "  prod-up      Levanta el stack en produccion (valida el .env primero)"
	@echo "  prod-verify  Certificado y ruteo del stack de produccion ya levantado"
	@echo "  prod-down    Baja el stack de produccion"
	@echo
	@echo "  Accesos (desarrollo):"
	@echo "    Admin SaaS:  $(ADMIN_URL)"
	@echo "    Tenant demo: $(DEMO_URL)"
	@echo "    Landing:     http://$(DEV_DOMAIN)"
	@echo "    API docs:    $(DEMO_URL)/api/docs"
	@echo "    Traefik:     http://localhost:8080"
	@echo "    MinIO:       http://127.0.0.1:9001"

urls:
	@echo "Admin SaaS:  $(ADMIN_URL)"
	@echo "Tenant demo: $(DEMO_URL)"
	@echo "Landing:     http://$(DEV_DOMAIN)"
	@echo "API docs:    $(DEMO_URL)/api/docs"
	@echo "Traefik:     http://localhost:8080"
	@echo "MinIO:       http://127.0.0.1:9001"

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down -v

logs:
	docker compose logs -f

ps:
	docker compose ps

test:
	docker compose run --rm fastapi pytest -q

prod-check:
	@./scripts/preflight-prod.sh

prod-up: prod-check
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
	@echo
	@echo "Levantado. El certificado se emite en los primeros minutos; verificalo con:"
	@echo "  make prod-verify"

prod-verify:
	@./scripts/verify-prod.sh

prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

.PHONY: help urls up down reset logs ps test prod-check prod-up prod-verify prod-down
