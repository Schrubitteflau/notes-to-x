"""Markdown file loader with optional frontmatter parsing."""

import re
from typing import Any

import yaml
from pydantic import Field

from ...core import Context, Stage, StageOptions, read_file_content, register_stage


class MarkdownLoaderOptions(StageOptions):
    """Options for MarkdownLoader stage."""

    parse_frontmatter: bool = Field(default=False, description="Whether to parse YAML frontmatter")


@register_stage("load.markdown")
class MarkdownLoader(Stage[MarkdownLoaderOptions]):
    """
    Load markdown file content and optionally parse YAML frontmatter.

    Sets ctx.file.content and ctx.file.markdown_properties (if frontmatter found).
    """

    Options = MarkdownLoaderOptions

    def execute(self, ctx: Context) -> Context:
        """Read file and parse frontmatter if requested."""
        # Read file content
        content = read_file_content(ctx, self.name)
        if content is None:
            return ctx

        # Parse frontmatter if requested
        if self.options.parse_frontmatter:
            content, properties, error = self._parse_frontmatter(content)
            ctx.file.markdown_properties = properties
            if error:
                ctx.add_issue(f"Failed to parse frontmatter: {error}", self.name, severity="warning")

        # Store content
        ctx.file.content = content

        return ctx

    def _parse_frontmatter(self, content: str) -> tuple[str, dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown content.

        Returns:
            Tuple of (content without frontmatter, properties dict, error message or empty string)
        """
        # Match YAML frontmatter pattern: ---\n...\n---
        pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            return content, {}, ""

        frontmatter_text = match.group(1)
        content_without_frontmatter = content[match.end() :]

        # Parse YAML properly using PyYAML
        try:
            properties = yaml.safe_load(frontmatter_text) or {}
            # Ensure we return a dict (in case YAML contains non-dict at root)
            if not isinstance(properties, dict):
                properties = {"data": properties}
            return content_without_frontmatter, properties, ""
        except yaml.YAMLError as e:
            # If YAML parsing fails, return empty dict and error message
            return content_without_frontmatter, {}, str(e)
