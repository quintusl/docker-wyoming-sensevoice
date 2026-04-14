import argparse
import asyncio
from wyoming.asr import Transcribe, Transcript
from wyoming.server import AsyncServer
from funasr import AutoModel

# Load SenseVoice Model
model = AutoModel(model="iic/SenseVoiceSmall", device="cpu") # Change to "cuda" if using GPU

class SenseVoiceEventHandler:
    async def handle_event(self, event):
        if isinstance(event, Transcribe):
            # Process audio through SenseVoice
            res = model.generate(input=event.audio)
            text = res[0]['text']
            return Transcript(text=text)
        return None

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", required=True, help="unix:// or tcp://")
    args = parser.parse_args()

    server = AsyncServer.from_uri(args.uri)
    await server.run(lambda: SenseVoiceEventHandler())

if __name__ == "__main__":
    asyncio.run(main())
