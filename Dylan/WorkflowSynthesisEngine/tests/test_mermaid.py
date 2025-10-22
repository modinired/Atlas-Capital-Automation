from cesar_src.models.schemas import JobWorkflowSchema, TaskObject
from cesar_src.services.mermaid import Mermaid

def test_mermaid_basic():
    t = TaskObject(task_id="T1", task_description="Do a thing", role_owner="Role")
    wf = JobWorkflowSchema(workflow_name="WF", tasks=[t])
    code = Mermaid.render(wf)
    assert code.startswith("graph TD")
    assert "T1" in code
    assert "\n" in code

def test_mermaid_escapes_quotes_and_newlines():
    desc = 'Say "hello" and\nthen continue'
    t = TaskObject(task_id="T2", task_description=desc, role_owner="Mgr")
    wf = JobWorkflowSchema(workflow_name="WF2", tasks=[t])
    code = Mermaid.render(wf)
    assert 'T2(["' in code
    assert '<sub>Mgr</sub>' in code
