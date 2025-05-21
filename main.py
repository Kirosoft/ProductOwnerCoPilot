import os
import json
import httpx
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

OLLAMA_MODEL = os.getenv("LLM_MODEL", "mistral-small:latest")

def convert_messages_to_prompt(messages):
    return "\n".join([m["content"] for m in messages if m["role"] == "user"])

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/stream_result")
async def stream_result(prompt: str, template: str = "pbi"):
    if template == "product_goal":
        template_path = "static/product_goal_template.txt"
    else:
        template_path = "static/pbi_template.txt"
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    except FileNotFoundError:
        async def error_stream():
            yield "Error: template file not found."
        return StreamingResponse(error_stream(), media_type="text/plain")
    ollama_prompt = f"Using the following template:\n---\n{template_content}\n---\nFill in the details based on this information:\n---\n{prompt}\n---"
    messages = [{"role": "user", "content": ollama_prompt}]
    async def stream_generator():
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": convert_messages_to_prompt(messages),
            "stream": True
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", "http://localhost:11434/api/generate", json=payload) as response:
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("response", "")
                        if content:
                            yield content
                        if data.get("done", False):
                            break
                    except Exception as e:
                        yield f"\n[Streaming error: {str(e)}]\n"
                        break
    return StreamingResponse(stream_generator(), media_type="text/plain")
