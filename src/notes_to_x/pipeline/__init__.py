"""
Pipeline-based processing system for notes-to-x.

This module provides a flexible, stage-based pipeline for transforming notes.
"""

# Import core components
# Import all stages to trigger registration
from . import stages  # noqa: F401
from .core import (
    Context,
    FileContext,
    MetaContext,
    NoteContext,
    Pipeline,
    Stage,
    get_stage,
    get_stage_info,
    list_stages,
    load_config_from_preset,
    load_pipeline_config,
    register_stage,
)

__all__ = [
    "Context",
    "FileContext",
    "NoteContext",
    "MetaContext",
    "Stage",
    "register_stage",
    "get_stage",
    "list_stages",
    "get_stage_info",
    "Pipeline",
    "load_pipeline_config",
    "load_config_from_preset",
]
