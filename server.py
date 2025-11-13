"""
AI 数学老师 - 最终版（Render 部署适配 + CORS 跨域支持）
"""

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import pytesseract
import io
import os
import json
import requests
import webbrowser

# ==================================================
# 初始化 FastAPI 应用
# ==================================================
app = FastAPI(title="AI 数学老师", version="3.0")

# 启用跨域 CORS 支持（防止浏览器请求被阻止）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 允许所有来源（可改为特定前端域名）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# 运行环境检测
# ==================================================
IS_RENDER = bool(os.environ.get("RENDER"))
LOCAL_MODE = not IS_RENDER

# Tesseract OCR 路径（仅本地使用）
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.name == "nt" and os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# ==================================================
# 静态文件（网页前端）
# ==================================================
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    """首页：加载 OCR 页面"""
    ocr_path = "static/ocr.html"
    if os.path.exists(ocr_path):
        return FileResponse(ocr_path)
    return HTMLResponse("<h3>⚠️ 找不到 static/ocr.html</h3>", status_code=404)

# ==================================================
# OCR 接口
# ==================================================
@app.post("/api/ocr")
async def ocr_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")
        return {"text": text.strip()}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ==================================================
# 数学题文字解析接口
# ==================================================
@app.post("/api/parse")
async def parse_question(request: Request):
    try:
        data = await request.json()
        question = data.get("text", "").strip()
        if not question:
            return JSONResponse(content={"error": "缺少 text 字段"}, status_code=400)

        # 模拟标签识别
        tags = []
        if "f(x)" in question or "二次" in question or "x^2" in question:
            tags = ["函数-单调性", "二次函数"]
        elif "导数" in question:
            tags = ["导数-求导法则", "导数-极值讨论"]
        else:
            tags = ["基础-理解与分析"]

        result = {
            "success": True,
            "parsed": {
                "question": question,
                "knowledge_tags": tags,
                "summary": f"自动识别出 {len(tags)} 个标签"
            },
            "used": "local"
        }
        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ==================================================
# AI 数学求解接口
# ==================================================
class SolveReq(BaseModel):
    problem: str
    level: str = "高中"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
PROMPT_TEMPLATE = """
你是一个数学老师，请根据以下题目生成 JSON 格式的详细解答。
JSON 示例：
{
  "problem": "<题目>",
  "final_answer": "<结论>",
  "steps": [
    {"step":"1","content":"...","explain":"..."},
    {"step":"2","content":"...","explain":"..."}
  ],
  "why": "<总结>",
  "similar": ["同类题1","同类题2"]
}
题目：{problem}
难度：{level}
"""

def call_deepseek(prompt: str):
    if not DEEPSEEK_API_KEY:
        raise Exception("缺少 DEEPSEEK_API_KEY 环境变量")
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.3
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    data = r.json()
    return data["choices"][0]["message"]["content"]

@app.post("/api/solve")
async def solve(req: SolveReq):
    try:
        prompt = PROMPT_TEMPLATE.format(problem=req.problem, level=req.level)
        result = call_deepseek(prompt)
        return json.loads(result)
    except Exception as e:
        return {"error": str(e)}

# ==================================================
# 健康检查接口
# ==================================================
@app.get("/health")
async def health():
    return {"status": "ok"}

# ==================================================
# 主程序入口
# ==================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 启动中... 模式: {'Render 云端' if IS_RENDER else '本地开发'} 端口: {port}")
    if LOCAL_MODE:
        webbrowser.open(f"http://127.0.0.1:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
