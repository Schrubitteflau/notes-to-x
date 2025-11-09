"""Plain text file loader."""

from ...core import Context, Stage, StageOptions, read_file_content, register_stage


@register_stage("load.plaintext")
class PlaintextLoader(Stage[StageOptions]):
    """
    Load plain text file content.

    Sets ctx.file.content.

    No options required.
    """

    def execute(self, ctx: Context) -> Context:
        """Read file content."""
        content = read_file_content(ctx, self.name)
        if content is not None:
            ctx.file.content = content
        return ctx
