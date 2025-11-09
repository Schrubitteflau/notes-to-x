"""Source stage for loading files from a folder."""

import os

from pydantic import Field, field_validator

from ...core import Context, FileContext, MetaContext, NoteContext, Stage, StageOptions, register_stage


class FolderSourceOptions(StageOptions):
    """Options for FolderSource stage."""

    path: str = Field(..., description="Path to folder")
    extensions: list[str] = Field(default=[".md", ".txt"], description="File extensions to include")
    recursive: bool = Field(default=True, description="Whether to search recursively")
    preset: str = Field(default="", description="Preset identifier for metadata")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate that path exists and is a directory."""
        if not os.path.exists(v):
            raise ValueError(f"Folder not found: {v}")
        if not os.path.isdir(v):
            raise ValueError(f"Path is not a directory: {v}")
        return v


@register_stage("source.folder")
class FolderSource(Stage[FolderSourceOptions]):
    """
    Initialize contexts from files in a folder.

    This is a special source stage that generates contexts from the file system.
    Unlike regular stages, it doesn't need an input context.
    """

    Options = FolderSourceOptions

    def generate(self) -> list[Context]:
        """
        Generate contexts from files in the folder.

        This method doesn't require an input context.
        Use this instead of execute() when calling from outside the pipeline.

        Returns:
            List of contexts, one per file found
        """
        path = self.options.path
        extensions = self.options.extensions
        recursive = self.options.recursive
        preset = self.options.preset

        contexts = []

        if recursive:
            # Walk directory recursively
            for root, _, files in os.walk(path):
                for filename in files:
                    if any(filename.endswith(ext) for ext in extensions):
                        filepath = os.path.join(root, filename)
                        contexts.append(self._create_context(filepath, preset))
        else:
            # Just files in top-level directory
            for filename in os.listdir(path):
                filepath = os.path.join(path, filename)
                if os.path.isfile(filepath) and any(filename.endswith(ext) for ext in extensions):
                    contexts.append(self._create_context(filepath, preset))

        return contexts

    def execute(self, ctx: Context) -> list[Context]:
        """
        Execute stage (for pipeline compatibility).

        Note: Input context is ignored as this is a source stage.
        """
        return self.generate()

    def _create_context(self, filepath: str, preset: str) -> Context:
        """Create initial context from file path."""
        name = os.path.basename(filepath)
        extension = os.path.splitext(filepath)[1]

        return Context(
            file=FileContext(path=filepath, name=name, extension=extension),
            note=NoteContext(),
            meta=MetaContext(preset=preset),
        )


# Note: This is a special "source" stage that generates contexts
# In practice, it would be called separately before the pipeline
# to create the initial context list
