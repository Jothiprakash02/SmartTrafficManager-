FROM python:3.13-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY web ./web
RUN pip install --no-cache-dir ".[mqtt]"

CMD ["python", "-m", "traffic_edge.web_server"]