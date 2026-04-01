# PaddleOCR VL Web App

This project wraps the official PaddleOCR-VL Apple Silicon setup in a simple web application:

- `backend/` runs a local FastAPI OCR service on your Apple Silicon Mac.
- `web/` is a static frontend that can be deployed to Netlify.
- `PaddleOCR/` is reserved for the official upstream repository clone and is ignored by git.

## Architecture

Netlify cannot run the Apple Silicon-specific PaddleOCR-VL backend. The production-friendly setup is:

1. Deploy the static frontend to Netlify.
2. Run the OCR backend on an Apple Silicon Mac or another dedicated machine.
3. Point the frontend to that backend URL.

## Official PaddleOCR-VL Apple Silicon setup

The backend follows the official installation flow from PaddleOCR docs:

```bash
python3 -m venv .venv_paddleocr
source .venv_paddleocr/bin/activate
python -m pip install paddlepaddle==3.2.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m pip install -U "paddleocr[doc-parser]"
```

Optional MLX-VLM acceleration:

```bash
python -m pip install "mlx-vlm>=0.3.11"
mlx_vlm.server --port 8111
```

## Run the backend locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 5050
```

The backend defaults to standard PaddleOCR-VL inference. To use the MLX-VLM server described in the official guide, set these values in `backend/.env`:

```bash
PADDLEOCR_VL_BACKEND=mlx-vlm-server
PADDLEOCR_VL_SERVER_URL=http://127.0.0.1:8111/
PADDLEOCR_VL_MODEL_NAME=PaddlePaddle/PaddleOCR-VL-1.5
```

## Run the frontend locally

Because the frontend is static, any simple static server works:

```bash
cd web
python3 -m http.server 8080
```

Open `http://127.0.0.1:8080` and set the backend URL to `http://127.0.0.1:5050`.

## Deploy the frontend to Netlify

This repo includes a `netlify.toml` that publishes the `web/` directory directly.

If you later host the backend on a public URL, update the frontend's backend URL in the UI or prefill it through query parameters:

```text
https://your-netlify-site.netlify.app/?backend=https://your-backend.example.com
```

## API

- `GET /api/health`
- `POST /api/ocr`
  - form field: `file`
  - optional form field: `backend_mode`
