"""Helper functions for common stage operations."""

from typing import Optional
from .context import Context


def read_file_content(ctx: Context, stage_name: str) -> Optional[str]:
    """
    Read file content from ctx.file.path.

    Args:
        ctx: Context with file path
        stage_name: Name of calling stage (for error reporting)

    Returns:
        File content if successful, None if error

    Side effects:
        Adds error to context if file reading fails
    """
    try:
        with open(ctx.file.path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        ctx.add_issue(f"Failed to read file: {e}", stage_name, severity="error")
        return None
