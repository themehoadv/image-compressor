"""Verification tests for MoMo image compressor backend."""

import io
import time
from PIL import Image, ImageDraw
from app.compressor import compress_image
from app.main import app
from starlette.testclient import TestClient


def create_dummy_png(width=400, height=300):
    img = Image.new("RGBA", (width, height), (255, 100, 100, 255))
    for x in range(50, 150):
        for y in range(50, 150):
            img.putpixel((x, y), (50, 200, 50, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_dummy_jpeg(width=400, height=300):
    img = Image.new("RGB", (width, height), (100, 150, 250))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def create_large_image(width=2400, height=1800, mode="RGBA"):
    """Create a realistic high-resolution image to test ~2MB+ files."""
    img = Image.new(mode, (width, height), (220, 220, 230, 255) if mode == "RGBA" else (220, 220, 230))
    draw = ImageDraw.Draw(img)
    for i in range(0, width, 12):
        color = ((i * 3) % 256, (i * 7) % 256, (i * 11) % 256, 210) if mode == "RGBA" else ((i * 3) % 256, (i * 7) % 256, (i * 11) % 256)
        draw.line([(i, 0), (width - i, height)], fill=color, width=6)
    buf = io.BytesIO()
    fmt = "PNG" if mode == "RGBA" else "JPEG"
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_compressor_engine():
    # 1. Small PNG
    png_bytes = create_dummy_png()
    res_png = compress_image(png_bytes, "test.png", "image/png", quality=80)
    print(f"Small PNG: {res_png['original_size']} -> {res_png['compressed_size']} bytes (-{res_png['saved_percent']}%) in {res_png.get('duration_ms')}ms")
    assert res_png["compressed_size"] <= res_png["original_size"]
    assert res_png["saved_bytes"] >= 0

    # 2. Small JPEG
    jpeg_bytes = create_dummy_jpeg()
    res_jpeg = compress_image(jpeg_bytes, "test.jpg", "image/jpeg", quality=75)
    print(f"Small JPEG: {res_jpeg['original_size']} -> {res_jpeg['compressed_size']} bytes (-{res_jpeg['saved_percent']}%) in {res_jpeg.get('duration_ms')}ms")
    assert res_jpeg["compressed_size"] <= res_jpeg["original_size"]

    # 3. Large 2MB+ PNG compression (Must finish well under 3 seconds!)
    large_png = create_large_image(2400, 1800, mode="RGBA")
    print(f"Testing Large PNG: {len(large_png) / 1024 / 1024:.2f} MB...")
    t0 = time.perf_counter()
    res_large = compress_image(large_png, "large_photo.png", "image/png", quality=80)
    dur = time.perf_counter() - t0
    print(f"Large PNG: {res_large['original_size']/1024:.1f} KB -> {res_large['compressed_size']/1024:.1f} KB (-{res_large['saved_percent']}%) in {dur:.2f}s")
    assert dur < 3.0, f"Large PNG compression took {dur:.2f}s, exceeding 3-second requirement!"
    assert res_large["compressed_size"] <= res_large["original_size"]


def test_fastapi_endpoints():
    client = TestClient(app)

    # 1. Health check
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"
    print("Health check: OK")

    # 2. Compress endpoint with 2MB+ image
    large_png = create_large_image(2400, 1800, mode="RGBA")
    files = {"file": ("large_test.png", large_png, "image/png")}
    t0 = time.perf_counter()
    compress_resp = client.post("/api/compress?quality=80", files=files)
    elapsed = time.perf_counter() - t0
    assert compress_resp.status_code == 200
    json_data = compress_resp.json()
    assert json_data["success"] is True
    assert "data_url" in json_data
    assert json_data["saved_percent"] >= 0
    print(f"FastAPI /api/compress (Large File): OK in {elapsed:.2f}s")
    assert elapsed < 3.0, f"Endpoint took {elapsed:.2f}s, exceeding target threshold!"

    # 3. Raw endpoint
    png_bytes = create_dummy_png()
    files_raw = {"file": ("test.png", png_bytes, "image/png")}
    raw_resp = client.post("/api/compress-raw?quality=80", files=files_raw)
    assert raw_resp.status_code == 200
    assert "X-Savings-Percent" in raw_resp.headers
    print("FastAPI /api/compress-raw: OK")

    # 4. Batch ZIP endpoint
    batch_files = [
        ("files", ("test1.png", png_bytes, "image/png")),
        ("files", ("test2.png", png_bytes, "image/png")),
    ]
    zip_resp = client.post("/api/compress-batch-zip?quality=80", files=batch_files)
    assert zip_resp.status_code == 200
    assert zip_resp.headers["content-type"] == "application/zip"
    assert len(zip_resp.content) > 0
    print(f"FastAPI /api/compress-batch-zip: OK (ZIP size: {len(zip_resp.content)} bytes)")

    # 5. Error handling: Empty file (400)
    empty_files = {"file": ("empty.png", b"", "image/png")}
    empty_resp = client.post("/api/compress", files=empty_files)
    assert empty_resp.status_code == 400
    assert "empty" in empty_resp.json()["detail"].lower()
    print("Error handling (400 Empty File): OK")

    # 6. Error handling: Corrupt image file (422)
    corrupt_files = {"file": ("corrupt.png", b"not-a-valid-image-bytes", "image/png")}
    corrupt_resp = client.post("/api/compress", files=corrupt_files)
    assert corrupt_resp.status_code == 422
    assert "detail" in corrupt_resp.json()
    print("Error handling (422 Corrupt Image): OK")

    # 7. Verification of timeout simulation delay
    t_start = time.perf_counter()
    files_delay = {"file": ("test.png", png_bytes, "image/png")}
    delay_resp = client.post("/api/compress?quality=80&debug_delay=0.5", files=files_delay)
    delay_dur = time.perf_counter() - t_start
    assert delay_resp.status_code == 200
    assert delay_dur >= 0.5
    print(f"Debug delay simulation endpoint: OK ({delay_dur:.2f}s)")


if __name__ == "__main__":
    test_compressor_engine()
    test_fastapi_endpoints()
    print("\nAll compressor verification tests PASSED successfully!")

