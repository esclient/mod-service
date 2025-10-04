FROM python:3.13-slim

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir pdm

COPY pyproject.toml pdm.lock ./
RUN pdm export --group dev --without-hashes -f requirements > /tmp/req.text \
    && pip install --no-cache-dir -r /tmp/req.text \
    && rm /tmp/req.text

COPY . .
RUN pip install --no-cache-dir -e .

CMD ["watchfiles", "run-server"]