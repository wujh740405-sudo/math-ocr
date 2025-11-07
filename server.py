from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pytesseract
from PIL import Image
import io
import os

app = FastAPI()

# ✅ 1. 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ 2. 首页（访问根路径时自动显示 index.html）
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return HTMLResponse("<h3>⚠️ static/index.html 未找到</h3>", status_code=404)

# ✅ 3. OCR 页面
@app.get("/ocr.html", response_class=HTMLResponse)
async def serve_ocr():
    ocr_path = "static/ocr.html"
    if os.path.exists(ocr_path):
        return FileResponse(ocr_path)
    else:
        return HTMLResponse("<h3>⚠️ static/ocr.html 未找到</h3>", status_code=404)

# ✅ 4. OCR 接口
@app.post("/api/ocr")
async def ocr_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # 自动识别中英文
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")

        # 返回识别结果
        return {"text": text.strip()}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ✅ 5. 健康检查
@app.get("/health")
async def health():
    return {"status": "ok"}

# ✅ 6. 本地启动（Render 会自动忽略）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
