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

# =========================
# 初始化 FastAPI 应用
# =========================
app = FastAPI()

# -------------------- 基础配置 --------------------
# Tesseract 安装路径（Render 上不会用到，本地用）
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSDATA_PATH = r"C:\Program Files\Tesseract-OCR\tessdata"

if os.name == "nt" and os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# -------------------- 静态页面 --------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    index_path = "static/ocr.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h3>⚠️ 找不到 ocr.html 文件</h3>", status_code=404)


# -------------------- OCR 接口 --------------------
@app.post("/api/ocr")
async def ocr_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")
        return {"text": text.strip()}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# -------------------- 文字解析接口 --------------------
@app.post("/api/parse")
async def parse_question(request: Request):
    """
    接收 JSON 格式的数学题文本
    例如：{"text": "已知 f(x)=x^2-3x+2, 求单调区间"}
    """
    try:
        data = await request.json()
        question = data.get("text", "").strip()
        if not question:
            return JSONResponse(content={"error": "缺少 text 字段"}, status_code=400)

        # 简单模拟解析逻辑
        tags = []
        if "f(x)" in question or "函数" in question or "二次" in question or "x^2" in question:
            tags = ["函数-单调性", "二次函数"]
        elif "导数" in question or "求导" in question:
            tags = ["导数-求导法则", "导数-极值讨论"]
        else:
            tags = ["基础-阅读理解"]

        result = {
            "success": True,
            "parsed": {
                "question": question,
                "knowledge_tags": tags,
                "summary": f"自动解析示例：识别到 {len(tags)} 个标签"
            },
            "used": "local-fallback"
        }
        return JSONResponse(content=result, status_code=200)

    except json.JSONDecodeError:
        return JSONResponse(content={"error": "请求体不是有效的 JSON"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# -------------------- AI 数学求解接口 --------------------
class SolveReq(BaseModel):
    problem: str
    level: str = "高中"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

PROMPT_TEMPLATE = """
你是高中数学教练。下面给出一道题目，要求你**只输出一个 JSON**，不要多余其他语言、不要解释。
JSON 格式严格如下：
{
  "problem": "<原题文本>",
  "final_answer": "<最终答案或结论>",
  "steps": [
    {"step":"1","content":"写出操作或计算","explain":"为什么这样做"},
    {"step":"2","content":"...","explain":"..."}
  ],
  "why": "<对策略或方法的总结（2-3句话）>",
  "similar": ["同类型题目1","同类型题目2"]
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
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.3
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        raise Exception(f"模型调用失败: {r.status_code}, {r.text}")
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


# -------------------- 健康检查 --------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


# -------------------- 启动 --------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 启动中... 端口: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
