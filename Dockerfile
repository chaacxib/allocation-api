FROM python:3.11-alpine as base

ARG LOCAL_ENVIRONMENT=false
ENV APP_IS_LOCAL_ENVIRONMENT=${LOCAL_ENVIRONMENT}

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app

FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.4.1

RUN pip install --no-cache-dir --upgrade "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock ./

RUN poetry export -f requirements.txt --output requirements.txt  --without-hashes \
    $("${APP_IS_LOCAL_ENVIRONMENT}" == true && echo "--with dev")

FROM base as final

COPY --from=builder /app/requirements.txt ./

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

RUN adduser -u 1002 --disabled-password --gecos "" fastapi && chown -R fastapi /app
USER fastapi

EXPOSE 5000

COPY src ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]