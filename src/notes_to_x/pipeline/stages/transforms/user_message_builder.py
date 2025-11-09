"""Build user message for LLM from note content."""

from pydantic import Field

from ...core import Context, Stage, StageOptions, register_stage


class UserMessageBuilderOptions(StageOptions):
    """Options for UserMessageBuilder stage."""

    include_date: bool = Field(default=True, description="Include date in message")
    date_label: str = Field(default="DATE", description="Label for date field")
    content_label: str = Field(default="CONTENT", description="Label for content field")


@register_stage("transform.build_user_message")
class UserMessageBuilder(Stage[UserMessageBuilderOptions]):
    """
    Build user message for LLM from note content.

    Stores message in ctx.custom["user_message"].
    """

    Options = UserMessageBuilderOptions

    def execute(self, ctx: Context) -> Context:
        """Build user message."""
        parts = []

        # Add date if present
        if self.options.include_date and ctx.note.date:
            date_label = self.options.date_label
            parts.append(f"{date_label}: {ctx.note.date}")

        # Add content
        content_label = self.options.content_label
        if ctx.note.content:
            parts.append(f"{content_label}:\n{ctx.note.content}")

        ctx.custom["user_message"] = "\n\n".join(parts)
        return ctx
