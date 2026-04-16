import asyncio
import logging
import numpy as np
import sherpa_onnx
import os
import argparse
import re
from typing import Optional

import opencc

from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.server import AsyncEventHandler, AsyncServer
from wyoming.info import Describe, Info, AsrModel, AsrProgram, Attribution

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

# OpenCC converters for Traditional Chinese variants.
# Keyed by language code; values are (converter, base_language) pairs.
# base_language is the underlying SenseVoice language to use for recognition.
_OPENCC_CONVERTERS: dict[str, tuple[opencc.OpenCC, str]] = {
    "zh-tw":   (opencc.OpenCC("s2twp"), "zh"),  # Taiwan Traditional + phrase conversion
    "zh-hant": (opencc.OpenCC("s2t"),   "zh"),  # Generic Traditional Chinese
    "zh-hk":   (opencc.OpenCC("s2hk"),  "zh"),  # Hong Kong Traditional
    "yue":     (opencc.OpenCC("s2hk"),  "yue"), # Cantonese (Hong Kong)
    "yue-hk":  (opencc.OpenCC("s2hk"),  "yue"), # Cantonese (Hong Kong)
    "yue-hant":(opencc.OpenCC("s2t"),   "yue"), # Cantonese in Traditional
}

# All languages including Traditional Chinese variants
_ALL_LANGUAGES = ["zh-TW", "zh-Hant", "zh-HK", "yue-HK", "yue-Hant",
                  "zh", "zh-CN", "zh-Hans", "yue", "en", "en-US", "en-GB", "ja", "ko"]

class SherpaSenseVoiceHandler(AsyncEventHandler):
    """Handles Wyoming events for Sherpa-ONNX SenseVoice STT."""

    def __init__(self, recognizer: sherpa_onnx.OfflineRecognizer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recognizer = recognizer
        self.audio_data = bytearray()
        self.sample_rate = 16000 # Default Wyoming sample rate
        self._opencc_converter: Optional[opencc.OpenCC] = None

    async def handle_event(self, event: Event) -> bool:
        if Transcribe.is_type(event.type):
            transcribe = Transcribe.from_event(event)
            lang = (transcribe.language or "").lower()
            conv_entry = _OPENCC_CONVERTERS.get(lang)
            self._opencc_converter = conv_entry[0] if conv_entry else None
            if conv_entry:
                _LOGGER.info("Received Transcribe request (lang=%s, will convert to Traditional Chinese)", transcribe.language)
            else:
                _LOGGER.info("Received Transcribe request (lang=%s)", transcribe.language)
            
        elif AudioStart.is_type(event.type):
            _LOGGER.info("Audio stream started")
            start = AudioStart.from_event(event)
            self.sample_rate = start.rate
            self.audio_data.clear()

        elif AudioChunk.is_type(event.type):
            chunk = AudioChunk.from_event(event)
            self.audio_data.extend(chunk.audio)

        elif AudioStop.is_type(event.type):
            _LOGGER.info(f"Audio stream stopped. Processing {len(self.audio_data)} bytes...")
            
            # Convert PCM bytes to float32 numpy array normalized to [-1, 1]
            audio_np = np.frombuffer(self.audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Run inference
            try:
                stream = self.recognizer.create_stream()
                stream.accept_waveform(sample_rate=self.sample_rate, waveform=audio_np)
                self.recognizer.decode_stream(stream)
                text = stream.result.text.strip()
                
                # SenseVoice often includes language/emotion tags like <|yue|>, <|HAPPY|>, etc.
                text = re.sub(r'<\|.*?\|>', '', text).strip()

                # Convert Simplified Chinese to Traditional Chinese if requested
                if self._opencc_converter and text:
                    text = self._opencc_converter.convert(text)
                    _LOGGER.info(f"Converted to Traditional Chinese: {text}")

                _LOGGER.info(f"Transcription: {text}")
                await self.write_event(Transcript(text=text).event())
            except Exception as e:
                _LOGGER.error(f"Inference failed: {e}")
                await self.write_event(Transcript(text="").event())
            
            # Close connection after transcription
            return False

        elif Describe.is_type(event.type):
            await self.write_event(
                Info(
                    asr=[
                        AsrProgram(
                            name="sherpa-sensevoice",
                            description="Sherpa-ONNX SenseVoice STT",
                            attribution=Attribution(
                                name="Alibaba Damo Academy",
                                url="https://github.com/alibaba-damo-academy/SenseVoice",
                            ),
                            installed=True,
                            version="1.0.0",
                            models=[
                                AsrModel(
                                    name="SenseVoiceSmall",
                                    description="SenseVoiceSmall model",
                                    attribution=Attribution(
                                        name="Alibaba Damo Academy",
                                        url="https://github.com/alibaba-damo-academy/SenseVoice",
                                    ),
                                    installed=True,
                                    version="1.0.0",
                                    languages=_ALL_LANGUAGES,
                                )
                            ],
                        )
                    ],
                ).event()
            )

        return True

async def main():
    parser = argparse.ArgumentParser(description="Wyoming Sherpa-ONNX SenseVoice Server")
    parser.add_argument("--model", required=True, help="Path to the SenseVoice ONNX model file")
    parser.add_argument("--tokens", required=True, help="Path to the tokens.txt file")
    parser.add_argument("--uri", default="tcp://0.0.0.0:10300", help="Wyoming server URI")
    parser.add_argument("--num-threads", type=int, default=4, help="Number of threads for inference")
    parser.add_argument("--use-itn", action="store_true", help="Enable Inverse Text Normalization")
    args = parser.parse_args()

    _LOGGER.info(f"Loading SenseVoice model from {args.model}")
    if not os.path.exists(args.model) or not os.path.exists(args.tokens):
        _LOGGER.error("Model or tokens file not found!")
        return

    recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=args.model,
        tokens=args.tokens,
        num_threads=args.num_threads,
        use_itn=args.use_itn,
        debug=False
    )
    _LOGGER.info("Model loaded successfully")

    server = AsyncServer.from_uri(args.uri)
    _LOGGER.info(f"Ready! Listening on {args.uri}")
    
    # We need a factory to pass the recognizer to the handler
    def handler_factory(*args_inner, **kwargs_inner):
        return SherpaSenseVoiceHandler(recognizer, *args_inner, **kwargs_inner)

    await server.run(handler_factory)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
