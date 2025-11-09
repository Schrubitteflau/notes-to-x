"""
Stage registry - imports all stages to trigger @register_stage decorators.

This module must be imported to make stages available to the pipeline.
"""

# Import all stages to trigger registration

# Sources
from .sources.folder import FolderSource

# Loaders
from .loaders.markdown_loader import MarkdownLoader
from .loaders.plaintext_loader import PlaintextLoader

# Segmenters
from .segmenters.single_segmenter import SingleSegmenter
from .segmenters.by_title_segmenter import ByTitleSegmenter
from .segmenters.by_delimiter_segmenter import ByDelimiterSegmenter

# Enrichers
from .enrichers.date_from_title_enricher import DateFromTitleEnricher
from .enrichers.date_from_filename_enricher import DateFromFilenameEnricher
from .enrichers.metadata_enricher import MetadataEnricher

# Transforms
from .transforms.prompt_builder import PromptBuilder
from .transforms.user_message_builder import UserMessageBuilder
from .transforms.llm import LLMCaller


__all__ = [
    # Sources
    "FolderSource",
    # Loaders
    "MarkdownLoader",
    "PlaintextLoader",
    # Segmenters
    "SingleSegmenter",
    "ByTitleSegmenter",
    "ByDelimiterSegmenter",
    # Enrichers
    "DateFromTitleEnricher",
    "DateFromFilenameEnricher",
    "MetadataEnricher",
    # Transforms
    "PromptBuilder",
    "UserMessageBuilder",
    "LLMCaller",
]
