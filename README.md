# wyoming-sensevoice

A [Wyoming protocol](https://github.com/rhasspy/wyoming) server that transcribes speech using [FunASR SenseVoice](https://github.com/FunAudioLLM/SenseVoice). Compatible with [Home Assistant](https://www.home-assistant.io/) and other Wyoming-based voice pipelines.

## Quick start

### 1. Download the model

Pull the image (or build it locally) and run the one-shot download service to populate `./models`:

```bash
docker compose run --rm download
```

This downloads the default model (`iic/SenseVoiceSmall`) into `./models/modelscope/` on your host. It only needs to run once.

To download a different model, set the environment variable before running:

```bash
SENSEVOICE_MODEL_NAME=iic/SenseVoiceLarge docker compose run --rm download
```

### 2. Start the server

```bash
docker compose up -d
```

The server listens on port **10300**. The `./models` directory is bind-mounted into the container so the downloaded model is used directly — no re-download needed.

---

## Manual Docker usage (without Compose)

### Build

```bash
docker build -t wyoming-sensevoice .
```

### Download the model

```bash
mkdir -p models
docker run --rm \
  -v "$(pwd)/models:/models" \
  -e SENSEVOICE_MODEL_NAME=iic/SenseVoiceSmall \
  --entrypoint python3 \
  wyoming-sensevoice \
  -c "
import os;
from modelscope import snapshot_download;
snapshot_download(os.environ['SENSEVOICE_MODEL_NAME'], cache_dir='/models/modelscope')
"
```

### Run the server

```bash
docker run -d \
  --name wyoming-sensevoice \
  -p 10300:10300 \
  -v "$(pwd)/models:/models" \
  wyoming-sensevoice
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `SENSEVOICE_MODEL_NAME` | `iic/SenseVoiceSmall` | FunASR/ModelScope model identifier |
| `SENSEVOICE_MODELS_DIR` | `/models` | Base directory for model files inside the container |
| `MODELSCOPE_CACHE` | `/models/modelscope` | ModelScope download cache directory |
| `SENSEVOICE_DEVICE` | `cpu` | Inference device — `cpu` or `cuda` |

---

## GPU support

Set `SENSEVOICE_DEVICE=cuda` and pass `--gpus all` to `docker run`, or add the following to `docker-compose.yml`:

```yaml
    environment:
      SENSEVOICE_DEVICE: cuda
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## CI/CD — publishing to Docker Hub

The included workflow (`.github/workflows/docker-publish.yml`) builds and pushes multi-platform images (`linux/amd64`, `linux/arm64`) automatically.

**Required repository secrets** (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | A Docker Hub [access token](https://hub.docker.com/settings/security) |

**Tagging strategy:**

| Event | Tags produced |
|---|---|
| Push to `main` | `latest`, `main` |
| Push tag `v1.2.3` | `1.2.3`, `1.2`, `1`, `latest` |
| Pull request | Image is built but **not** pushed |

---

## Connecting to Home Assistant

In Home Assistant → **Settings → Voice Assistants → Add Assistant**, choose **Wyoming Protocol** and enter the container host and port **10300**.
