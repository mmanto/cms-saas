# ============================================================================
# Backend: FastAPI + ARQ worker. Multi-stage real: el compilador y los headers
# viven solo en el builder; el venv se copia ya compilado.
# ============================================================================
ARG PYTHON_VERSION=3.14

# --- Etapa 1: builder ------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# --- Etapa 2: base de runtime --------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    TZ=America/Argentina/Buenos_Aires

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv

WORKDIR /code

# Primero el manifest de migraciones y el codigo, despues los tests: se copia
# todo porque en desarrollo el contenedor tambien corre pytest.
COPY . .
RUN chown -R appuser:appuser /code

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- Etapa 3: desarrollo --------------------------------------------------
FROM base AS development

USER root
COPY requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Etapa 4: produccion --------------------------------------------------
FROM base AS production

ENV WEB_CONCURRENCY=4

# gunicorn + uvicorn-worker: el modulo uvicorn.workers esta deprecado desde
# uvicorn 0.30 y pide migrar al paquete uvicorn-worker.
CMD ["sh", "-c", "exec gunicorn app.main:app -k uvicorn_worker.UvicornWorker -w ${WEB_CONCURRENCY} --bind 0.0.0.0:8000 --access-logfile - --error-logfile - --timeout 120 --graceful-timeout 30 --keep-alive 5"]
