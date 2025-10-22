
import os as _os2
from dataclasses import dataclass as _dataclass2
from typing import Dict as _Dict4, Optional as _Optional4
import yaml as _yaml2

class AutomationMatrixError(Exception):
    pass

@_dataclass2(frozen=True)
class Service:
    name: str
    base_url: str
    api_key_env: _Optional4[str]
    def api_key(self) -> _Optional4[str]:
        return _os2.environ.get(self.api_key_env) if self.api_key_env else None

@_dataclass2(frozen=True)
class WorkflowBinding:
    workflow: str
    service: str
    enabled: bool

@_dataclass2(frozen=True)
class AutomationMatrix:
    services: _Dict4[str, Service]
    bindings: _Dict4[str, WorkflowBinding]

    @staticmethod
    def load(path: str) -> "AutomationMatrix":
        with open(path, "r", encoding="utf-8") as f:
            raw = _yaml2.safe_load(f)
        try:
            services = {
                name: Service(name=name, base_url=v["base_url"], api_key_env=v.get("api_key_env", None))
                for name, v in raw["services"].items()
            }
            bindings = {
                b["workflow"]: WorkflowBinding(
                    workflow=b["workflow"], service=b["service"], enabled=bool(b.get("enabled", True))
                )
                for b in raw["bindings"]
            }
        except Exception as e:
            raise AutomationMatrixError(f"Invalid automation matrix: {e}") from e
        for wf, bind in bindings.items():
            if bind.service not in services:
                raise AutomationMatrixError(f"Binding references unknown service '{bind.service}' for workflow '{wf}'")
        return AutomationMatrix(services=services, bindings=bindings)

    def service_for(self, workflow_name: str) -> Service:
        if workflow_name not in self.bindings:
            raise AutomationMatrixError(f"No binding for workflow '{workflow_name}'")
        b = self.bindings[workflow_name]
        if not b.enabled:
            raise AutomationMatrixError(f"Binding for workflow '{workflow_name}' is disabled")
        return self.services[b.service]
