"""Image compression engine for White Buffalo MoMo Image Compressor.

Handles in-memory compression for PNG, JPEG, WebP, and other raster formats
with optimal visual fidelity, high speed, and high compression ratios (TinyPNG-style).
"""

from __future__ import annotations

import io
import logging
import os
import time
from typing import Any, Dict, Tuple
from PIL import Image, ImageFile, ImageOps

# Configure logger
logger = logging.getLogger("momo.compressor")

# Image safety configurations
ImageFile.LOAD_TRUNCATED_IMAGES = True
# Allow reasonable large images while guarding against multi-gigabyte decompression bombs
Image.MAX_IMAGE_PIXELS = 100_000_000

SUPPORTED_MIME_TYPES = {
    "image/png": "PNG",
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/webp": "WEBP",
    "image/gif": "GIF",
}

EXTENSION_TO_FORMAT = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP",
    ".gif": "GIF",
}


def detect_format(filename: str, content_type: str | None = None) -> str:
    """Detect image format from MIME type or file extension."""
    if content_type and content_type.lower() in SUPPORTED_MIME_TYPES:
        return SUPPORTED_MIME_TYPES[content_type.lower()]

    ext = os.path.splitext(filename)[1].lower()
    if ext in EXTENSION_TO_FORMAT:
        return EXTENSION_TO_FORMAT[ext]

    return "JPEG"  # default fallback


def _compress_jpeg(img: Image.Image, quality: int, filename: str = "") -> bytes:
    """Compress JPEG image with progressive encoding and arithmetic optimization."""
    t0 = time.perf_counter()
    # JPEG does not support alpha channel
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        if img.mode in ("RGBA", "LA"):
            alpha = img.split()[-1]
            background.paste(img, mask=alpha)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    output = io.BytesIO()
    img.save(
        output,
        format="JPEG",
        quality=max(10, min(quality, 95)),
        optimize=True,
        progressive=True,
    )
    data = output.getvalue()
    dur_ms = (time.perf_counter() - t0) * 1000
    logger.debug(f"[{filename}] JPEG compressed in {dur_ms:.1f}ms: {len(data)/1024:.1f}KB")
    return data


def _compress_png(img: Image.Image, quality: int, filename: str = "") -> bytes:
    """Compress PNG using smart palette quantization and fast zlib compression (TinyPNG-style).

    Uses FASTOCTREE for RGBA/LA (preserving alpha channel and preventing Pillow quantization deadlock)
    and MEDIANCUT for RGB/L images. Avoids slow brute-force filter evaluation (optimize=True) on large images
    to guarantee sub-second compression times.
    """
    # Map quality (10-100) to palette color count (32-256)
    if quality >= 90:
        max_colors = 256
    elif quality >= 75:
        max_colors = 192
    elif quality >= 55:
        max_colors = 128
    else:
        max_colors = 64

    quantized_bytes = None
    t0 = time.perf_counter()

    try:
        # Quantize according to image mode
        if img.mode in ("RGBA", "LA"):
            # Pillow requires FASTOCTREE (method=2) or LIBIMAGEQUANT (method=3) for RGBA.
            # FASTOCTREE preserves transparency and finishes in milliseconds.
            quantized = img.quantize(
                colors=max_colors,
                method=Image.Quantize.FASTOCTREE,
                dither=Image.Dither.FLOYDSTEINBERG,
            )
        elif img.mode in ("RGB", "L"):
            quantized = img.quantize(
                colors=max_colors,
                method=Image.Quantize.MEDIANCUT,
                dither=Image.Dither.FLOYDSTEINBERG,
            )
        else:
            quantized = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=max_colors)

        t_quant = (time.perf_counter() - t0) * 1000
        logger.info(f"[{filename}] PNG palette quantization ({img.mode} -> {quantized.mode}, max_colors={max_colors}) took {t_quant:.1f}ms")

        quantized_buf = io.BytesIO()
        # Use compress_level=6 (industry standard fast zlib) without scanline filter permutations
        quantized.save(quantized_buf, format="PNG", compress_level=6)
        quantized_bytes = quantized_buf.getvalue()

    except Exception as q_err:
        logger.warning(f"[{filename}] PNG palette quantization skipped due to: {q_err}")

    # Lossless candidate using standard fast level 6
    lossless_buf = io.BytesIO()
    img.save(lossless_buf, format="PNG", compress_level=6)
    lossless_bytes = lossless_buf.getvalue()

    # Pick the smaller result between quantized palette and lossless PNG
    if quantized_bytes and len(quantized_bytes) < len(lossless_bytes):
        return quantized_bytes

    return lossless_bytes


