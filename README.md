# Product Owner Copilot

Product Owner Copilot is a FastAPI-based web app for product owners to generate and stream LLM (Ollama) responses using customizable prompt templates. The app features a modern frontend with template selection and real-time streaming output.

## Features
- Select between PBI and Product Goal templates
- Enter your own prompt and stream the LLM response live
- Automatic review process: LLM output is reviewed using a second template and streamed to a second textarea
- Model and template selection via `.env` (`LLM_MODEL`, `PBI_TEMPLATE_PATH`, `PRODUCT_GOAL_TEMPLATE_PATH`, `PO_REVIEW_TEMPLATE`)
- Ollama API URL configurable via `.env` (`OLLAMA_API_URL`)
- FastAPI backend with `/stream_result` endpoint for true streaming
- Simple, modern HTML frontend with dual word-wrapped textareas (LLM Response & Review)
- Elastic APM and generic Elasticsearch logging integration (configurable via `.env`)

## Getting Started

1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
2. **Set your model in `.env`:**
   - Default: `mistral-small:latest`
3. **Run the server:**
   ```sh
   uvicorn main:app --reload
   ```
4. **Open the app:**
   - Go to [http://localhost:8000](http://localhost:8000) in your browser.

## Running as a systemd Service on Ubuntu

To run Product Owner Copilot as a background service on Ubuntu:

1. **Copy the service file:**
   Copy `product-owner-copilot.service` to your systemd directory:
   ```sh
   sudo cp /home/ubuntu/ProductOwnerCoPilot/product-owner-copilot.service /etc/systemd/system/
   ```

2. **Reload systemd:**
   ```sh
   sudo systemctl daemon-reload
   ```

3. **Enable the service to start on boot:**
   ```sh
   sudo systemctl enable product-owner-copilot
   ```

4. **Start the service:**
   ```sh
   sudo systemctl start product-owner-copilot
   ```

5. **Check service status and logs:**
   ```sh
   sudo systemctl status product-owner-copilot
   sudo journalctl -u product-owner-copilot -f
   ```

**Notes:**
- The service runs as user `ubuntu` and expects your app at `/home/ubuntu/ProductOwnerCoPilot`.
- The app will be available at port 5000 (http://<your-server-ip>:5000/).
- Ensure your virtual environment and dependencies are installed at `/home/ubuntu/ProductOwnerCoPilot/.venv/`.
- Update paths in the service file if your deployment directory is different.

## Project Structure
- `main.py` — FastAPI backend
- `static/index.html` — Main web UI (with dual textarea: LLM Response & Review)
- `static/pbi_template.txt` — PBI prompt template
- `static/product_goal_template.txt` — Product Goal prompt template
- `static/po_review_template.txt` — Review prompt template
- `static/style.css` — Stylesheet
- `.env` — Model, template, Ollama API, and logging configuration

## Notes
- Requires Ollama to be running and the model to be pulled.
- For best streaming, use Uvicorn (not Flask or WSGI).
- All code and UI are designed for easy extension and customization.
- Elastic APM and Elasticsearch logging are supported. Set `ELASTIC_APM_*` and `ES_*` variables in `.env` to enable telemetry and log shipping.

---

**Product Owner Copilot** — Your AI-powered assistant for product backlog and goal management!
