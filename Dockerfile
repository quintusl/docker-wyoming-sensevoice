FROM python:3.11-slim

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the bridge server script
COPY server.py .

# Pre-download the model to the image (optional, saves startup time)
RUN python3 -c "from modelscope import snapshot_download; snapshot_download('iic/SenseVoiceSmall')"

EXPOSE 10300

ENTRYPOINT ["python3", "server.py"]
CMD ["--uri", "tcp://0.0.0.0:10300"]
