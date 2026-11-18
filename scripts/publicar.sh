#!/usr/bin/env bash
# Constrói as 3 imagens do PontoZero e envia para o Docker Hub (Linux/Mac/WSL).
#   docker login                      (uma vez)
#   ./scripts/publicar.sh [usuario] [tag]
set -euo pipefail
cd "$(dirname "$0")/.."
USUARIO="$(echo "${1:-ogabrieltenorio}" | tr '[:upper:]' '[:lower:]')"
TAG="${2:-1.0}"
PLATAFORMAS="${PLATAFORMAS:-linux/amd64,linux/arm64}"

docker buildx inspect pontozero >/dev/null 2>&1 || docker buildx create --name pontozero --driver docker-container >/dev/null
docker buildx use pontozero

for img in db api web; do
  echo "-> pontozero-$img ($PLATAFORMAS)"
  docker buildx build --platform "$PLATAFORMAS" \
    -t "$USUARIO/pontozero-$img:$TAG" -t "$USUARIO/pontozero-$img:latest" \
    --push "./$img"
done
echo "Pronto. Teste com: docker compose up -d"
