
from ..models.schemas import JobWorkflowSchema

class ValidatorAgent:
    name = "validator"

    async def run(self, payload: dict) -> dict:
        wf: JobWorkflowSchema = payload["workflow"]
        _ = JobWorkflowSchema(**wf.model_dump())
        return {"valid": True}
