"""
Script registry for managing Python scripts, their metadata, and configurations.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
import hashlib
import threading

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScriptParameter:
    """Represents a script parameter configuration."""
    name: str
    type: str  # 'string', 'int', 'float', 'bool', 'file', 'directory', 'choice'
    description: str
    default: Any = None
    required: bool = False
    choices: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScriptParameter':
        return cls(**data)


@dataclass
class ScriptMetadata:
    """Complete metadata for a registered script."""
    id: str
    name: str
    path: str
    description: str
    parameters: List[ScriptParameter] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    author: str = ""
    version: str = "1.0.0"
    python_version: str = "3.11"
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[int] = None  # seconds
    working_directory: Optional[str] = None
    environment_variables: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_run: Optional[str] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    enabled: bool = True
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['parameters'] = [p.to_dict() for p in self.parameters]
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScriptMetadata':
        params = data.pop('parameters', [])
        metadata = cls(**data)
        metadata.parameters = [ScriptParameter.from_dict(p) for p in params]
        return metadata
    
    def update_stats(self, success: bool):
        """Update execution statistics."""
        self.run_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.last_run = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


class ScriptRegistry:
    """
    Central registry for managing all registered scripts.
    Thread-safe singleton implementation.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.config_dir = Path.home() / 'script_launcher' / 'config'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.config_dir / 'registry.json'
        
        self.scripts: Dict[str, ScriptMetadata] = {}
        self._load_registry()
        
        logger.info(f"Script registry initialized with {len(self.scripts)} scripts")
    
    def _generate_script_id(self, script_path: str) -> str:
        """Generate a unique ID for a script based on its path."""
        return hashlib.md5(script_path.encode()).hexdigest()[:12]
    
    def _load_registry(self):
        """Load registry from disk."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.scripts = {
                        script_id: ScriptMetadata.from_dict(script_data)
                        for script_id, script_data in data.items()
                    }
                logger.info(f"Loaded {len(self.scripts)} scripts from registry")
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
                self.scripts = {}
    
    def _save_registry(self):
        """Save registry to disk."""
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                data = {
                    script_id: metadata.to_dict()
                    for script_id, metadata in self.scripts.items()
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug("Registry saved successfully")
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def register_script(self, metadata: ScriptMetadata) -> str:
        """
        Register a new script or update existing one.
        
        Args:
            metadata: Script metadata
            
        Returns:
            Script ID
        """
        with self._lock:
            script_id = metadata.id or self._generate_script_id(metadata.path)
            metadata.id = script_id
            metadata.updated_at = datetime.now().isoformat()
            
            if script_id in self.scripts:
                logger.info(f"Updating script: {metadata.name} ({script_id})")
            else:
                logger.info(f"Registering new script: {metadata.name} ({script_id})")
            
            self.scripts[script_id] = metadata
            self._save_registry()
            return script_id
    
    def unregister_script(self, script_id: str) -> bool:
        """Remove a script from the registry."""
        with self._lock:
            if script_id in self.scripts:
                script_name = self.scripts[script_id].name
                del self.scripts[script_id]
                self._save_registry()
                logger.info(f"Unregistered script: {script_name} ({script_id})")
                return True
            return False
    
    def get_script(self, script_id: str) -> Optional[ScriptMetadata]:
        """Get script metadata by ID."""
        return self.scripts.get(script_id)
    
    def get_all_scripts(self) -> List[ScriptMetadata]:
        """Get all registered scripts."""
        return list(self.scripts.values())
    
    def get_enabled_scripts(self) -> List[ScriptMetadata]:
        """Get all enabled scripts."""
        return [s for s in self.scripts.values() if s.enabled]
    
    def search_scripts(self, query: str) -> List[ScriptMetadata]:
        """Search scripts by name, description, or tags."""
        query_lower = query.lower()
        results = []
        for script in self.scripts.values():
            if (query_lower in script.name.lower() or
                query_lower in script.description.lower() or
                any(query_lower in tag.lower() for tag in script.tags)):
                results.append(script)
        return results
    
    def get_scripts_by_tag(self, tag: str) -> List[ScriptMetadata]:
        """Get all scripts with a specific tag."""
        return [s for s in self.scripts.values() if tag in s.tags]
    
    def update_script_stats(self, script_id: str, success: bool):
        """Update script execution statistics."""
        with self._lock:
            if script_id in self.scripts:
                self.scripts[script_id].update_stats(success)
                self._save_registry()
    
    def toggle_script(self, script_id: str) -> bool:
        """Enable or disable a script."""
        with self._lock:
            if script_id in self.scripts:
                self.scripts[script_id].enabled = not self.scripts[script_id].enabled
                self._save_registry()
                return self.scripts[script_id].enabled
            return False
    
    def export_script_config(self, script_id: str, output_path: str) -> bool:
        """Export script configuration to a JSON file."""
        script = self.get_script(script_id)
        if script:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(script.to_dict(), f, indent=2, ensure_ascii=False)
                logger.info(f"Exported script config to {output_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to export script config: {e}")
        return False
    
    def import_script_config(self, config_path: str) -> Optional[str]:
        """Import script configuration from a JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                metadata = ScriptMetadata.from_dict(data)
                return self.register_script(metadata)
        except Exception as e:
            logger.error(f"Failed to import script config: {e}")
            return None


# Global registry instance
_registry = ScriptRegistry()


def get_registry() -> ScriptRegistry:
    """Get the global script registry instance."""
    return _registry

