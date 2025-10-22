
import os as _os
from dataclasses import dataclass as _dataclass, field as _field
from typing import Dict as _Dict, Optional as _Optional
import yaml as _yaml

class ConfigError(Exception):
    pass

@_dataclass(frozen=True)
class LLMEndpoint:
    name: str
    base_url: str
    model: str
    api_key_env: str
    def api_key(self) -> _Optional[str]:
        return _os.environ.get(self.api_key_env) if self.api_key_env else None

@_dataclass(frozen=True)
class AppConfig:
    environment: str
    database_url: str
    llm_endpoints: _Dict[str, LLMEndpoint] = _field(default_factory=dict)
    primary_endpoint: str = "remote"
    living_data_brain_db: _Optional[str] = None
    master_job_tree_root: _Optional[str] = None
    autogen_creator_path: _Optional[str] = None
    autogen_workflows_dir: _Optional[str] = None
    skill_node_registry: _Optional[str] = None
    automation_matrix_root: _Optional[str] = None

    @staticmethod
    def load(path: str) -> "AppConfig":
        with open(path, "r", encoding="utf-8") as f:
            raw = _yaml.safe_load(f)
        try:
            llms = {
                k: LLMEndpoint(
                    name=k,
                    base_url=v["base_url"],
                    model=v["model"],
                    api_key_env=v.get("api_key_env", ""),
                )
                for k, v in raw["llm_endpoints"].items()
            }
            cfg = AppConfig(
                environment=str(raw["environment"]),
                database_url=str(raw["database_url"]),
                llm_endpoints=llms,
                primary_endpoint=str(raw.get("primary_endpoint", "remote")),
                living_data_brain_db=raw.get("living_data_brain_db"),
                master_job_tree_root=raw.get("master_job_tree_root"),
                autogen_creator_path=raw.get("autogen_creator_path"),
                autogen_workflows_dir=raw.get("autogen_workflows_dir"),
                skill_node_registry=raw.get("skill_node_registry"),
                automation_matrix_root=raw.get("automation_matrix_root"),
            )
        except Exception as e:
            raise ConfigError(f"Invalid config: {e}") from e
        if cfg.primary_endpoint not in cfg.llm_endpoints:
            raise ConfigError("primary_endpoint not found in llm_endpoints")
        return cfg
