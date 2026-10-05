FROM python:3.13-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[opcua,mqtt]"

CMD ["python", "-m", "traffic_edge.opcua_service"]
