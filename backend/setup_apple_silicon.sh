#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install paddlepaddle==3.2.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m pip install -U "paddleocr[doc-parser]"
python -m pip install fastapi python-multipart "uvicorn[standard]"

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Apple Silicon PaddleOCR-VL environment is ready."
