"""
AI 数学老师 - 后端服务（Render 自动安装 Linux Tesseract 版本）
"""

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image
import pytesseract
import io
import os
import json
import requests

# ==================================================
# Render 自动安装 Linux Tesseract
# ==================================================
if os.environ.get("RENDER"):
    import subprocess

    TESS_PATH = "/usr/bin/tesseract"   # Render apt-get 默认安装路径

    # 检查 tesseract 是否已安装
    if not os.path.exists(TESS_PATH):
        print("🔧 Render 环境未安装 Tesseract，正在自动安装中...")
        subprocess.run(
            ["bash", "-c", "apt-get update && apt-get install -y tesseract-ocr"],
            check=False
        )
        print("✅ Tesseract 安装完成")

    pytesseract.pytesseract.tesseract_cmd = TESS_PATH
    print(f"📌 使用 Tesseract 路径：{TESS_PATH}")

# Windows 本地路径
if os.name == "nt":
    WIN_TESS_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(WIN_TESS_PATH):
        pytesseract.pytesseract.tesseract_cmd = WIN_TESS_PATH
        print("📌 本地使用 Windows Tesseract")

# ==================================================
# FastAPI 初始化
# ==================================================
app = FastAPI(title="AI 数学老师", version="2.0")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    """
    注意：你的页面文件是 static/index.html，不是 ocr.html
    """
    file_path = "static/index.html"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse("<h3>⚠️ 未找到 static/index.html</h3>", status_code=404)

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
# 数学题解析
# ==================================================
@app.post("/api/parse")
async def parse_question(request: Request):
    data = await request.json()
    question = data.get("text", "").strip()

    if not question:
        return JSONResponse({"error": "缺少 text 字段"}, status_code=400)

    # 简单分类示例
    tags = []
    if "函数" in question:
        tags = ["函数-单调性", "二次函数"]
    elif "导数" in question:
        tags = ["导数-求导", "导数-极值"]
    else:
        tags = ["基础识别"]

    return {
        "success": True,
        "parsed": {
            "question": question,
            "knowledge_tags": tags
        }
    }

# ==================================================
# DeepSeek 解题
# ==================================================
class SolveReq(BaseModel):
    problem: str
    level: str = "高中"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

PROMPT_TEMPLATE = """
你是高中数学教练。严格输出 JSON。
{
  "problem": "<原题>",
  "final_answer": "<最终答案>",
  "steps": [
    {"step":"1","content":"步骤描述","explain":"解释"},
    {"step":"2","content":"...","explain":"..."}
  ],
  "why": "<方法总结>",
  "similar": ["同类题1","同类题2"]
}
题目：{problem}
难度：{level}
"""

def call_deepseek(prompt: str):
    if not DEEPSEEK_API_KEY:
        raise Exception("缺少 DEEPSEEK_API_KEY 环境变量")

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
    }

    r = requests.post(url, json=payload, headers=headers)
    data = r.json()

    return data["choices"][0]["message"]["content"]

@app.post("/api/solve")
async def solve(req: SolveReq):
    try:
        prompt = PROMPT_TEMPLATE.format(problem=req.problem, level=req.level)
        output = call_deepseek(prompt)
        return json.loads(output)
    except Exception as e:
        return {"error": str(e)}

# ==================================================
# 健康检查
# ==================================================
@app.get("/health")
async def health():
    return {"status": "ok"}

# ==================================================
# 本地启动
# ==================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
