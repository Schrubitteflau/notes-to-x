"""Stage abstraction and registry system."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from .context import Context


class StageOptions(BaseModel):
    """Base options model for stages. Override in subclasses."""

    pass


# Type variable for generic stage options
TOptions = TypeVar("TOptions", bound=StageOptions)


class Stage(ABC, Generic[TOptions]):
    """
    Base class for all pipeline stages.

    A stage transforms one or more contexts:
    - 1:1 transform: Returns single Context
    - 1:N split: Returns List[Context] (e.g., segmenter)

    Each stage should define its own Options class (inheriting from StageOptions)
    to specify and validate its configuration parameters.

    Type parameter:
        TOptions: The specific StageOptions subclass for this stage
    """

    # Override this in subclasses with a Pydantic model
    Options: type[TOptions] = StageOptions

    def __init__(self, options: dict[str, Any]):
        """
        Initialize stage with options from config.

        Args:
            options: Dictionary of stage-specific options from YAML config

        Raises:
            ValidationError: If options don't match the stage's Options schema
        """
        try:
            # Validate and parse options using Pydantic model
            self.options: TOptions = self.Options(**options)
        except ValidationError as e:
            raise ValueError(f"Invalid options for {self.__class__.__name__}: {e}") from e

    @abstractmethod
    def execute(self, ctx: Context) -> Context | list[Context]:
        """
        Execute stage logic on a context.

        Args:
            ctx: Input context

        Returns:
            - Single Context for 1:1 transforms
            - List[Context] for 1:N splits (e.g., segmentation)
        """
        pass

    @property
    def name(self) -> str:
        """
        Stage name for logging and debugging.

        Can be overridden for custom naming.
        """
        return self.__class__.__name__

    def finalize(self):
        """
        Called after all contexts have been processed.

        Useful for writers that need to aggregate results.
        Override if stage needs cleanup or final processing.
        """
        pass


# Global stage registry
STAGE_REGISTRY: dict[str, type[Stage]] = {}


def register_stage(kind: str):
    """
    Decorator to register a stage implementation.

    Usage:
        @register_stage("load.markdown")
        class MarkdownLoader(Stage):
            ...

    Args:
        kind: Dot-separated stage identifier (e.g., "load.markdown")
    """

    def decorator(cls: type[Stage]):
        if kind in STAGE_REGISTRY:
            raise ValueError(f"Stage '{kind}' is already registered")

        if not issubclass(cls, Stage):
            raise TypeError("Stage class must inherit from Stage")

        STAGE_REGISTRY[kind] = cls
        return cls

    return decorator


def get_stage(kind: str, options: dict[str, Any]) -> Stage:
    """
    Create a stage instance from registry.

    Args:
        kind: Stage kind identifier
        options: Stage options from config

    Returns:
        Configured stage instance

    Raises:
        ValueError: If stage kind is not registered
    """
    if kind not in STAGE_REGISTRY:
        available = ", ".join(sorted(STAGE_REGISTRY.keys()))
        raise ValueError(f"Unknown stage kind: '{kind}'. Available stages: {available}")

    return STAGE_REGISTRY[kind](options)


def list_stages() -> list[str]:
    """List all registered stage kinds."""
    return sorted(STAGE_REGISTRY.keys())


def get_stage_info(kind: str) -> dict[str, Any]:
    """
    Get information about a registered stage.

    Args:
        kind: Stage kind identifier

    Returns:
        Dictionary with stage metadata

    Raises:
        ValueError: If stage kind is not registered
    """
    if kind not in STAGE_REGISTRY:
        raise ValueError(f"Unknown stage kind: '{kind}'")

    cls = STAGE_REGISTRY[kind]
    return {
        "kind": kind,
        "class": cls.__name__,
        "module": cls.__module__,
        "docstring": cls.__doc__ or "No description available",
    }
