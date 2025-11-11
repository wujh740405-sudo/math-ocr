from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image
import pytesseract
import io
import os


app = FastAPI()

# -------------------- 基础配置 --------------------
# Tesseract 安装路径（请根据你电脑路径修改）
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSDATA_PATH = r"C:\Program Files\Tesseract-OCR\tessdata"

# 设置 tesseract 路径
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# 检查 Tesseract 是否存在
if not os.path.exists(TESSERACT_PATH):
    print("❌ 未找到 Tesseract 可执行文件，请检查安装路径：", TESSERACT_PATH)

# 检查中文语言包是否存在
chi_sim_path = os.path.join(TESSDATA_PATH, "chi_sim.traineddata")
if not os.path.exists(chi_sim_path):
    print("⚠️ 未找到 chi_sim.traineddata，请下载后放入：", TESSDATA_PATH)

# -------------------- 静态页面 --------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    index_path = "static/ocr.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h3>⚠️ 找不到 ocr.html 文件</h3>", status_code=404)


# -------------------- OCR 接口 --------------------
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI()

@app.post("/api/solve")
async def solve_math(request: Request):
    try:
        # 读取 JSON 数据
        data = await request.json()
        problem = data.get("problem", "")
        level = data.get("level", "")

        if not problem:
            return JSONResponse(content={"error": "缺少 'problem' 参数"}, status_code=400)

        # 这里可以加入你自己的数学求解逻辑
        # 现在先返回一个模拟结果
        return {
            "problem": problem,
            "level": level,
            "final_answer": "(-∞, 3/2) 递减, (3/2, +∞) 递增",
            "steps": [
                {"step": 1, "content": "求导 f'(x)=2x-3"},
                {"step": 2, "content": "解得 x=3/2"},
                {"step": 3, "content": "左负右正 → 单调区间"},
            ],
        }
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
# 数学题解析接口（文字版）
from fastapi import Request
import json

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

        # ---------- 这里是本地回退解析示例（可替换为调用 OpenAI/Mathpix/DeepSeek） ----------
        # 简单模拟解析：根据关键字返回示例 knowledge_tags
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


# ==============================
#  AI 数学求解接口部分
# ==============================

class SolveReq(BaseModel):
    problem: str
    level: str = "高中"

# ✅ 从环境变量获取 DeepSeek 或 OpenAI API 密钥
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
注意：答案字段中的数学符号请用 LaTeX（例如 x^2 写作 \\(x^2\\)）。
请严格输出 JSON。
"""

def call_deepseek(prompt: str):
    url = "https://api.deepseek.com/v1/chat/completions"  # ✅ DeepSeek API 正式地址
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
        # 要求模型返回标准 JSON 字符串
        return json.loads(output)
    except Exception as e:
        return {"error": str(e)}
from fastapi import Request
import json

# 数学题解析接口（文字版）
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

        # 简单模拟解析（你可以接入 Mathpix 或 OpenAI）
        result = {
            "success": True,
            "parsed": {
                "question": question,
                "knowledge_tags": ["函数-单调性", "二次函数"],
                "summary": "自动解析示例：识别到 2 个标签"
            },
            "used": "local-fallback"
        }
        return JSONResponse(content=result, status_code=200)

    except json.JSONDecodeError:
        return JSONResponse(content={"error": "请求体不是有效的 JSON"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# -------------------- 健康检查 --------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


# -------------------- 本地运行 --------------------
if __name__ == "__main__":
    import uvicorn
    print("🚀 启动 OCR 服务中...")
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

