#!/bin/bash
set -e

MODEL_REPO=${MODEL_REPO:-"csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09"}
MODEL_DIR="/app/model"

if [ ! -f "$MODEL_DIR/model.int8.onnx" ]; then
    echo "Model not found. Downloading from $MODEL_REPO..."
    python3 download_model.py --repo "$MODEL_REPO" --out "$MODEL_DIR"
fi

CHINESE_SCRIPT_FLAG=""
if [ "${TRADITIONAL_CHINESE,,}" = "true" ] || [ "${TRADITIONAL_CHINESE,,}" = "1" ]; then
    CHINESE_SCRIPT_FLAG="--traditional-chinese"
elif [ "${SIMPLIFIED_CHINESE,,}" = "true" ] || [ "${SIMPLIFIED_CHINESE,,}" = "1" ]; then
    CHINESE_SCRIPT_FLAG="--simplified-chinese"
fi

echo "Starting Wyoming Sherpa-ONNX SenseVoice server..."
exec python3 wyoming_sherpa_sensevoice.py \
    --model "$MODEL_DIR/model.int8.onnx" \
    --tokens "$MODEL_DIR/tokens.txt" \
    --uri "tcp://0.0.0.0:10300" \
    --num-threads "${NUM_THREADS:-4}" \
    --use-itn \
    $CHINESE_SCRIPT_FLAG
