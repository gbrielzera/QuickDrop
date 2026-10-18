#!/usr/bin/env bash
# Atualiza as imagens base do QuickDrop (Python e Caddy) sem mexer no código do projeto.
# Roda toda semana no servidor (veja "Manutenção de segurança" em docs/DEPLOY.md). Mudanças no código
# continuam sendo publicadas à mão, com git pull, depois de testadas.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== $(date -Iseconds) Atualizando imagens"
docker compose pull caddy
docker compose build --pull app
docker compose up -d
docker image prune -f

# Espera o app ficar saudável; se não ficar, o registro mostra o problema na manhã seguinte.
for _ in $(seq 1 30); do
  if [ "$(docker compose ps app --format '{{.Health}}')" = "healthy" ]; then
    echo "== Atualização concluída: app saudável"
    exit 0
  fi
  sleep 2
done
echo "== ATENÇÃO: o app não ficou saudável depois da atualização" >&2
docker compose logs app --tail 30 >&2
exit 1
