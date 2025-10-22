from typing import List as _List
from ..models.schemas import JobWorkflowSchema

class Mermaid:
    @staticmethod
    def _sanitize(text: str, max_len: int = 120) -> str:
        t = (text or "").replace("\n", " ").replace('"', "'")
        return (t[: max_len - 1] + "...") if len(t) > max_len else t

    @classmethod
    def render(cls, workflow: JobWorkflowSchema) -> str:
        lines: _List[str] = ["graph TD"]
        for t in workflow.tasks:
            role = t.role_owner or "role?"
            label = cls._sanitize(t.task_description)
            lines.append(f'    {t.task_id}(["{label}\n<sub>{role}</sub>"])')
        for t in workflow.tasks:
            for nxt in t.precedes_tasks:
                lines.append(f'    {t.task_id} --> {nxt}')
            if t.conditional_logic:
                c = t.conditional_logic
                lines.append(f'    {t.task_id} -- "{cls._sanitize(c.condition, 60)}" --> {c.true_path_task_id}')
                if c.false_path_task_id:
                    lines.append(f'    {t.task_id} -- "Else" --> {c.false_path_task_id}')
        dec = [t.task_id for t in workflow.tasks if t.conditional_logic]
        if dec:
            lines.append('    classDef decisionNode fill:#ffe4b5,stroke:#333;')
            for n in dec:
                lines.append(f'    class {n} decisionNode;')
        return "\n".join(lines)
