"""Extract date from note title."""

from pydantic import Field

from ...core import Context, Stage, StageOptions, register_stage
from ...core.helpers import extract_and_validate_date


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

        date_str, error_msg = extract_and_validate_date(
            ctx.note.title,
            self.options.pattern,
            self.options.format,
        )

        if error_msg:
            ctx.add_issue(
                error_msg,
                self.name,
                severity="error" if self.options.required else "warning",
            )
            return ctx

        ctx.note.date = date_str
        return ctx
