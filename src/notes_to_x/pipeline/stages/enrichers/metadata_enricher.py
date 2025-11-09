"""Add custom metadata to note from frontmatter or custom logic."""

from pydantic import Field

from ...core import Context, Stage, StageOptions, register_stage


class MetadataEnricherOptions(StageOptions):
    """Options for MetadataEnricher stage."""

    fields: dict[str, str] = Field(default_factory=dict, description="Map of field names to source paths")


@register_stage("enrich.metadata")
class MetadataEnricher(Stage[MetadataEnricherOptions]):
    """
    Add custom metadata to note from frontmatter or custom logic.
    """

    Options = MetadataEnricherOptions

    def execute(self, ctx: Context) -> Context:
        """Add metadata fields."""
        fields = self.options.fields

        for field_name, source_path in fields.items():
            value = ctx.get_value_from_path(source_path)
            if value is not None:
                ctx.note.metadata[field_name] = value

        return ctx
