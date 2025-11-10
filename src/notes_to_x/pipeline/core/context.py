"""Context dataclasses for pipeline flow."""

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal

from .logging import get_logger


@dataclass
class FileContext:
    """File-level information."""

    path: str
    name: str
    extension: str
    content: str | None = None
    markdown_properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class NoteContext:
    """Note-level information (a file may contain multiple notes)."""

    title: str | None = None
    content: str | None = None
    date: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    results: list[Any] = field(default_factory=list)


@dataclass
class MetaContext:
    """Pipeline execution metadata."""

    preset: str = ""
    processed_by: list[str] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Context:
    """
    Main context object that flows through the pipeline.

    Stages transform this context as it moves through the pipeline.
    Supports immutable cloning for 1:N splits.
    """

    file: FileContext
    note: NoteContext
    meta: MetaContext
    custom: dict[str, Any] = field(default_factory=dict)

    def clone(self, **overrides) -> "Context":
        """
        Create a deep copy of this context with optional field overrides.

        Examples:
            ctx.clone(note=NoteContext(title="New"))
            ctx.clone(custom={"key": "value"})
        """
        # Deep copy to avoid shared references
        new_ctx = Context(
            file=deepcopy(self.file), note=deepcopy(self.note), meta=deepcopy(self.meta), custom=deepcopy(self.custom)
        )

        # Apply overrides
        for key, value in overrides.items():
            setattr(new_ctx, key, value)

        return new_ctx

    def add_issue(self, message: str, stage: str, severity: Literal["warning", "error"] = "error", **extra):
        """
        Add a warning or error to the context.

        Args:
            message: Issue description
            stage: Name of the stage reporting the issue
            severity: "warning" (continues execution) or "error" (may stop pipeline)
            **extra: Additional metadata to include

        Examples:
            ctx.add_issue("Missing field", self.name, severity="warning")
            ctx.add_issue("Invalid data", self.name, severity="error")

            # Conditional severity:
            severity = "error" if self.options.required else "warning"
            ctx.add_issue("No data found", self.name, severity=severity)
        """
        issue = {"stage": stage, "message": message, "timestamp": datetime.now().isoformat(), **extra}

        # Log the issue with structured logging
        logger = get_logger(__name__)
        log_method = logger.error if severity == "error" else logger.warning
        log_method(
            "Pipeline issue",
            stage=stage,
            severity=severity,
            message=message,
            file=self.file.name if self.file else None,
            **extra,
        )

        if severity == "error":
            self.meta.errors.append(issue)
        else:
            self.meta.warnings.append(issue)

    def mark_processed_by(self, stage_name: str):
        """Track which stages have processed this context."""
        self.meta.processed_by.append(stage_name)

    @property
    def has_errors(self) -> bool:
        """Check if context has any errors."""
        return len(self.meta.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if context has any warnings."""
        return len(self.meta.warnings) > 0

    def get_value_from_path(self, path: str):
        """
        Get value from context using dot notation path.

        Args:
            path: Dot-separated path like "file.markdown_properties.author"

        Returns:
            Value at path, or None if not found

        Examples:
            ctx.get_value_from_path("file.name") -> "example.md"
            ctx.get_value_from_path("file.markdown_properties.author") -> "John Doe"
            ctx.get_value_from_path("note.date") -> "2024-11-09"
        """
        parts = path.split(".")
        current = self

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)

            if current is None:
                return None

        return current

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_file_path(cls, path: str, preset: str = "") -> "Context":
        """Create a minimal context from a file path."""
        import os

        name = os.path.basename(path)
        extension = os.path.splitext(path)[1]

        return cls(
            file=FileContext(path=path, name=name, extension=extension),
            note=NoteContext(),
            meta=MetaContext(preset=preset),
        )
