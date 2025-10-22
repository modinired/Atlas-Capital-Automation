
import pytest
from cesar_src.models.schemas import JobWorkflowSchema, TaskObject

def test_cycle_detection_raises():
    t1 = TaskObject(task_id="A", task_description="A", role_owner="r", precedes_tasks=["B"])
    t2 = TaskObject(task_id="B", task_description="B", role_owner="r", precedes_tasks=["A"])
    with pytest.raises(ValueError):
        JobWorkflowSchema(workflow_name="Cycle", tasks=[t1, t2])

def test_missing_ref_raises():
    t1 = TaskObject(task_id="A", task_description="A", role_owner="r", precedes_tasks=["Z"])  # Z not present
    with pytest.raises(ValueError):
        JobWorkflowSchema(workflow_name="BadRefs", tasks=[t1])
