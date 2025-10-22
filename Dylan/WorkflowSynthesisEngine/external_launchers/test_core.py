"""
Test script to verify core functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    get_registry, get_engine, get_logger,
    ScriptMetadata, ScriptParameter, ParameterManager
)

logger = get_logger(__name__)


def test_registry():
    """Test script registry."""
    logger.info("Testing script registry...")
    
    registry = get_registry()
    
    # Create test script metadata
    metadata = ScriptMetadata(
        id="",
        name="Test Script",
        path=str(Path(__file__).parent.parent / "scripts" / "hello_world.py"),
        description="A test script for verification",
        parameters=[
            ScriptParameter(
                name="test_param",
                type="string",
                description="A test parameter",
                required=False,
                default="test_value"
            )
        ],
        tags=["test", "verification"]
    )
    
    # Register script
    script_id = registry.register_script(metadata)
    logger.info(f"Registered test script with ID: {script_id}")
    
    # Retrieve script
    script = registry.get_script(script_id)
    assert script is not None, "Failed to retrieve registered script"
    assert script.name == "Test Script", "Script name mismatch"
    
    logger.info("✓ Registry test passed")
    
    return script_id


def test_parameter_manager():
    """Test parameter manager."""
    logger.info("Testing parameter manager...")
    
    param_manager = ParameterManager()
    
    # Test parameter validation
    param = ScriptParameter(
        name="age",
        type="int",
        description="Age parameter",
        required=True,
        min_value=0,
        max_value=150
    )
    
    # Valid value
    validated = param_manager.validate_parameter(param, "25")
    assert validated == 25, "Parameter validation failed"
    
    # Test command args building
    parameters = [
        ScriptParameter(name="name", type="string", description="Name", required=True),
        ScriptParameter(name="verbose", type="bool", description="Verbose", required=False)
    ]
    
    values = {"name": "John", "verbose": True}
    args = param_manager.build_command_args(parameters, values, style='posix')
    
    assert "--name=John" in args, "Command args building failed"
    assert "--verbose" in args, "Boolean parameter handling failed"
    
    logger.info("✓ Parameter manager test passed")


def test_launcher_engine(script_id):
    """Test launcher engine."""
    logger.info("Testing launcher engine...")
    
    engine = get_engine()
    
    # Quick launch test
    test_script = Path(__file__).parent.parent / "scripts" / "hello_world.py"
    
    if test_script.exists():
        logger.info(f"Quick launching: {test_script}")
        result = engine.quick_launch(str(test_script))
        
        assert result is not None, "Quick launch failed"
        logger.info(f"Exit code: {result.exit_code}")
        logger.info(f"Status: {result.status.value}")
        
        if result.stdout:
            logger.info(f"Output: {result.stdout[:100]}")
    
    logger.info("✓ Launcher engine test passed")


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Starting core functionality tests")
    logger.info("=" * 60)
    
    try:
        script_id = test_registry()
        test_parameter_manager()
        test_launcher_engine(script_id)
        
        logger.info("=" * 60)
        logger.info("✓ All tests passed!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

