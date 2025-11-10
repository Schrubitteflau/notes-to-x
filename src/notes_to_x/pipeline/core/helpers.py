"""Helper functions for common stage operations."""

import re
from datetime import datetime

from .context import Context, NoteContext


def read_file_content(ctx: Context, stage_name: str) -> str | None:
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
        with open(ctx.file.path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        ctx.add_issue(f"Failed to read file: {e}", stage_name, severity="error")
        return None


def extract_and_validate_date(
    text: str,
    pattern: str,
    date_format: str | None = None,
) -> tuple[str | None, str | None]:
    """
    Extract and validate date from text using regex pattern.

    Args:
        text: Text to search for date
        pattern: Regex pattern to match date (use capture group for date)
        date_format: Optional strptime format string for validation

    Returns:
        Tuple of (date_str, error_msg)
        - If successful: (date_str, None)
        - If no match: (None, error_msg)
        - If invalid format: (None, error_msg)

    Examples:
        >>> extract_and_validate_date("2024-01-15 notes", r"(\d{4}-\d{2}-\d{2})", "%Y-%m-%d")
        ('2024-01-15', None)

        >>> extract_and_validate_date("no date here", r"(\d{4}-\d{2}-\d{2})")
        (None, "No date found in: no date here")
    """
    match = re.search(pattern, text)
    if not match:
        return None, f"No date found in: {text}"

    # Use capture group(1) if present, otherwise full match
    date_str = match.group(1) if match.groups() else match.group(0)

    # Validate format if provided
    if date_format:
        try:
            datetime.strptime(date_str, date_format)
        except ValueError as e:
            return None, f"Date '{date_str}' doesn't match format '{date_format}': {e}"

    return date_str, None


def create_segmented_contexts(
    base_ctx: Context,
    segments: list[tuple[str, str]],
) -> list[Context]:
    """
    Create contexts from segments, filtering out empty content.

    Args:
        base_ctx: Base context to clone
        segments: List of (title, content) tuples

    Returns:
        List of contexts with segmented content.
        Returns [base_ctx] if no valid segments found.

    Examples:
        >>> segments = [("Section 1", "content1"), ("Section 2", "content2")]
        >>> contexts = create_segmented_contexts(ctx, segments)
        >>> len(contexts)
        2
    """
    contexts = []
    for title, content in segments:
        if not content.strip():
            continue
        new_ctx = base_ctx.clone(note=NoteContext(title=title, content=content.strip()))
        contexts.append(new_ctx)

    return contexts if contexts else [base_ctx]
