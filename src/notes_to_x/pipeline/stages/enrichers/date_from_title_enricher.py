"""Extract date from note title."""

import re
from datetime import datetime

from pydantic import Field

from ...core import Context, Stage, StageOptions, register_stage


class DateFromTitleEnricherOptions(StageOptions):
    """Options for DateFromTitleEnricher stage."""

    pattern: str = Field(..., description="Regex pattern with capture group for date")
    format: str | None = Field(default=None, description="strptime format string for validation")
    required: bool = Field(default=False, description="Whether to error if no date found")


@register_stage("enrich.date_from_title")
class DateFromTitleEnricher(Stage[DateFromTitleEnricherOptions]):
    """
    Extract date from note title using regex pattern.

    Sets ctx.note.date.
    """

    Options = DateFromTitleEnricherOptions

    def execute(self, ctx: Context) -> Context:
        """Extract date from title."""
        if not ctx.note.title:
            ctx.add_issue(
                "No title available for date extraction",
                self.name,
                severity="error" if self.options.required else "warning",
            )
            return ctx

        pattern = self.options.pattern
        date_format = self.options.format

        match = re.search(pattern, ctx.note.title)
        if not match:
            ctx.add_issue(
                f"No date found in title: {ctx.note.title}",
                self.name,
                severity="error" if self.options.required else "warning",
            )
            return ctx

        date_str = match.group(1) if match.groups() else match.group(0)

        # Validate format if provided
        if date_format:
            try:
                datetime.strptime(date_str, date_format)
            except ValueError as e:
                ctx.add_issue(
                    f"Date '{date_str}' doesn't match format '{date_format}': {e}", self.name, severity="error"
                )
                return ctx

        ctx.note.date = date_str
        return ctx
