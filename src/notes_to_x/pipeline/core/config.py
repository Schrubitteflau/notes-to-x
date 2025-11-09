"""Pipeline configuration loading and validation."""

import os
from typing import Any

import yaml
from jinja2 import Template


def load_pipeline_config(config_path: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Load and parse pipeline configuration from YAML file.

    Supports Jinja2 templating for variable substitution.

    Args:
        config_path: Path to YAML config file
        variables: Dictionary of variables for template substitution

    Returns:
        Parsed configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        config_content = f.read()

    # Apply Jinja2 templating if variables provided
    if variables is None:
        variables = {}

    template = Template(config_content)
    config_content = template.render(
        **variables,
        env=os.environ,  # Allow access to environment variables
    )

    # Parse YAML
    config = yaml.safe_load(config_content)

    # Validate basic structure
    validate_config(config)

    return config


def validate_config(config: dict[str, Any]):
    """
    Validate pipeline configuration structure.

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If configuration is invalid
    """
    if not isinstance(config, dict):
        raise ValueError("Config must be a dictionary")

    # Required top-level keys
    if "pipeline" not in config:
        raise ValueError("Config must have 'pipeline' key")

    # Validate pipeline structure
    pipeline = config["pipeline"]
    if not isinstance(pipeline, list):
        raise ValueError("'pipeline' must be a list of stages")

    # Validate each stage definition
    for i, stage_def in enumerate(pipeline):
        if not isinstance(stage_def, dict):
            raise ValueError(f"Stage {i} must be a dictionary")

        if "kind" not in stage_def:
            raise ValueError(f"Stage {i} missing 'kind' field")

        # 'options' is optional, but must be a dict if present
        if "options" in stage_def and not isinstance(stage_def["options"], dict):
            raise ValueError(f"Stage {i} 'options' must be a dictionary")


def load_config_from_preset(preset_name: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Load pipeline config from preset name.

    Looks for config in src/notes_to_x/pipeline/presets/<preset_name>.yaml

    Args:
        preset_name: Name of the preset (without .yaml extension)
        variables: Dictionary of variables for template substitution

    Returns:
        Parsed configuration dictionary

    Raises:
        FileNotFoundError: If preset file doesn't exist
    """
    # Get presets directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    presets_dir = os.path.join(os.path.dirname(current_dir), "presets")

    # Add .yaml extension if not present
    if not preset_name.endswith(".yaml"):
        preset_name = f"{preset_name}.yaml"

    config_path = os.path.join(presets_dir, preset_name)

    return load_pipeline_config(config_path, variables)
