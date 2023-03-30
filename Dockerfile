FROM python:3.11-alpine as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app

FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.4.1

RUN apk add --no-cache gcc libffi-dev musl-dev
RUN pip install "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock ./

ARG LOCAL_ENVIRONMENT=false
RUN poetry export -f requirements.txt --output requirements.txt $("${LOCAL_ENVIRONMENT}" == true && echo "--with dev")
FROM base as final

COPY --from=builder /app/requirements.txt ./
RUN pip install -r ./requirements.txt

COPY src ./src
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5000"]