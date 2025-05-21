<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Copilot Instructions

- This project is a FastAPI-based Python backend for streaming LLM (Ollama) responses.
- Use python-dotenv to load environment variables from `.env`.
- The LLM model name should be read from the `.env` file as `LLM_MODEL`.
- The backend should provide a `/stream_result` endpoint that streams the LLM response.
- The frontend should use JavaScript to stream the response into a `<textarea>` with word wrap.
- Use only FastAPI and Uvicorn for serving the backend.
- Do not use Flask or WSGI for streaming endpoints.
- Use requirements.txt for dependencies.
