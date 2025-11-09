"""Core pipeline abstractions."""

from .context import Context, FileContext, NoteContext, MetaContext
from .stage import Stage, StageOptions, register_stage, get_stage, list_stages, get_stage_info
from .pipeline import Pipeline
from .config import load_pipeline_config, load_config_from_preset
from .helpers import read_file_content

__all__ = [
    "Context",
    "FileContext",
    "NoteContext",
    "MetaContext",
    "Stage",
    "StageOptions",
    "register_stage",
    "get_stage",
    "list_stages",
    "get_stage_info",
    "Pipeline",
    "load_pipeline_config",
    "load_config_from_preset",
    "read_file_content",
]
