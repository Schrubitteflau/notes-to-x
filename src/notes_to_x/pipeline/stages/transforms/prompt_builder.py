"""Prompt building from Jinja2 templates."""

import os

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from pydantic import Field

from ...core import Context, Stage, StageOptions, register_stage


class PromptBuilderOptions(StageOptions):
    """Options for PromptBuilder stage."""

    template: str = Field(..., description="Path to template file or inline template")
    template_inline: bool = Field(default=False, description="If True, treat 'template' as inline content")
    required_vars: list[str] = Field(default_factory=list, description="Variables that must be present")
    system_prompt: bool = Field(
        default=True, description="If True, store in ctx.custom['system_prompt'], else 'user_prompt'"
    )


@register_stage("transform.prompt")
class PromptBuilder(Stage[PromptBuilderOptions]):
    """
    Build LLM prompts from Jinja2 templates.

    Stores rendered prompt in ctx.custom["prompt"].
    """

    Options = PromptBuilderOptions

    def execute(self, ctx: Context) -> Context:
        """Render prompt template."""
        template_str = self.options.template
        is_inline = self.options.template_inline
        required_vars = self.options.required_vars
        is_system = self.options.system_prompt

        # Build template context
        template_ctx = self._build_template_context(ctx)

        # Check required variables
        missing_vars = [var for var in required_vars if var not in template_ctx]
        if missing_vars:
            ctx.add_issue(
                f"Missing required template variables: {', '.join(missing_vars)}", self.name, severity="warning"
            )

        # Render template
        try:
            if is_inline:
                template = Template(template_str)
                rendered = template.render(template_ctx)
            else:
                rendered = self._render_from_file(template_str, template_ctx)

            # Store in context
            key = "system_prompt" if is_system else "user_prompt"
            ctx.custom[key] = rendered

        except Exception as e:
            ctx.add_issue(f"Failed to render template: {e}", self.name, severity="error")

        return ctx

    def _build_template_context(self, ctx: Context) -> dict:
        """Build context dictionary for template rendering."""
        return {
            "file": {
                "name": ctx.file.name,
                "path": ctx.file.path,
                "extension": ctx.file.extension,
                **ctx.file.markdown_properties,
            },
            "note": {
                "title": ctx.note.title,
                "content": ctx.note.content,
                "date": ctx.note.date,
                "metadata": ctx.note.metadata,
            },
            **ctx.custom,  # Include any custom data set by previous stages
        }

    def _render_from_file(self, template_name: str, context: dict) -> str:
        """Render template from file.

        Looks for templates in this order:
        1. Absolute path
        2. Relative to current working directory
        3. Package templates directory (for backward compatibility)
        """
        # Try absolute path or relative to cwd first
        if os.path.isabs(template_name):
            template_path = template_name
        else:
            template_path = os.path.abspath(template_name)

        if os.path.exists(template_path):
            # Load from absolute/cwd path
            template_dir = os.path.dirname(template_path)
            template_file = os.path.basename(template_path)
            env = Environment(loader=FileSystemLoader(template_dir or "."))
            try:
                template = env.get_template(template_file)
                return template.render(context)
            except TemplateNotFound:
                pass

        # Fall back to package templates directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pipeline_dir = os.path.dirname(os.path.dirname(current_dir))
        templates_dir = os.path.join(pipeline_dir, "templates")

        env = Environment(loader=FileSystemLoader(templates_dir))

        try:
            template = env.get_template(template_name)
            return template.render(context)
        except TemplateNotFound as e:
            raise FileNotFoundError(
                f"Template not found: {template_name}\n  Searched in: {template_path}, {templates_dir}"
            ) from e
