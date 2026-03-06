# Build context must be the repo root so both site/ and docs/build/ are accessible.
# docker build -f site/Dockerfile .

FROM python:3.12-slim as python-base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    UV_PROJECT_ENVIRONMENT="/opt/venv"

ENV PATH="$UV_PROJECT_ENVIRONMENT/bin:$PATH"

# builder-base installs runtime dependencies
FROM python-base as builder-base
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --only-group site --no-install-project

# production stage
FROM python-base as production

COPY --from=builder-base /opt/venv /opt/venv

# Copy the site directory into /app/
COPY site/ /app/

WORKDIR /app

EXPOSE 80

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update --fix-missing && \
    apt-get install --no-install-recommends -y curl && \
    ENVIRONMENT=live SECRET_KEY=dummy python manage.py collectstatic --no-input && \
    ENVIRONMENT=live SECRET_KEY=dummy python manage.py compress

HEALTHCHECK --interval=1m --timeout=10s --start-period=5s --retries=3 \
  CMD curl -fs http://localhost:80/ > /dev/null || exit 1

CMD ["gunicorn", "project.wsgi", "--config=gunicorn.conf.py"]
