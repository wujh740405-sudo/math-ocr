from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import base64
import requests
import os

app = FastAPI()

# -------------------------------
# ① 挂载 static 文件夹，用于访问前端网页
# -------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------
# ② 首页路由：打开 OCR 上传界面
# -------------------------------
@app.get("/", response_class=HTMLResponse)
async def read_index():
    try:
        with open("static/ocr.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h2>⚠️ 没找到 static/ocr.html 文件，请确认路径。</h2>", status_code=404)

# -------------------------------
# ③ OCR 识别接口
# -------------------------------
@app.post("/api/ocr")
async def ocr_api(file: UploadFile = File(...)):
    try:
        # 读取上传图片
        content = await file.read()
        image_base64 = base64.b64encode(content).decode("utf-8")

        # 调用 Mathpix OCR（可替换为 DeepSeek）
        api_key = os.getenv("MATHPIX_API_KEY", "")
        headers = {"app_id": "your_app_id", "app_key": api_key}
        data = {"src": f"data:image/png;base64,{image_base64}", "formats": ["text"]}

        response = requests.post("https://api.mathpix.com/v3/text", json=data, headers=headers)
        return response.json()

    except Exception as e:
        return JSONResponse(content={"error": str(e)})

# -------------------------------
# ④ Render 自动运行 / 本地调试
# -------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
