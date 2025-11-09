"""Extract date from filename."""

import re
from typing import Optional
from datetime import datetime
from pydantic import Field
from ...core import Context, Stage, StageOptions, register_stage


class DateFromFilenameEnricherOptions(StageOptions):
    """Options for DateFromFilenameEnricher stage."""
    pattern: str = Field(..., description="Regex pattern with capture group for date")
    format: Optional[str] = Field(
        default=None,
        description="strptime format string for validation"
    )


@register_stage("enrich.date_from_filename")
class DateFromFilenameEnricher(Stage[DateFromFilenameEnricherOptions]):
    """
    Extract date from filename using regex pattern.

    Sets ctx.note.date.
    """

    Options = DateFromFilenameEnricherOptions

    def execute(self, ctx: Context) -> Context:
        """Extract date from filename."""
        pattern = self.options.pattern
        date_format = self.options.format

        match = re.search(pattern, ctx.file.name)
        if not match:
            ctx.add_issue(f"No date found in filename: {ctx.file.name}", self.name, severity="warning")
            return ctx

        date_str = match.group(1) if match.groups() else match.group(0)

        # Validate format if provided
        if date_format:
            try:
                datetime.strptime(date_str, date_format)
            except ValueError as e:
                ctx.add_issue(
                    f"Date '{date_str}' doesn't match format '{date_format}': {e}",
                    self.name,
                    severity="error"
                )
                return ctx

        ctx.note.date = date_str
        return ctx
