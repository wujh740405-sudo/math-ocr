from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import pytesseract
import io
import os

# ✅ 如果是 Windows 本地运行，请确保 tesseract 安装路径正确
# 如果你是在 Render 部署，请注释掉下一行
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -----------------------------------------------------
# 启动 FastAPI 应用
# -----------------------------------------------------
app = FastAPI()

# ✅ 1. 静态文件目录（前端页面）
app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ 2. 首页：访问 http://127.0.0.1:8000 显示 index.html
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h3>⚠️ 找不到 static/index.html 文件</h3>", status_code=404)

# ✅ 3. OCR 页面：访问 http://127.0.0.1:8000/ocr.html
@app.get("/ocr.html", response_class=HTMLResponse)
async def serve_ocr():
    ocr_path = "static/ocr.html"
    if os.path.exists(ocr_path):
        return FileResponse(ocr_path)
    return HTMLResponse("<h3>⚠️ 找不到 static/ocr.html 文件</h3>", status_code=404)

# ✅ 4. OCR 识别接口
@app.post("/api/ocr")
async def ocr_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # 自动识别中英文
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")

        return {"text": text.strip()}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ✅ 5. 健康检查接口（Render 会用这个检查是否启动成功）
@app.get("/health")
async def health():
    return {"status": "ok"}

# ✅ 6. 启动入口
if __name__ == "__main__":
    import uvicorn
    # ✅ 自动判断运行环境（Render会注入PORT=10000）
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 服务器启动中： http://127.0.0.1:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
