FROM python:3.12-slim

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치 (PostgreSQL 연결 등 빌드에 필요한 라이브러리)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Poetry 및 필수 패키지 설치
RUN pip install --no-cache-dir poetry setuptools

# 의존성 파일 복사
COPY pyproject.toml poetry.lock* ./

# 가상환경 생성 없이 시스템에 직접 패키지 설치 (도커 환경 최적화)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root \
    && pip install --force-reinstall "setuptools<70" wheel

# 소스 코드 복사
COPY . .

# 포트 개방
EXPOSE 8000

# 서버 실행 (uvicorn)
CMD ["uvicorn", "services.orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000"]
