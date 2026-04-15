FROM python:3.11-slim

ARG SENSEVOICE_MODEL_NAME=iic/SenseVoiceSmall

ENV SENSEVOICE_MODEL_NAME=${SENSEVOICE_MODEL_NAME} \
    SENSEVOICE_MODELS_DIR=/models \
    MODELSCOPE_CACHE=/models/modelscope \
    SENSEVOICE_DEVICE=cpu \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install ffmpeg (runtime) and build-essential (compile-time for pip packages).
# Purge build-essential in the same layer so it doesn't bloat the final image.
COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg build-essential \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the bridge server script.
COPY server.py .

# Run as a non-root user for better security.
RUN useradd --system --no-create-home --uid 1000 appuser \
    && mkdir -p /models \
    && chown -R appuser /app /models

VOLUME ["/models"]

USER appuser

EXPOSE 10300

ENTRYPOINT ["python3", "server.py"]
CMD ["--uri", "tcp://0.0.0.0:10300"]
