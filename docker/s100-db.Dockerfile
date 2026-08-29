FROM postgis/postgis:17-3.5

# Keep the vector extension in the image so container recreation does not lose it.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends postgresql-17-pgvector \
    && rm -rf /var/lib/apt/lists/*
