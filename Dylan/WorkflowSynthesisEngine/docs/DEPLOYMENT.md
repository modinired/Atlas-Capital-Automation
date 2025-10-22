
# Deployment

## Python Environment
- Python >= 3.10
- Install via `pip install -e .[audio,export]` as needed.

## Local LLMs
Run local models behind OpenAI-compatible servers (examples):
- Ollama: `ollama serve` and `ollama run <model>` with an OpenAI-compatible adapter.
- LM Studio: enable the OpenAI API server and set `base_url` accordingly.
- vLLM or llama.cpp server: start with OpenAI-compatible REST enabled.

## Remote LLM
Provide `base_url=https://api.openai.com/v1`, `model=<deployed model>`, and set `OPENAI_API_KEY` in the environment.

## Database
Set `database_url` to a production-grade RDBMS (for example, Postgres). The repository is SQLAlchemy-agnostic and will create schema automatically.
