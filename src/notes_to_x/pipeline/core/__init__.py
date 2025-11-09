"""Core pipeline abstractions."""

from .config import load_config_from_preset, load_pipeline_config
from .context import Context, FileContext, MetaContext, NoteContext
from .helpers import read_file_content
from .pipeline import Pipeline
from .stage import Stage, StageOptions, get_stage, get_stage_info, list_stages, register_stage

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
