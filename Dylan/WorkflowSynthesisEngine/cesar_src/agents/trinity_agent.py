
from ..services.llm_router import LLMRouter
from .jury_agent import JuryAgent

class TrinityAgent:
    """Neural triangulation across endpoints with Jury synthesis."""
    def __init__(self, router: LLMRouter, jury: JuryAgent):
        self.router = router
        self.jury = jury
    async def run(self, payload: dict) -> dict:
        prompt = payload["prompt"]
        endpoints = payload.get("endpoints") or list(self.router.cfg.llm_endpoints.keys())
        answers = []
        for ep in endpoints:
            ans = await self.router.chat(endpoint=ep, messages=[{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1200)
            answers.append(ans)
        verdict = await self.jury.run({"candidates": answers, "endpoint": payload.get("endpoint", None)})
        return {"answers": answers, "verdict": verdict}
