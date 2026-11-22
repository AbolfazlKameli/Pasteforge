ARG PYTHON_VERSION=3.13.15

FROM python:${PYTHON_VERSION}-alpine AS builder

COPY --from=astral/uv:0.10.0 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /usr/src/pasteforge/

COPY pyproject.toml uv.lock alembic.ini entrypoint.sh ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY pasteforge/ ./pasteforge

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

FROM python:${PYTHON_VERSION}-alpine AS runtime

RUN apk add --no-cache libpq libmagic

COPY --from=astral/uv:0.10.0 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy \
    PATH="/usr/src/pasteforge/.venv/bin:$PATH"

WORKDIR /usr/src/pasteforge/

LABEL maintainer="abolfazlkameli0@gmail.com"

COPY --from=builder /usr/src/pasteforge/ ./

RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
