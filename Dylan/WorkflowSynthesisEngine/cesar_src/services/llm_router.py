
from typing import Dict as _Dict2, Any as _Any2
import httpx as _httpx
from ..config import AppConfig, LLMEndpoint

class LLMRouterError(Exception):
    pass

class LLMRouter:
    """Routes chat-completion calls across multiple OpenAI-compatible endpoints."""

    def __init__(self, config: AppConfig):
        self.cfg = config

    async def chat(self, *, endpoint: str | None, messages: list[dict[str, str]], temperature: float = 0.1, max_tokens: int = 4096) -> str:
        name = endpoint or self.cfg.primary_endpoint
        if name not in self.cfg.llm_endpoints:
            raise LLMRouterError(f"Unknown endpoint '{name}'")
        ep = self.cfg.llm_endpoints[name]
        return await self._openai_compatible_chat(ep, messages, temperature, max_tokens)

    async def _openai_compatible_chat(self, ep: LLMEndpoint, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
        url = ep.base_url.rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        api_key = ep.api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload: _Dict2[str, _Any2] = {
            "model": ep.model,
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }
        async with _httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code >= 400:
                raise LLMRouterError(f"{ep.name} error {r.status_code}: {r.text}")
            data = r.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception as e:  # noqa: BLE001
            raise LLMRouterError(f"Malformed response from {ep.name}: {data}") from e
        return content
