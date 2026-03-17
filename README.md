# LPR — Parking Spot Monitor

Sistema embarcado de visão computacional que monitora vagas de estacionamento em tempo real. Detecta veículos com YOLOv8, reconhece placas com PaddleOCR e notifica uma API central — tudo rodando localmente no Raspberry Pi.

## O que este projeto faz

- Captura imagens periódicas da câmera
- Detecta presença de veículos em cada vaga (carro, moto, ônibus, caminhão)
- Reconhece placas no padrão brasileiro (7 caracteres)
- Envia eventos de entrada e saída para uma API REST

## Hardware necessário

| Componente | Especificação |
|---|---|
| Raspberry Pi 4 | 4 GB de RAM (mínimo) |
| Câmera | Raspberry Pi Camera Module 3 Wide (IMX708) |
| Cartão SD | 32 GB+ (classe 10 ou superior) |
| Fonte | USB-C, 5V / 3A |

## Passo a passo de montagem e configuração

### 1. Gravar o sistema operacional no cartão SD

1. No seu computador, baixe e instale o [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insira o cartão SD no computador
3. No Imager, selecione:
   - **Dispositivo**: Raspberry Pi 4
   - **Sistema Operacional**: **Raspberry Pi OS (64-bit)** — obrigatório para YOLOv8 e PaddlePaddle
   - **Armazenamento**: seu cartão SD
4. Clique no ícone de engrenagem e configure:
   - **Hostname**: `lpr.local`
   - **Ativar SSH**: marque e defina uma senha
   - **Wi-Fi**: SSID e senha da sua rede
   - **Usuário e senha**: defina suas credenciais
   - **Locale**: fuso horário e layout do teclado
5. Grave a imagem

### 2. Montar o hardware

> Realize todas as conexões com o Raspberry Pi **desligado e desconectado da fonte**.

1. Insira o cartão SD no slot do Raspberry Pi 4
2. Conecte a câmera via cabo flat na porta **CAMERA** (entre a porta HDMI e o conector de áudio):
   - Levante a trava plástica do conector
   - Insira o cabo com os contatos metálicos voltados para a porta HDMI
   - Pressione a trava de volta para prender o cabo
3. Conecte a fonte USB-C

### 3. Primeiro boot e atualização do sistema

1. Aguarde o boot inicial (1-2 minutos na primeira vez)
2. Acesse via SSH:

```bash
ssh seu-usuario@lpr.local
```

3. Atualize o sistema:

```bash
sudo apt update && sudo apt full-upgrade -y
```

4. Instale e configure o swap (necessário para compilar PaddlePaddle com 4 GB de RAM):

```bash
sudo apt install -y dphys-swapfile
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

5. Reinicie:

```bash
sudo reboot
```

### 4. Testar a câmera

Reconecte via SSH e execute:

```bash
sudo apt install -y libcamera-apps
rpicam-hello --timeout 5000
```

Se não houver erro, a câmera está funcionando. Capture uma imagem de teste:

```bash
rpicam-still -o teste.jpg
```

Para conferir o sensor detectado e as resoluções disponíveis:

```bash
rpicam-hello --list-cameras
```

O Camera Module 3 Wide (IMX708) suporta resolução máxima de **4608x2592**.

> Em imagens mais novas (Bookworm/Trixie), os comandos corretos são `rpicam-*`.
> Em imagens antigas, você pode encontrar os comandos legados `libcamera-*`.

### 5. Instalar dependências

```bash
sudo apt install -y python3-pip python3-venv python3-picamera2 \
    rpicam-apps dphys-swapfile libcamera-dev \
    libopenblas-dev libjpeg-dev zlib1g-dev
```

> No Debian Trixie, `libatlas-base-dev` pode não estar disponível.
> Para este projeto, `libopenblas-dev` já atende as dependências BLAS.

### 6. Clonar o projeto e criar o ambiente virtual

Copie o projeto para o Raspberry Pi (a partir do seu computador):

```bash
scp -r ./lpr seu-usuario@lpr.local:~/lpr
```

No Raspberry Pi, crie o ambiente virtual:

```bash
cd ~/lpr
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

O flag `--system-site-packages` garante acesso ao `picamera2` instalado via apt.
Se o `pip install -r requirements.txt` falhar por causa de `picamera2`, remova `picamera2`
do `requirements.txt` (no Raspberry Pi, use preferencialmente o pacote via `apt`).

### 7. Calibrar as vagas

1. Posicione a câmera no local definitivo
2. Capture uma imagem de referência:

```bash
source .venv/bin/activate
rpicam-still -o referencia.jpg --width 4608 --height 2592
```

3. Copie para o seu computador e abra num editor de imagens:

```bash
# No seu computador
scp seu-usuario@lpr.local:~/lpr/referencia.jpg .
```

4. Identifique as coordenadas **(x, y, largura, altura)** de cada vaga na imagem
5. Defina as regiões via variáveis de ambiente (JSON) ou diretamente em `config.py`.
   Exemplo com variáveis de ambiente:

```bash
export LPR_SPOT_A='{"x":0,"y":0,"width":2304,"height":2592}'
export LPR_SPOT_B='{"x":2304,"y":0,"width":2304,"height":2592}'
```

### 8. Executar

```bash
cd ~/lpr
source .venv/bin/activate
python main.py
```

Você verá nos logs:
- `Camera iniciada`
- `Monitor iniciado — 2 vagas configuradas`
- Detecções a cada intervalo configurado

### 9. (Opcional) Rodar como serviço no boot

Crie um serviço systemd para iniciar automaticamente:

```bash
sudo tee /etc/systemd/system/lpr.service << 'EOF'
[Unit]
Description=LPR Parking Monitor
Wants=network-online.target
After=network-online.target

[Service]
User=seu-usuario
WorkingDirectory=/home/seu-usuario/lpr
ExecStart=/home/seu-usuario/lpr/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable lpr.service
sudo systemctl start lpr.service
```

Para acompanhar os logs em tempo real:

```bash
journalctl -u lpr.service -f
```

## Configuração

Todas as configurações são feitas via variáveis de ambiente com o prefixo `LPR_`:

| Variável | Default | Descrição |
|---|---|---|
| `LPR_CAPTURE_INTERVAL_SECONDS` | `5` | Intervalo entre capturas (segundos) |
| `LPR_API_BASE_URL` | `http://localhost:8000` | URL da API que recebe os eventos |
| `LPR_VEHICLE_CONFIDENCE_THRESHOLD` | `0.5` | Confiança mínima para detectar veículo |
| `LPR_PLATE_CONFIDENCE_THRESHOLD` | `0.6` | Confiança mínima para leitura de placa |
| `LPR_CAMERA_RESOLUTION_WIDTH` | `4056` | Largura da captura |
| `LPR_CAMERA_RESOLUTION_HEIGHT` | `3040` | Altura da captura |
| `LPR_RECOGNITION_HEARTBEAT_ENABLED` | `true` | Habilita log de heartbeat de reconhecimento por vaga em cada ciclo |
| `LPR_RECOGNITION_LOG_LEVEL` | `INFO` | Nível do logger `lpr.recognition` (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

Para o Camera Module 3 Wide, ajuste a resolução:

```bash
export LPR_CAMERA_RESOLUTION_WIDTH=4608
export LPR_CAMERA_RESOLUTION_HEIGHT=2592
```

### Consultar eventos de reconhecimento no journald

Com o serviço rodando via `systemd`, os heartbeats de reconhecimento ficam no `journald`.

```bash
# Fluxo completo do serviço
journalctl -u lpr.service -f

# Somente eventos de reconhecimento
journalctl -u lpr.service -f | rg "lpr.recognition"
```

## Eventos enviados

O serviço envia `POST` para `{LPR_API_BASE_URL}/events` com os seguintes payloads:

### Veículo estacionou (placa reconhecida)

```json
{
  "event": "vehicle_parked",
  "spot_id": "A",
  "plate": "ABC1D23",
  "confidence": 0.87,
  "timestamp": "2026-02-22T14:30:00"
}
```

### Veículo estacionou (placa não reconhecida)

```json
{
  "event": "vehicle_parked",
  "spot_id": "A",
  "plate": null,
  "confidence": 0.0,
  "timestamp": "2026-02-22T14:30:00"
}
```

### Veículo saiu

```json
{
  "event": "vehicle_departed",
  "spot_id": "B",
  "timestamp": "2026-02-22T15:00:00"
}
```

## Arquitetura

```
main.py            → Ponto de entrada
monitor.py         → Loop principal, coordena captura e detecção por vaga
camera.py          → Abstração sobre picamera2
detector.py        → YOLOv8 (veículos) + PaddleOCR (placas)
notifier.py        → Envio de eventos HTTP para a API
config.py          → Variáveis de ambiente via pydantic-settings
```
