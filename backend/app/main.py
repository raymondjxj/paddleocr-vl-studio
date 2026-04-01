import json
import os
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware


APP_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = APP_DIR / "output"
UPLOAD_DIR = APP_DIR / "uploads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _parse_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
    if raw.strip() == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


def _pipeline_kwargs() -> dict[str, Any]:
    backend = os.getenv("PADDLEOCR_VL_BACKEND", "").strip()
    kwargs: dict[str, Any] = {}
    if backend:
        kwargs["vl_rec_backend"] = backend
        server_url = os.getenv("PADDLEOCR_VL_SERVER_URL", "").strip()
        model_name = os.getenv("PADDLEOCR_VL_MODEL_NAME", "PaddlePaddle/PaddleOCR-VL-1.5").strip()
        if server_url:
            kwargs["vl_rec_server_url"] = server_url
        if model_name:
            kwargs["vl_rec_api_model_name"] = model_name
    return kwargs


@lru_cache(maxsize=1)
def get_pipeline():
    try:
        from paddleocr import PaddleOCRVL
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "PaddleOCR is not installed. Follow the README Apple Silicon setup first."
        ) from exc

    return PaddleOCRVL(**_pipeline_kwargs())


def _find_first(path: Path, pattern: str) -> str | None:
    match = next(path.glob(pattern), None)
    if not match:
        return None
    return match.read_text(encoding="utf-8")


def _normalize_result(item: Any, index: int, request_dir: Path) -> dict[str, Any]:
    item.save_to_json(save_path=str(request_dir))
    item.save_to_markdown(save_path=str(request_dir))

    json_text = _find_first(request_dir, "*.json")
    markdown_text = _find_first(request_dir, "*.md")
    parsed_json: Any = None
    if json_text:
        try:
            parsed_json = json.loads(json_text)
        except json.JSONDecodeError:
            parsed_json = json_text

    return {
        "index": index,
        "json": parsed_json,
        "markdown": markdown_text,
        "preview": str(item),
    }


app = FastAPI(
    title="PaddleOCR VL Web API",
    description="Apple Silicon OCR backend built on the official PaddleOCR-VL flow.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "ok": True,
        "backend": os.getenv("PADDLEOCR_VL_BACKEND", "paddleocr"),
        "model": os.getenv("PADDLEOCR_VL_MODEL_NAME", "PaddlePaddle/PaddleOCR-VL-1.5"),
    }


@app.post("/api/ocr")
async def run_ocr(
    file: UploadFile = File(...),
    backend_mode: str | None = Form(default=None),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename.")

    suffix = Path(file.filename).suffix or ".bin"
    request_dir = Path(tempfile.mkdtemp(prefix="ocr_", dir=str(OUTPUT_DIR)))
    upload_path = UPLOAD_DIR / f"{request_dir.name}{suffix}"

    with upload_path.open("wb") as destination:
        shutil.copyfileobj(file.file, destination)

    if backend_mode:
        os.environ["PADDLEOCR_VL_BACKEND"] = backend_mode
        get_pipeline.cache_clear()

    try:
        pipeline = get_pipeline()
        results = pipeline.predict(str(upload_path))
        normalized = [
            _normalize_result(item, index=index, request_dir=request_dir)
            for index, item in enumerate(results)
        ]
        return {
            "filename": file.filename,
            "backend": os.getenv("PADDLEOCR_VL_BACKEND", "paddleocr"),
            "results": normalized,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"OCR failed: {exc}") from exc
    finally:
        if upload_path.exists():
            upload_path.unlink()
