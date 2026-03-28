#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_DIR}"

if [[ ! -d ".venv" ]]; then
  echo "ERRO: ambiente virtual .venv nao encontrado em ${PROJECT_DIR}"
  echo "Crie o venv antes: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

source ".venv/bin/activate"

mkdir -p ".cache"
export XDG_CACHE_HOME="${PROJECT_DIR}/.cache"
export PADDLE_HOME="${PROJECT_DIR}/.cache"
export PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

python - <<'PY'
import requests

from camera import Camera
from vehicle.infrastructure.recognition_http_gateway import RecognitionHttpGateway
from vehicle.settings import settings

camera = Camera()
try:
    camera.start()
    frame = camera.capture()
finally:
    camera.stop()

health_url = f"{settings.recognition_service_base_url.rstrip('/')}/health"
try:
    response = requests.get(health_url, timeout=settings.recognition_request_timeout_seconds)
    response.raise_for_status()
except requests.RequestException as error:
    raise SystemExit(f"ERRO: reconhecimento remoto indisponivel em {health_url}: {error}")

gateway = RecognitionHttpGateway()
frame_presence = gateway.detect_frame_presence(frame.image)
spot_result = gateway.detect_spot("SMOKE", frame.image)

print(
    f"SMOKE_OK frame={frame.width}x{frame.height} "
    f"veiculo_detectado={frame_presence.vehicle_detected} "
    f"placa={spot_result.plate} confianca={spot_result.confidence}"
)
PY

echo "RESULTADO: APTO (camera no Pi + recognition remoto via HTTP)"
