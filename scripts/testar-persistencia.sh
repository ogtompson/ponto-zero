#!/usr/bin/env bash
# Desliga e religa o compose algumas vezes e confere se os dados continuam (Linux/Mac/WSL).
#   ./scripts/testar-persistencia.sh [ciclos]
set -euo pipefail
cd "$(dirname "$0")/.."
CICLOS="${1:-3}"
API="http://localhost:${WEB_PORTA:-8080}/api"
JAR="$(mktemp)"
EMAIL="teste-$RANDOM$RANDOM@pontozero.app"
SENHA="persistencia123"
campo() { grep -o "\"$1\":\"[^\"]*\"" | head -1 | cut -d'"' -f4; }

docker compose up -d --wait
echo "[ok] containers saudáveis"
curl -sf -c "$JAR" -H 'Content-Type: application/json' \
  -d "{\"nome\":\"Teste\",\"email\":\"$EMAIL\",\"senha\":\"$SENHA\",\"empresa\":\"Teste\",\"segmento\":\"Padaria\"}" \
  "$API/auth/cadastro" >/dev/null
IDS="$(curl -sf "$API/regioes" | grep -o '"id_regiao":[0-9]*' | head -2 | cut -d: -f2 | paste -sd, -)"
SEGMENTO_ID="$(curl -sf "$API/segmentos" | grep -o '{[^{}]*"nome":"Padaria"[^{}]*}' | grep -o '"id_categoria":[0-9]*' | head -1 | cut -d: -f2)"
[ -n "$SEGMENTO_ID" ] || { echo "[falhou] segmento Padaria não encontrado"; exit 1; }
ID="$(curl -sf -b "$JAR" -H 'Content-Type: application/json' \
  -d "{\"nome\":\"Persistência\",\"segmento\":$SEGMENTO_ID,\"regioes\":[$IDS]}" "$API/analises" \
  | grep -o '"id_analise":[0-9]*' | head -1 | cut -d: -f2)"
[ -n "$ID" ] || { echo "[falhou] API não devolveu o id da análise"; exit 1; }
VOLUME="$(curl -sf "$API/status" | campo volume_inicializado_em)"
echo "[ok] conta $EMAIL e análise $ID gravadas; volume criado em $VOLUME"

for i in $(seq 1 "$CICLOS"); do
  docker compose down
  docker compose up -d --wait
  [ "$(curl -sf "$API/status" | campo volume_inicializado_em)" = "$VOLUME" ] || { echo "[falhou] volume recriado"; exit 1; }
  rm -f "$JAR"
  curl -sf -c "$JAR" -H 'Content-Type: application/json' -d "{\"email\":\"$EMAIL\",\"senha\":\"$SENHA\"}" "$API/auth/login" >/dev/null
  curl -sf -b "$JAR" "$API/analises" | grep -q "\"id_analise\":$ID" || { echo "[falhou] análise sumiu"; exit 1; }
  echo "[ok] ciclo $i: mesmo volume, login e análise preservados"
done
echo "Tudo certo: os dados persistem no volume pgdata."
