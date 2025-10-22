# Validates SQLAlchemy ORM annotations (Mapped[...] and mapped_column) are correctly interpreted
from cesar_src.models.db import make_session, WorkflowModel
from cesar_src.models.schemas import JobWorkflowSchema, TaskObject
from cesar_src.models.repository import WorkflowRepository

def test_db_persist_roundtrip(tmp_path):
    db_path = tmp_path / "e2e.db"
    Session = make_session(f"sqlite:///{db_path}")
    repo = WorkflowRepository(Session)

    t1 = TaskObject(task_id="X1", task_description="Start", role_owner="Owner")
    t2 = TaskObject(task_id="X2", task_description="Next", role_owner="Owner", dependencies=["X1"])
    wf = JobWorkflowSchema(workflow_name="WF_DB", tasks=[t1, t2])

    wid = repo.save(wf.workflow_name, wf, mermaid_code="graph TD\nX1-->X2")
    model = repo.get(wid)
    assert isinstance(model, WorkflowModel)
    assert model.name == "WF_DB"
    assert "mermaid" not in model.json_data  # ensure schema persisted as JSON dict
