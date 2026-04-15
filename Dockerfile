FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
# Use --no-cache-dir to keep image small
RUN pip install --no-cache-dir \
    numpy \
    sherpa-onnx \
    wyoming \
    huggingface_hub

# Copy application files
COPY wyoming_sherpa_sensevoice.py .
COPY download_model.py .
COPY run.sh .

# Ensure run.sh is executable
RUN chmod +x run.sh

# Create model directory and set permissions
RUN mkdir -p /app/model && chmod 777 /app/model

# Expose Wyoming port
EXPOSE 10300

# Default environment variables
ENV MODEL_REPO="csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09"
ENV NUM_THREADS=4

# Run the server
CMD ["./run.sh"]
