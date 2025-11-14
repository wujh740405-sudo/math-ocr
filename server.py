"""
AI 数学老师 - 后端服务（使用 RapidOCR，无需 Tesseract）
"""

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image
import numpy as np
import io
import os
import json
import requests
import webbrowser

# ==================================================
# 使用 RapidOCR（Render 免费实例可运行）
# ==================================================
from rapidocr_paddle import RapidOCR
ocr = RapidOCR()

# ==================================================
# FastAPI 初始化
# ==================================================
app = FastAPI(title="AI 数学老师", version="2.0")

# 静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    ocr_path = "static/ocr.html"
    if os.path.exists(ocr_path):
        return FileResponse(ocr_path)
    return HTMLResponse("<h3>⚠️ 找不到 static/ocr.html</h3>", status_code=404)

# ==================================================
# 1. OCR 识别接口（无需 Tesseract）
# ==================================================
@app.post("/api/ocr")
async def ocr_image(file: UploadFile = File(...)):
    try:
        img_bytes = await file.read()
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img_np = np.array(image)

        result, _ = ocr(img_np)
        if not result:
            return {"text": ""}

        text = "\n".join([line[1] for line in result])
        return {"text": text}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ==================================================
# 2. 数学题解析
# ==================================================
@app.post("/api/parse")
async def parse_question(request: Request):
    data = await request.json()
    question = data.get("text", "").strip()

    if not question:
        return JSONResponse({"error": "缺少 text 字段"}, status_code=400)

    tags = []
    if "f(x)" in question or "函数" in question:
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
# 3. 调用 DeepSeek AI 求解数学题
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
# 本地调试
# ==================================================
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 本地服务启动 http://127.0.0.1:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
