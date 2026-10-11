FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic ./alembic
COPY src ./src
COPY scripts ./scripts
COPY alembic.ini .
COPY main.py .

CMD ["uvicorn", "src.misptool.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
