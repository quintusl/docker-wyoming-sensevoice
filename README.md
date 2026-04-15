# Wyoming Sherpa-ONNX SenseVoice (Cantonese STT)

An all-in-one Docker image for Cantonese Speech-to-Text (STT) using [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx) and the [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) model, specifically optimized for Home Assistant's [Wyoming protocol](https://github.com/rhasspy/wyoming).

## Features

- **All-in-One**: Contains the Wyoming server, Sherpa-ONNX engine, and model downloader.
- **Cantonese Optimized**: Uses the `csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09` model, fine-tuned on 21.8k hours of Cantonese data.
- **Automatic Setup**: Downloads the ~700MB model from Hugging Face on the first run.
- **Clean Output**: Automatically strips SenseVoice language/emotion tags (e.g., `<|yue|>`, `<|HAPPY|>`) for better Home Assistant Assist compatibility.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed.
- (Optional) A directory to persist the downloaded model.

## Build Instructions

To build the image locally, run the following command in the project directory:

```bash
docker build -t wyoming-sherpa-sensevoice .
```

## Run Instructions

### 1. Basic Run
Run the container and expose port `10300`:

```bash
docker run -d \
  --name wyoming-stt-cantonese \
  -p 10300:10300 \
  wyoming-sherpa-sensevoice
```

### 2. Recommended Run (With Persistent Model Storage)
Mount a local directory to `/app/model` to avoid re-downloading the 700MB model every time you recreate the container:

```bash
docker run -d \
  --name wyoming-stt-cantonese \
  -p 10300:10300 \
  -v $(pwd)/model:/app/model \
  -e NUM_THREADS=4 \
  wyoming-sherpa-sensevoice
```

## Configuration

The following environment variables can be adjusted:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MODEL_REPO` | `csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09` | The Hugging Face repo ID to download from. |
| `NUM_THREADS` | `4` | Number of CPU threads used for inference. |

## Home Assistant Integration

1.  In Home Assistant, go to **Settings** > **Devices & Services**.
2.  Click **Add Integration** and search for **Wyoming**.
3.  Enter the **IP address** of your Docker host and port **`10300`**.
4.  Once added, go to **Settings** > **Voice Assistants**.
5.  Edit your **Assist Pipeline** and select this server as your **Speech-to-Text** engine.

## Acknowledgements

- [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx) by k2-fsa.
- [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) by FunAudioLLM.
- [Wyoming Protocol](https://github.com/rhasspy/wyoming) by Nabu Casa/Rhasspy.
