# Imagem do QuickDrop: o backend e o frontend juntos, porque o backend serve o frontend.
# A imagem é fixada pelo conteúdo (digest): uma versão trocada no Docker Hub não entra sem querer.
# O Dependabot sugere o digest novo quando sai uma atualização.
FROM python:3.14-slim@sha256:930e1abba7c4e8f96ed93e8012c35d174d7732752731bbd5e8e757d7ec6f3966

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

# --require-hashes: só instala pacotes cujo conteúdo bate com o hash registrado em requirements.lock.
COPY backend/requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

COPY backend/app ./app
COPY frontend /app/frontend

# /data guarda o banco e os arquivos enviados; o docker-compose coloca um volume aqui.
# O app roda sem privilégios de administrador.
RUN useradd --create-home --uid 1000 quickdrop \
    && mkdir /data \
    && chown quickdrop /data
USER 1000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"

# 1 processo só: as conexões em tempo real e os limites de tentativas ficam na memória dele.
# --proxy-headers: o Caddy fica na frente; sem isto todo visitante pareceria ter o IP do Caddy.
# Quem pode informar o IP real (FORWARDED_ALLOW_IPS) é definido no docker-compose: só a rede do Caddy.
# --no-access-log: os registros de acesso guardariam o IP e o código de cada sala para sempre (privacidade).
# --no-server-header: não anuncia qual servidor é este. --ws-max-size: as mensagens do WebSocket são
# minúsculas (só "ping"), então 4 KB bastam e ninguém consegue mandar 16 MB de uma vez.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", \
     "--no-access-log", "--no-server-header", "--ws-max-size", "4096"]
