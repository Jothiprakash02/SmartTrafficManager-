FROM python:3.13-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[mqtt]"

CMD ["sh", "-c", "python -m traffic_edge.cli --forever --scenario ${SCENARIO:-live} --mqtt --broker mosquitto --interval ${INTERVAL:-1}"]