"""Segment content by custom delimiter pattern."""

import re

from pydantic import Field

from ...core import Context, Stage, StageOptions, register_stage
from ...core.helpers import create_segmented_contexts


class ByDelimiterSegmenterOptions(StageOptions):
    """Options for ByDelimiterSegmenter stage."""

    pattern: str = Field(default="^---$", description="Regex pattern to split on")


@register_stage("segment.by_delimiter")
class ByDelimiterSegmenter(Stage[ByDelimiterSegmenterOptions]):
    """
    Split content by custom delimiter pattern (1:N split).
    """

    Options = ByDelimiterSegmenterOptions

    def execute(self, ctx: Context) -> list[Context]:
        """Split content by delimiter."""
        if not ctx.file.content:
            ctx.add_issue("No content to segment", self.name, severity="warning")
            return [ctx]

        pattern = self.options.pattern
        parts = re.split(pattern, ctx.file.content, flags=re.MULTILINE)

        # Create segments with numbered titles
        segments = [(f"Segment {i + 1}", part) for i, part in enumerate(parts)]

        # Create one context per segment (filters empty content)
        return create_segmented_contexts(ctx, segments)
