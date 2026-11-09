# Orbit — PDF RAG

Upload a PDF, retrieve relevant passages, and ask grounded questions from a Streamlit interface. The Streamlit app calls OpenAI directly and uses Qdrant for vector storage; it does not need a separate Inngest or FastAPI service.

## Run locally (Windows)

1. Put `OPENAI_API_KEY` in `.env`.
2. Start the local services:

   ```powershell
   .\start-local.ps1
   ```

3. Open <http://127.0.0.1:8501>.

The script starts Qdrant, FastAPI, Inngest, and Streamlit for local development. The Streamlit UI connects directly to the local Qdrant server. Logs and vector data are stored under `.local/`.

## Deploy to Streamlit Community Cloud

Community Cloud deploys apps from GitHub. Add this project to a GitHub repository, then create an app at <https://share.streamlit.io> using `streamlit_app.py` as the entrypoint. Select Python 3.14 in Advanced settings to match `.python-version`.

In the app's Secrets settings, add the contents of `.streamlit/secrets.toml.example` and replace `your-openai-api-key` with an API key that has available API credits. Never commit the real key. If `QDRANT_URL` is omitted, the app uses local embedded Qdrant storage, which is temporary on Community Cloud. For persistent data, provide a Qdrant Cloud URL and API key in the app secrets.

The app uses OpenAI embeddings and chat completions, so its API organization must have available credits. ChatGPT subscriptions do not include API usage credits.
