"""Extract date from filename."""

from pydantic import Field

from ...core import Context, Stage, StageOptions, register_stage
from ...core.helpers import extract_and_validate_date


class DateFromFilenameEnricherOptions(StageOptions):
    """Options for DateFromFilenameEnricher stage."""

    pattern: str = Field(..., description="Regex pattern with capture group for date")
    format: str | None = Field(default=None, description="strptime format string for validation")


@register_stage("enrich.date_from_filename")
class DateFromFilenameEnricher(Stage[DateFromFilenameEnricherOptions]):
    """
    Extract date from filename using regex pattern.

    Sets ctx.note.date.
    """

    Options = DateFromFilenameEnricherOptions

    def execute(self, ctx: Context) -> Context:
        """Extract date from filename."""
        date_str, error_msg = extract_and_validate_date(
            ctx.file.name,
            self.options.pattern,
            self.options.format,
        )

        if error_msg:
            ctx.add_issue(error_msg, self.name, severity="warning")
            return ctx

        ctx.note.date = date_str
        return ctx
