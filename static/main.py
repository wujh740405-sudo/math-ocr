# main.py
import os
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI(title="DeepSeek Proxy for Math GPT")

# 允许跨域（OpenAI 的服务器会请求你的服务）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 部署后可改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("请设置环境变量 DEEPSEEK_API_KEY")

# 简单访问控制：要求调用方带上 X-PROXY-KEY 与我们设定的 PROXY_KEY 一致
PROXY_KEY = os.getenv("PROXY_KEY")  # 在 Render 上配置此值

DEEPSEEK_URL = os.getenv("DEEPSEEK_URL", "https://api.deepseek.com/chat/completions")

@app.post("/call_deepseek")
async def call_deepseek(request: Request, x_proxy_key: str | None = Header(None)):
    # 验证 PROXY_KEY
    if PROXY_KEY and x_proxy_key != PROXY_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid proxy key")

    body = await request.json()
    # 这里期望 body 包含 messages 或者 query 字段
    # 你可以按需定制请求格式
    query = body.get("query")
    messages = body.get("messages")

    payload = {}
    if messages:
        payload["messages"] = messages
    else:
        payload["messages"] = [{"role": "user", "content": query or ""}]

    payload["model"] = body.get("model", "deepseek-chat")  # 可改为你想调用的模型名
    payload["max_tokens"] = body.get("max_tokens", 800)

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=30)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "DeepSeek request failed", "detail": str(e)})

    try:
        return JSONResponse(status_code=resp.status_code, content=resp.json())
    except Exception:
        return JSONResponse(status_code=resp.status_code, content={"text": resp.text})
