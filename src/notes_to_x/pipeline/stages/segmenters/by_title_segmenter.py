"""Segment markdown content by headers."""

import re
from typing import ClassVar, Pattern

from pydantic import Field

from ...core import Context, Stage, StageOptions, register_stage
from ...core.helpers import create_segmented_contexts


class ByTitleSegmenterOptions(StageOptions):
    """Options for ByTitleSegmenter stage."""

    level: int = Field(default=1, description="Header level to split on (1-6)", ge=1, le=6)


@register_stage("segment.by_title")
class ByTitleSegmenter(Stage[ByTitleSegmenterOptions]):
    """
    Split markdown content by headers (1:N split).

    Creates multiple contexts, one per header section.
    """

    Options = ByTitleSegmenterOptions

    # Pre-compiled regex patterns for markdown headers (levels 1-6)
    HEADER_PATTERNS: ClassVar[dict[int, Pattern[str]]] = {
        level: re.compile(f"^{'#' * level}\\s+(.+)$") for level in range(1, 7)
    }

    def execute(self, ctx: Context) -> list[Context]:
        """Split content by headers."""
        if not ctx.file.content:
            ctx.add_issue("No content to segment", self.name, severity="warning")
            return [ctx]

        level = self.options.level
        segments = self._split_by_header(ctx.file.content, level)

        if not segments:
            # No headers found, treat as single segment
            ctx.note.content = ctx.file.content
            return [ctx]

        # Create one context per segment
        return create_segmented_contexts(ctx, segments)

    def _split_by_header(self, content: str, level: int) -> list[tuple[str, str]]:
        """
        Split markdown by headers of specified level.

        Returns:
            List of (title, content) tuples
        """
        # Use pre-compiled pattern for the specified level
        pattern = self.HEADER_PATTERNS[level]

        segments = []
        lines = content.split("\n")
        current_title = None
        current_content_lines = []

        for line in lines:
            match = pattern.match(line)

            if match:
                # Found a header - save previous segment
                if current_title is not None:
                    segments.append((current_title, "\n".join(current_content_lines).strip()))

                # Start new segment
                current_title = match.group(1).strip()
                current_content_lines = []
            else:
                # Regular content line
                if current_title is not None:
                    current_content_lines.append(line)

        # Save last segment
        if current_title is not None:
            segments.append((current_title, "\n".join(current_content_lines).strip()))

        return segments
