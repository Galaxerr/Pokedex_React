FROM python:3.12-slim

WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv==0.11.15 && uv sync --locked --no-dev
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic


EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

