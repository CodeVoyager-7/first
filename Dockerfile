FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV HOST=0.0.0.0
ENV PORT=8000
ENV UVICORN_RELOAD=false
ENV APP_DATA_DIR=/app_data

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app_data

EXPOSE 8000

CMD ["python", "run_web_app.py"]
