FROM python:3.12-slim

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry setuptools
COPY pyproject.toml poetry.lock* ./
ARG INSTALL_DEV=false
RUN poetry config virtualenvs.create false \
    && if [ "$INSTALL_DEV" = "true" ]; then poetry install --with dev --no-interaction --no-ansi --no-root; else poetry install --only main --no-interaction --no-ansi --no-root; fi \
    && pip install --force-reinstall "setuptools<70" wheel
COPY . .
EXPOSE 8000
CMD ["uvicorn", "services.orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000"]