# Product Owner Copilot

Product Owner Copilot is a FastAPI-based web app for product owners to generate and stream LLM (Ollama) responses using customizable prompt templates. The app features a modern frontend with template selection and real-time streaming output.

## Features
- Select between PBI and Product Goal templates
- Enter your own prompt and stream the LLM response live
- Model selection via `.env` (`LLM_MODEL`)
- FastAPI backend with `/stream_result` endpoint for true streaming
- Simple, modern HTML frontend with word-wrapped textarea

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

## Project Structure
- `main.py` — FastAPI backend
- `static/index.html` — Main web UI
- `static/pbi_template.txt` — PBI prompt template
- `static/product_goal_template.txt` — Product Goal prompt template
- `static/style.css` — Stylesheet
- `.env` — Model selection

## Notes
- Requires Ollama to be running and the model to be pulled.
- For best streaming, use Uvicorn (not Flask or WSGI).
- All code and UI are designed for easy extension and customization.

---

**Product Owner Copilot** — Your AI-powered assistant for product backlog and goal management!
