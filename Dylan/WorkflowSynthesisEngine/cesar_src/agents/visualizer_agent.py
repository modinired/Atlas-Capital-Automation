
from ..services.mermaid import Mermaid
from ..models.schemas import JobWorkflowSchema

class VisualizerAgent:
    name = "visualizer"

    async def run(self, payload: dict) -> dict:
        wf: JobWorkflowSchema = payload["workflow"]
        code = Mermaid.render(wf)
        return {"mermaid": code}
