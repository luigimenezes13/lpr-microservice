#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="lpr.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"

if [[ "${EUID}" -eq 0 ]]; then
  echo "Execute este script sem sudo. Ele pedira sudo apenas quando necessario."
  exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_USER="${SUDO_USER:-$USER}"
RUN_HOME="$(getent passwd "${RUN_USER}" | cut -d: -f6)"

if [[ -z "${RUN_HOME}" ]]; then
  echo "Nao foi possivel resolver o home do usuario ${RUN_USER}."
  exit 1
fi

PYTHON_PATH="${PROJECT_DIR}/.venv/bin/python"
MAIN_PATH="${PROJECT_DIR}/main.py"

if [[ ! -x "${PYTHON_PATH}" ]]; then
  echo "Python do ambiente virtual nao encontrado em: ${PYTHON_PATH}"
  echo "Crie o ambiente antes: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

sudo tee "${SERVICE_PATH}" >/dev/null <<EOF
[Unit]
Description=LPR Parking Monitor
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PYTHON_PATH} ${MAIN_PATH}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

echo "Servico instalado e reiniciado com sucesso."
echo "Status:"
sudo systemctl status "${SERVICE_NAME}" --no-pager || true
echo
echo "Logs em tempo real:"
echo "journalctl -u ${SERVICE_NAME} -f"
