# Formata.AI Web — API + landing page num único contêiner.
# Construir:  docker build -t formata-ai .
# Executar:   docker run --rm -p 8000:8000 --env-file .env formata-ai
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FORMATA_HOST=0.0.0.0 \
    FORMATA_PORTA=8000 \
    FORMATA_FRONTEND_DIR=/app/frontend

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/formata backend/formata
COPY backend/servidor backend/servidor
COPY frontend frontend

# Usuário sem privilégios; o sistema de arquivos não precisa ser gravável.
RUN useradd --system --uid 10001 formata
USER formata
WORKDIR /app/backend

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/saude', timeout=2)"

CMD ["python", "-m", "servidor"]
