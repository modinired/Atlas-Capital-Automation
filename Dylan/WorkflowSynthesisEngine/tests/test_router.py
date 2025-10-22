
import os, pytest
from cesar_src.config import AppConfig
from cesar_src.services.llm_router import LLMRouter

CONFIG_SCHEMA = {
    "environment": "dev",
    "database_url": "sqlite:///test.db",
    "llm_endpoints": {
        "local1": {"base_url": "http://127.0.0.1:11434/v1", "model": "qwen2.5:7b", "api_key_env": ""},
        "local2": {"base_url": "http://127.0.0.1:8000/v1", "model": "llama3.1:8b", "api_key_env": ""},
        "remote": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "api_key_env": "OPENAI_API_KEY"},
    },
    "primary_endpoint": "remote",
}

def test_config_loads(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(__import__("yaml").safe_dump(CONFIG_SCHEMA), encoding="utf-8")
    cfg = AppConfig.load(str(p))
    assert cfg.primary_endpoint == "remote"
    assert "local1" in cfg.llm_endpoints

@pytest.mark.integration
@pytest.mark.skipif("OPENAI_API_KEY" not in os.environ, reason="requires OPENAI_API_KEY")
@pytest.mark.timeout(30)
async def test_router_remote_chat_roundtrip(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(__import__("yaml").safe_dump(CONFIG_SCHEMA), encoding="utf-8")
    cfg = AppConfig.load(str(p))
    router = LLMRouter(cfg)
    out = await router.chat(endpoint="remote", messages=[{"role": "user", "content": "Say 'ok'"}], temperature=0.0, max_tokens=5)
    assert "ok".lower() in out.lower()
