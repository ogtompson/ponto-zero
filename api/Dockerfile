# =====================================================================
# Imagem 2 de 3: API do PontoZero (Python 3.12 + FastAPI)
#
# Build em duas etapas: a primeira instala as dependências num ambiente
# virtual; a segunda copia só o ambiente pronto e o código. A imagem final
# fica menor e roda com um usuário sem privilégios de root.
# =====================================================================
FROM python:3.12-slim AS dependencias
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.12-slim
LABEL org.opencontainers.image.title="pontozero-api" \
      org.opencontainers.image.description="API do PontoZero (FastAPI)" \
      org.opencontainers.image.vendor="Equipe PontoZero"

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/Recife

RUN useradd --create-home --uid 10001 pontozero
COPY --from=dependencias /opt/venv /opt/venv
WORKDIR /app
COPY app ./app
USER pontozero

EXPOSE 8000

# python já existe na imagem, então o teste de saúde não precisa de curl
HEALTHCHECK --interval=10s --timeout=4s --start-period=15s --retries=6 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
