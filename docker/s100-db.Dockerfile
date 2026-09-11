FROM postgis/postgis:16-3.4

# Keep the vector extension in the image so container recreation does not lose it.
RUN apt-get update \
    -o Acquire::Check-Valid-Until=false \
    -o Acquire::Check-Date=false \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
