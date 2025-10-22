"""
Parameter manager for validating, converting, and managing script parameters.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json

from .script_registry import ScriptParameter
from .logger import get_logger

logger = get_logger(__name__)


class ParameterValidationError(Exception):
    """Raised when parameter validation fails."""
    pass


class ParameterManager:
    """Manages parameter validation, conversion, and command-line generation."""
    
    @staticmethod
    def validate_parameter(param: ScriptParameter, value: Any) -> Any:
        """
        Validate and convert a parameter value according to its specification.
        
        Args:
            param: Parameter specification
            value: Value to validate
            
        Returns:
            Validated and converted value
            
        Raises:
            ParameterValidationError: If validation fails
        """
        # Check required
        if param.required and (value is None or value == ""):
            raise ParameterValidationError(
                f"Parameter '{param.name}' is required but not provided"
            )
        
        # Use default if not provided
        if value is None or value == "":
            return param.default
        
        # Type conversion and validation
        try:
            if param.type == 'string':
                converted = str(value)
            
            elif param.type == 'int':
                converted = int(value)
                if param.min_value is not None and converted < param.min_value:
                    raise ParameterValidationError(
                        f"Parameter '{param.name}' must be >= {param.min_value}"
                    )
                if param.max_value is not None and converted > param.max_value:
                    raise ParameterValidationError(
                        f"Parameter '{param.name}' must be <= {param.max_value}"
                    )
            
            elif param.type == 'float':
                converted = float(value)
                if param.min_value is not None and converted < param.min_value:
                    raise ParameterValidationError(
                        f"Parameter '{param.name}' must be >= {param.min_value}"
                    )
                if param.max_value is not None and converted > param.max_value:
                    raise ParameterValidationError(
                        f"Parameter '{param.name}' must be <= {param.max_value}"
                    )
            
            elif param.type == 'bool':
                if isinstance(value, bool):
                    converted = value
                elif isinstance(value, str):
                    converted = value.lower() in ('true', 'yes', '1', 'on')
                else:
                    converted = bool(value)
            
            elif param.type == 'file':
                path = Path(value)
                if not path.exists():
                    raise ParameterValidationError(
                        f"File not found: {value}"
                    )
                if not path.is_file():
                    raise ParameterValidationError(
                        f"Path is not a file: {value}"
                    )
                converted = str(path.absolute())
            
            elif param.type == 'directory':
                path = Path(value)
                if not path.exists():
                    raise ParameterValidationError(
                        f"Directory not found: {value}"
                    )
                if not path.is_dir():
                    raise ParameterValidationError(
                        f"Path is not a directory: {value}"
                    )
                converted = str(path.absolute())
            
            elif param.type == 'choice':
                if param.choices is None or len(param.choices) == 0:
                    raise ParameterValidationError(
                        f"No choices defined for parameter '{param.name}'"
                    )
                if value not in param.choices:
                    raise ParameterValidationError(
                        f"Parameter '{param.name}' must be one of: {param.choices}"
                    )
                converted = value
            
            else:
                raise ParameterValidationError(
                    f"Unknown parameter type: {param.type}"
                )
            
            return converted
            
        except (ValueError, TypeError) as e:
            raise ParameterValidationError(
                f"Failed to convert parameter '{param.name}' to {param.type}: {e}"
            )
    
    @staticmethod
    def validate_parameters(
        parameters: List[ScriptParameter],
        values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate all parameters for a script.
        
        Args:
            parameters: List of parameter specifications
            values: Dictionary of parameter values
            
        Returns:
            Dictionary of validated parameter values
            
        Raises:
            ParameterValidationError: If any validation fails
        """
        validated = {}
        
        for param in parameters:
            value = values.get(param.name)
            validated[param.name] = ParameterManager.validate_parameter(param, value)
        
        return validated
    
    @staticmethod
    def build_command_args(
        parameters: List[ScriptParameter],
        values: Dict[str, Any],
        style: str = 'posix'
    ) -> List[str]:
        """
        Build command-line arguments from parameters.
        
        Args:
            parameters: List of parameter specifications
            values: Dictionary of validated parameter values
            style: Argument style ('posix' for --name=value, 'simple' for positional)
            
        Returns:
            List of command-line arguments
        """
        args = []
        
        for param in parameters:
            value = values.get(param.name)
            
            # Skip if value is None or default
            if value is None:
                continue
            
            if style == 'posix':
                # POSIX-style: --name=value
                if param.type == 'bool':
                    if value:
                        args.append(f"--{param.name}")
                else:
                    args.append(f"--{param.name}={value}")
            
            elif style == 'simple':
                # Simple positional arguments
                if param.type == 'bool':
                    if value:
                        args.append(str(value).lower())
                else:
                    args.append(str(value))
            
            elif style == 'json':
                # Single JSON argument
                continue  # Handled separately
        
        return args
    
    @staticmethod
    def build_json_args(values: Dict[str, Any]) -> str:
        """
        Build a JSON string from parameter values.
        
        Args:
            values: Dictionary of validated parameter values
            
        Returns:
            JSON string
        """
        return json.dumps(values, ensure_ascii=False)
    
    @staticmethod
    def save_parameter_preset(
        preset_name: str,
        script_id: str,
        values: Dict[str, Any]
    ) -> bool:
        """
        Save a parameter preset for later use.
        
        Args:
            preset_name: Name of the preset
            script_id: Script ID
            values: Parameter values
            
        Returns:
            True if saved successfully
        """
        preset_dir = Path.home() / 'script_launcher' / 'config' / 'presets'
        preset_dir.mkdir(parents=True, exist_ok=True)
        
        preset_file = preset_dir / f"{script_id}_{preset_name}.json"
        
        try:
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(values, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved parameter preset: {preset_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save parameter preset: {e}")
            return False
    
    @staticmethod
    def load_parameter_preset(preset_name: str, script_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a saved parameter preset.
        
        Args:
            preset_name: Name of the preset
            script_id: Script ID
            
        Returns:
            Parameter values or None if not found
        """
        preset_file = Path.home() / 'script_launcher' / 'config' / 'presets' / f"{script_id}_{preset_name}.json"
        
        if not preset_file.exists():
            return None
        
        try:
            with open(preset_file, 'r', encoding='utf-8') as f:
                values = json.load(f)
            logger.info(f"Loaded parameter preset: {preset_name}")
            return values
        except Exception as e:
            logger.error(f"Failed to load parameter preset: {e}")
            return None
    
    @staticmethod
    def list_presets(script_id: str) -> List[str]:
        """
        List all available presets for a script.
        
        Args:
            script_id: Script ID
            
        Returns:
            List of preset names
        """
        preset_dir = Path.home() / 'script_launcher' / 'config' / 'presets'
        if not preset_dir.exists():
            return []
        
        presets = []
        prefix = f"{script_id}_"
        
        for preset_file in preset_dir.glob(f"{prefix}*.json"):
            preset_name = preset_file.stem[len(prefix):]
            presets.append(preset_name)
        
        return sorted(presets)

