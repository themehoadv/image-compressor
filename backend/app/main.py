"""FastAPI Application for White Buffalo MoMo Image Compressor."""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import time
import zipfile
from typing import List

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from starlette.concurrency import run_in_threadpool

from .compressor import compress_image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("momo.api")

app = FastAPI(
    title="White Buffalo MoMo Image Compressor API",
    description="Stateless, high-efficiency image compression microservice inspired by TinyPNG.",
    version="1.0.0",
)

# Enable CORS for decoupled frontend and microservice ecosystem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Original-Size", "X-Compressed-Size", "X-Savings-Percent", "Content-Disposition"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint for container and monitoring probes."""
    return {
        "status": "healthy",
        "app": "White Buffalo MoMo Image Compressor",
        "version": "1.0.0",
        "supported_formats": ["PNG", "JPEG", "JPG", "WEBP", "GIF"],
    }


@app.post("/api/compress")
async def compress_endpoint(
    file: UploadFile = File(...),
    quality: int = Query(80, ge=10, le=100, description="Compression quality (10-100)"),
    debug_delay: float = Query(0.0, ge=0.0, le=60.0, description="Optional delay for client timeout testing"),
):
    """Compress a single image and return detailed statistics and base64 data URI."""
    t0 = time.perf_counter()
    filename = file.filename or "image.png"

    try:
        content = await file.read()
        if not content:
            logger.warning(f"Empty upload received for filename '{filename}'")
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        logger.info(
            f"Incoming compression request: '{filename}' ({len(content) / 1024:.1f} KB, quality={quality})"
        )

        # Allow artificial delay if requested for verification and client timeout testing
        if debug_delay > 0:
            logger.info(f"Simulating debug delay: {debug_delay}s for '{filename}'")
            await asyncio.sleep(debug_delay)

        # Run CPU-bound compression in threadpool to keep FastAPI asyncio event loop completely responsive
        result = await run_in_threadpool(
            compress_image,
            file_bytes=content,
            filename=filename,
            content_type=file.content_type,
            quality=quality,
        )

        b64_encoded = base64.b64encode(result["data"]).decode("ascii")
        data_url = f"data:{result['mime_type']};base64,{b64_encoded}"

        total_req_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            f"Successfully responded for '{filename}' in {total_req_ms:.1f}ms: "
            f"{result['original_size']/1024:.1f} KB -> {result['compressed_size']/1024:.1f} KB (-{result['saved_percent']}%)"
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "filename": result["filename"],
                "mime_type": result["mime_type"],
                "width": result["width"],
                "height": result["height"],
                "original_size": result["original_size"],
                "compressed_size": result["compressed_size"],
                "saved_bytes": result["saved_bytes"],
                "saved_percent": result["saved_percent"],
                "data_url": data_url,
                "duration_ms": result.get("duration_ms", round(total_req_ms, 1)),
            },
        )
    except HTTPException:
        raise
    except ValueError as val_err:
        total_req_ms = (time.perf_counter() - t0) * 1000
        logger.warning(f"Validation error for '{filename}' after {total_req_ms:.1f}ms: {val_err}")
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception as exc:
        total_req_ms = (time.perf_counter() - t0) * 1000
        logger.error(f"Internal compression error for '{filename}' after {total_req_ms:.1f}ms: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal compression error: {str(exc)}")


@app.post("/api/compress-raw")
async def compress_raw_endpoint(
    file: UploadFile = File(...),
    quality: int = Query(80, ge=10, le=100),
):
    """Compress image and return raw binary stream with statistics in headers (CLI/curl friendly)."""
    t0 = time.perf_counter()
    filename = file.filename or "image.png"

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        logger.info(f"Incoming raw compression request: '{filename}' ({len(content) / 1024:.1f} KB)")

        result = await run_in_threadpool(
            compress_image,
            file_bytes=content,
            filename=filename,
            content_type=file.content_type,
            quality=quality,
        )

        headers = {
            "Content-Disposition": f'attachment; filename="compressed_{result["filename"]}"',
            "X-Original-Size": str(result["original_size"]),
            "X-Compressed-Size": str(result["compressed_size"]),
            "X-Savings-Percent": str(result["saved_percent"]),
        }
        total_req_ms = (time.perf_counter() - t0) * 1000
        logger.info(f"Responded raw binary for '{filename}' in {total_req_ms:.1f}ms")

        return Response(
            content=result["data"],
            media_type=result["mime_type"],
            headers=headers,
        )
    except HTTPException:
        raise
    except ValueError as val_err:
        logger.warning(f"Validation error in raw endpoint for '{filename}': {val_err}")
        raise HTTPException(status_code=422, detail=str(val_err))
    except Exception as exc:
        logger.error(f"Internal error in raw endpoint for '{filename}': {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/compress-batch-zip")
async def compress_batch_zip_endpoint(
    files: List[UploadFile] = File(...),
    quality: int = Query(80, ge=10, le=100),
):
    """Compress multiple images in batch and stream an in-memory ZIP archive directly."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    logger.info(f"Incoming batch ZIP request for {len(files)} files (quality={quality})")
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            content = await f.read()
            if not content:
                continue
            fname = f.filename or "image.png"
            try:
                result = await run_in_threadpool(
                    compress_image,
                    file_bytes=content,
                    filename=fname,
                    content_type=f.content_type,
                    quality=quality,
                )
                zf.writestr(f"compressed_{result['filename']}", result["data"])
                logger.info(f"Added compressed '{result['filename']}' to batch ZIP")
            except Exception as item_err:
                logger.warning(f"Failed to compress '{fname}' in batch ZIP, including original. Error: {item_err}")
                zf.writestr(fname, content)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="momo_compressed_images.zip"'},
    )
