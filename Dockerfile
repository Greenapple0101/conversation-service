FROM python:3.10-slim

WORKDIR /app

# 환경 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "app:app"]