import argparse
import asyncio
import logging
import os
from pathlib import Path

from funasr import AutoModel
from wyoming.asr import Transcribe, Transcript
from wyoming.server import AsyncServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_model() -> AutoModel:
    model_name = os.environ.get("SENSEVOICE_MODEL_NAME", "iic/SenseVoiceSmall")
    models_dir = Path(os.environ.get("SENSEVOICE_MODELS_DIR", "/models"))
    modelscope_cache = Path(
        os.environ.setdefault("MODELSCOPE_CACHE", str(models_dir / "modelscope"))
    )
    modelscope_cache.mkdir(parents=True, exist_ok=True)
    device = os.environ.get("SENSEVOICE_DEVICE", "cpu")

    logger.info("Loading model '%s' on device '%s' (cache: %s)", model_name, device, modelscope_cache)
    m = AutoModel(model=model_name, device=device)
    logger.info("Model loaded successfully")
    return m


model = load_model()


class SenseVoiceEventHandler:
    async def handle_event(self, event):
        if isinstance(event, Transcribe):
            try:
                res = model.generate(input=event.audio)
                text = res[0]["text"]
                logger.debug("Transcribed: %s", text)
                return Transcript(text=text)
            except Exception:
                logger.exception("Transcription failed")
                return Transcript(text="")
        return None


async def main():
    parser = argparse.ArgumentParser(description="Wyoming SenseVoice ASR server")
    parser.add_argument("--uri", required=True, help="unix:// or tcp://")
    args = parser.parse_args()

    logger.info("Starting Wyoming server on %s", args.uri)
    server = AsyncServer.from_uri(args.uri)
    await server.run(lambda: SenseVoiceEventHandler())


if __name__ == "__main__":
    asyncio.run(main())
