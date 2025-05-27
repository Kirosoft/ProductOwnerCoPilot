import os
import json
import httpx
import logging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from datetime import datetime
from elasticsearch import Elasticsearch
import aiofiles

# Elastic APM setup
try:
    import elasticapm
    from elasticapm.contrib.starlette import make_apm_client, ElasticAPM
    APM_SERVER_URL = os.getenv("ELASTIC_APM_SERVER_URL")
    APM_SECRET_TOKEN = os.getenv("ELASTIC_APM_SECRET_TOKEN")
    APM_SERVICE_NAME = os.getenv("ELASTIC_APM_SERVICE_NAME", "product-owner-copilot")
    apm_config = {
        'SERVICE_NAME': APM_SERVICE_NAME,
        'SERVER_URL': APM_SERVER_URL,
        'SECRET_TOKEN': APM_SECRET_TOKEN,
        'ENVIRONMENT': os.getenv("ELASTIC_APM_ENVIRONMENT", "production"),
    }
    if APM_SERVER_URL and APM_SECRET_TOKEN:
        apm_client = make_apm_client(apm_config)
    else:
        apm_client = None
except ImportError:
    apm_client = None

load_dotenv()

app = FastAPI()
if apm_client:
    app.add_middleware(ElasticAPM, client=apm_client)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Logging setup for Elastic
if os.getenv("ELASTIC_APM_LOGGING", "false").lower() == "true":
    from elasticapm.handlers.logging import LoggingHandler
    handler = LoggingHandler(client=apm_client) if apm_client else None
    if handler:
        logging.basicConfig(level=logging.INFO, handlers=[handler])
    else:
        logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("product-owner-copilot")

OLLAMA_MODEL = os.getenv("LLM_MODEL", "mistral-small:latest")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
LLM_STATUS_FILE = "llm.status"

def convert_messages_to_prompt(messages):
    return "\n".join([m["content"] for m in messages if m["role"] == "user"])

async def is_llm_offline():
    try:
        async with aiofiles.open(LLM_STATUS_FILE, mode="r", encoding="utf-8") as f:
            status = (await f.read()).strip().lower()
            return "offline" in status
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.error(f"Error reading LLM status file: {e}")
        return False

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/stream_result")
async def stream_result(prompt: str, template: str = "pbi"):
    if await is_llm_offline():
        async def offline_stream():
            yield "LLM is offline"
        return StreamingResponse(offline_stream(), media_type="text/plain")
    logger.info(f"Received prompt for template '{template}'")
    pbi_template_path = os.getenv("PBI_TEMPLATE_PATH", "static/pbi_template.txt")
    product_goal_template_path = os.getenv("PRODUCT_GOAL_TEMPLATE_PATH", "static/product_goal_template.txt")
    po_review_template_path = os.getenv("PO_REVIEW_TEMPLATE", "static/po_review_template.txt")
    if template == "product_goal":
        template_path = product_goal_template_path
    elif template == "po_review":
        template_path = po_review_template_path
    else:
        template_path = pbi_template_path
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    except FileNotFoundError:
        logger.error(f"Template file not found: {template_path}")
        async def error_stream():
            yield "Error: template file not found."
        return StreamingResponse(error_stream(), media_type="text/plain")
    ollama_prompt = f"As an expert product owner in the observability team, use the following template:\n---\n{template_content}\n---\nFill in the details based on this information:\n---\n{prompt}\n---"
    messages = [{"role": "user", "content": ollama_prompt}]
    async def stream_generator():
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": convert_messages_to_prompt(messages),
            "stream": True
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", OLLAMA_API_URL, json=payload) as response:
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
                            logger.error(f"Streaming error: {str(e)}")
                            yield f"\n[Streaming error: {str(e)}]\n"
                            break
        except Exception as e:
            logger.error(f"HTTPX error: {str(e)}")
            yield f"\n[HTTPX error: {str(e)}]\n"
    return StreamingResponse(stream_generator(), media_type="text/plain")

@app.post("/api/azdo-process")
async def AZDO_process(request: Request):
    if await is_llm_offline():
        return {"error": "LLM is offline"}
    data = await request.json()
    logger.info(f"Received AZDO process request: {data}")
    # Process the request data as needed
    return {"status": "success", "data": data}

@app.get("/llm_status")
async def llm_status():
    offline = await is_llm_offline()
    return {"status": "offline" if offline else "online"}

# Elasticsearch logging handler
class ElasticsearchHandler(logging.Handler):
    def __init__(self, es_client, index_name):
        super().__init__()
        self.es_client = es_client
        self.index_name = index_name
        self._emit_guard = False  # Prevent recursion
    def emit(self, record):
        if self._emit_guard:
            return
        self._emit_guard = True
        try:
            log_entry = self.format(record)
            doc = {
                "@timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": log_entry,
                "pathname": record.pathname,
                "lineno": record.lineno,
                "funcName": record.funcName,
            }
            # Do NOT set Accept/Content-Type headers; let elasticsearch-py handle it
            self.es_client.index(index=self.index_name, document=doc)
        except Exception as e:
            # Print to stderr to avoid recursion
            import sys
            print(f"[Elasticsearch Logging Error] {e}", file=sys.stderr)
        finally:
            self._emit_guard = False

# Setup Elasticsearch logging if ES_INDEX_NAME and ES_CLOUD_ID/API_KEY are present
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME")
ES_CLOUD_ID = os.getenv("ES_CLOUD_ID")
ES_API_KEY = os.getenv("ES_API_KEY")

if ES_INDEX_NAME and ES_CLOUD_ID and ES_API_KEY:
    es_client = Elasticsearch(
        cloud_id=ES_CLOUD_ID,
        api_key=ES_API_KEY
    )
    es_handler = ElasticsearchHandler(es_client, ES_INDEX_NAME)
    es_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    es_handler.setFormatter(formatter)
    # Use a dedicated logger for ES to avoid recursion
    es_logger = logging.getLogger("es-logger")
    es_logger.addHandler(es_handler)
    es_logger.propagate = False
    # Add a filter to main logger to also log to ES
    class ESLogFilter(logging.Filter):
        def filter(self, record):
            es_logger.handle(record)
            return True
    logger = logging.getLogger("product-owner-copilot")
    logger.addFilter(ESLogFilter())
else:
    logger = logging.getLogger("product-owner-copilot")
