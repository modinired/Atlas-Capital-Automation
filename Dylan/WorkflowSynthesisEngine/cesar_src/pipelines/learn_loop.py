
import json as _json4, time as _time
from ..brains.knowledge import KnowledgeBrain
from ..services.llm_router import LLMRouter

class LearnLoop:
    POLICY = (
        "You are a Reflection Agent. Given interaction logs (prompt, context snippets, outputs), extract: 1) stable facts, 2) hypothesized rules, 3) open questions, 4) follow-up actions. Return JSON with keys: facts, rules, questions, actions."
    )
    def __init__(self, kb: KnowledgeBrain, router: LLMRouter):
        self.kb = kb
        self.router = router
    async def record_and_reflect(self, *, doc_id: str, title: str, text: str, source: str, created_at: str) -> dict:
        self.kb.upsert([(doc_id, title, text, source, created_at)])
        out = await self.router.chat(endpoint=None, messages=[{"role": "system", "content": self.POLICY}, {"role": "user", "content": text}], temperature=0.1, max_tokens=1500)
        data = _json4.loads(out)
        rid = f"reflect:{doc_id}:{int(_time.time())}"
        self.kb.upsert([(rid, f"Reflection:{title}", _json4.dumps(data, ensure_ascii=False), source, created_at)])
        return data
