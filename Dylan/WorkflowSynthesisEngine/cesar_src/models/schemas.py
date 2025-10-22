
import uuid as _uuid
from typing import List as _List, Optional as _Optional
from pydantic import BaseModel as _BaseModel, Field as _Field, field_validator as _field_validator, model_validator as _model_validator
import networkx as _nx

class ConditionalLogic(_BaseModel):
    condition: str = _Field(..., description="Predicate determining branching")
    true_path_task_id: str = _Field(...)
    false_path_task_id: _Optional[str] = _Field(None)

class KnowledgeItem(_BaseModel):
    id: str
    description: str

class SkillItem(_BaseModel):
    id: str
    description: str

class TaskObject(_BaseModel):
    task_id: str = _Field(default_factory=lambda: str(_uuid.uuid4()))
    task_description: str
    role_owner: str
    precedes_tasks: _List[str] = _Field(default_factory=list)
    dependencies: _List[str] = _Field(default_factory=list)
    conditional_logic: _Optional[ConditionalLogic] = None
    required_knowledge: _List[KnowledgeItem] = _Field(default_factory=list)
    required_skill_tags: _List[SkillItem] = _Field(default_factory=list)

class JobWorkflowSchema(_BaseModel):
    workflow_name: str
    tasks: _List[TaskObject]

    @_field_validator("tasks")
    @classmethod
    def _validate_refs(cls, tasks: _List[TaskObject]) -> _List[TaskObject]:
        ids = {t.task_id for t in tasks}
        for t in tasks:
            for d in t.dependencies:
                if d not in ids:
                    raise ValueError(f"Dependency '{d}' not found")
            for n in t.precedes_tasks:
                if n not in ids:
                    raise ValueError(f"Successor '{n}' not found")
        return tasks

    @_model_validator(mode="after")
    def _validate_dag(self) -> "JobWorkflowSchema":
        G = _nx.DiGraph()
        for t in self.tasks:
            G.add_node(t.task_id)
        for t in self.tasks:
            for n in t.precedes_tasks:
                G.add_edge(t.task_id, n)
            if t.conditional_logic:
                G.add_edge(t.task_id, t.conditional_logic.true_path_task_id)
                if t.conditional_logic.false_path_task_id:
                    G.add_edge(t.task_id, t.conditional_logic.false_path_task_id)
        if not _nx.is_directed_acyclic_graph(G):
            raise ValueError("Workflow contains cycles")
        roots = [n for n, indeg in G.in_degree() if indeg == 0]
        if not roots:
            raise ValueError("No root task detected")
        return self