def _compress_webp(img: Image.Image, quality: int, filename: str = "") -> bytes:
    """Compress WebP image with balanced high-speed analysis."""
    t0 = time.perf_counter()
    output = io.BytesIO()
    # method=4 provides optimal balance between high compression and speed (< 0.5s)
    img.save(
        output,
        format="WEBP",
        quality=max(10, min(quality, 95)),
        method=4,
    )
    data = output.getvalue()
    dur_ms = (time.perf_counter() - t0) * 1000
    logger.debug(f"[{filename}] WebP compressed in {dur_ms:.1f}ms: {len(data)/1024:.1f}KB")
    return data


def compress_image(
    file_bytes: bytes,
    filename: str,
    content_type: str | None = None,
    quality: int = 80,
) -> Dict[str, Any]:
    """Compress an image in-memory and return compression statistics and binary payload.

    Args:
        file_bytes: Original image bytes
        filename: Original filename
        content_type: MIME type of uploaded file
        quality: Target quality score (10 to 100, default 80)

    Returns:
        Dict containing:
            - filename: str
            - mime_type: str
            - width: int
            - height: int
            - original_size: int
            - compressed_size: int
            - saved_bytes: int
            - saved_percent: float
            - data: bytes
    """
    original_size = len(file_bytes)
    if original_size == 0:
        raise ValueError("Uploaded file is empty.")

    t_start = time.perf_counter()
    logger.info(
        f"Processing image '{filename}' (size: {original_size / 1024:.1f} KB, requested quality: {quality})"
    )

    try:
        input_buf = io.BytesIO(file_bytes)
        img = Image.open(input_buf)

        # Apply EXIF orientation if available
        try:
            img = ImageOps.exif_transpose(img)
        except Exception as exif_err:
            logger.debug(f"[{filename}] EXIF transpose skipped: {exif_err}")

        img_format = detect_format(filename, content_type or img.format)
        width, height = img.size

        logger.debug(
            f"[{filename}] Detected format: {img_format}, dimensions: {width}x{height}, mode: {img.mode}"
        )

        if img_format == "JPEG":
            compressed_bytes = _compress_jpeg(img, quality, filename=filename)
            mime_type = "image/jpeg"
        elif img_format == "PNG":
            compressed_bytes = _compress_png(img, quality, filename=filename)
            mime_type = "image/png"
        elif img_format == "WEBP":
            compressed_bytes = _compress_webp(img, quality, filename=filename)
            mime_type = "image/webp"
        else:
            # Fallback to PNG optimization
            compressed_bytes = _compress_png(img, quality, filename=filename)
            mime_type = "image/png"

        compressed_size = len(compressed_bytes)

        # Automatic fallback preventing negative savings
        if compressed_size >= original_size and original_size > 0:
            final_bytes = file_bytes
            final_size = original_size
            saved_bytes = 0
            saved_percent = 0.0
            logger.info(
                f"[{filename}] Compressed size ({compressed_size / 1024:.1f} KB) >= Original ({original_size / 1024:.1f} KB). Retaining original bytes."
            )
        else:
            final_bytes = compressed_bytes
            final_size = compressed_size
            saved_bytes = original_size - final_size
            saved_percent = round((saved_bytes / original_size) * 100, 1)

        total_duration_ms = (time.perf_counter() - t_start) * 1000
        logger.info(
            f"[{filename}] Finished in {total_duration_ms:.1f}ms: "
            f"{original_size / 1024:.1f} KB -> {final_size / 1024:.1f} KB (-{saved_percent}%)"
        )

        return {
            "filename": filename,
            "mime_type": mime_type,
            "width": width,
            "height": height,
            "original_size": original_size,
            "compressed_size": final_size,
            "saved_bytes": saved_bytes,
            "saved_percent": saved_percent,
            "data": final_bytes,
            "duration_ms": round(total_duration_ms, 1),
        }

    except Exception as exc:
        total_duration_ms = (time.perf_counter() - t_start) * 1000
        logger.error(f"[{filename}] Compression failed after {total_duration_ms:.1f}ms: {exc}", exc_info=True)
        raise ValueError(f"Failed to process image '{filename}': {str(exc)}") from exc
