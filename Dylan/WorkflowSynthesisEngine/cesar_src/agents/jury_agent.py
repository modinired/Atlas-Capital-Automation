
import json as _json3
from ..services.llm_router import LLMRouter

CRITIC_PROMPT = (
    "You are the Jury Agent. Given N candidate answers, 1) identify agreement/disagreement, 2) rate each (1-10) on factuality, completeness, safety, 3) propose a final synthesized answer with citations to candidate #s. Respond as JSON with keys: ratings (list), issues (list), final_answer (string)."
)

class JuryAgent:
    name = "jury"
    def __init__(self, router: LLMRouter):
        self.router = router
    async def run(self, payload: dict) -> dict:
        candidates: list[str] = payload["candidates"]
        structured = "\n\n".join([f"Candidate #{i+1}:\n{c}" for i, c in enumerate(candidates)])
        msg = f"{CRITIC_PROMPT}\n\n{structured}"
        out = await self.router.chat(endpoint=payload.get("endpoint", None), messages=[{"role": "user", "content": msg}], temperature=0.1, max_tokens=2000)
        data = _json3.loads(out)
        return data
