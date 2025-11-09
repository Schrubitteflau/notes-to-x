"""
Pipeline-based processing system for notes-to-x.

This module provides a flexible, stage-based pipeline for transforming notes.
"""

# Import core components
from .core import (
    Context,
    FileContext,
    NoteContext,
    MetaContext,
    Stage,
    register_stage,
    get_stage,
    list_stages,
    get_stage_info,
    Pipeline,
    load_pipeline_config,
    load_config_from_preset,
)

# Import all stages to trigger registration
from . import stages

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
