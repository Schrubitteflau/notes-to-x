"""Single-segment pass-through stage."""

from ...core import Context, Stage, StageOptions, register_stage


@register_stage("segment.single")
class SingleSegmenter(Stage[StageOptions]):
    """
    No-op segmenter that treats entire file as single note.

    Sets ctx.note.content from ctx.file.content (1:1 pass-through).

    No options required.
    """

    def execute(self, ctx: Context) -> Context:
        """Pass file content to note content."""
        ctx.note.content = ctx.file.content
        return ctx
