# notes-to-x

> A flexible framework for transforming notes into various outputs using LLM

Transform your daily notes into structured, valuable content: skills for your résumé, summaries for documentation, blog post drafts, and more. The framework is designed to be simple, lightweight, and easy to extend with custom presets.

## What is notes-to-x?

**notes-to-x** is a configuration-driven framework that:
- Takes a folder of notes (Markdown, text files, etc.)
- Processes them through an LLM using customizable prompts
- Outputs structured results (JSON, and more formats to come)

The key feature: **you don't need to write code to create new transformations**. Just write a YAML config file and a prompt template.

## Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd notes-to-x

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Setup

Create a `.env` file with your LLM API credentials:

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
- `MODEL`: Your default LLM model (e.g., `openai/gpt-4`, `anthropic/claude-3-sonnet`)
- API keys for your chosen provider (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)

### Basic Usage

```bash
# Extract skills from work notes
notes-to-x ./notes --preset skills \
  --career-context "Senior Software Engineer" \
  --retrospective-content "@career_retro.txt"

# Generate summaries
notes-to-x ./notes --preset summary \
  --summary-style "technical"

# Create blog post drafts
notes-to-x ./notes --preset blog \
  --blog-tone "conversational"
```

## Built-in Presets

### 1. Skills (`skills`)

Extracts skills and achievements from work notes for résumé building.

**Variables:**
- `CAREER_CONTEXT` (required): Your career background
- `RETROSPECTIVE_CONTENT` (optional): Career retrospective for context
- `NOTES_LANGUAGE` (default: English): Language of your notes

**Output:** Structured JSON with achievements, hard skills, and soft skills

**Example:**
```bash
notes-to-x ./work_notes --preset skills \
  --career-context "Senior engineer with 10 years in web dev" \
  --retrospective-content "@retro.txt" \
  --output skills.json
```

### 2. Summary (`summary`)

Generates comprehensive summaries from notes.

**Variables:**
- `SUMMARY_STYLE` (default: professional): Writing style
- `TARGET_AUDIENCE` (default: general audience): Who will read this
- `NOTES_LANGUAGE` (default: English): Language of your notes

**Output:** JSON with title, summary, and key takeaways

**Example:**
```bash
notes-to-x ./notes --preset summary \
  --summary-style "technical" \
  --target-audience "software engineers"
```

### 3. Blog (`blog`)

Transforms notes into blog post drafts.

**Variables:**
- `BLOG_TONE` (default: conversational): Tone of the posts
- `TOPIC_FOCUS` (optional): Main topic or theme
- `NOTES_LANGUAGE` (default: English): Language of your notes

**Output:** JSON with title, introduction, sections, conclusion, and tags

**Example:**
```bash
notes-to-x ./notes --preset blog \
  --blog-tone "educational" \
  --topic-focus "lessons learned in software architecture"
```

## CLI Commands

### Process Notes

```bash
notes-to-x [INPUT_FOLDER] --preset [PRESET_NAME] [OPTIONS]
```

**Options:**
- `--preset, -p`: Preset to use (default: skills)
- `--output, -o`: Output file path (default: `<preset>_output.json`)
- `--model, -m`: LLM model to use (overrides MODEL env var)
- `--temperature, -t`: LLM temperature 0.0-1.0 (default: 0.2)
- `--extensions, -e`: File extensions to process (default: `.md,.txt`)

**Preset-specific variables:** Pass as `--variable-name "value"`

### List Available Presets

```bash
notes-to-x list-presets
```

### Show Preset Details

```bash
notes-to-x show-preset [PRESET_NAME]
```

Shows variables, description, and configuration for a preset.

## Python API

```python
from notes_to_x import NotesToX

# Create processor
processor = NotesToX(
    preset="skills",
    input_folder="./notes",
    variables={
        "CAREER_CONTEXT": "Senior engineer...",
        "RETROSPECTIVE_CONTENT": "@retro.txt"
    },
    model="openai/gpt-4",
    temperature=0.2
)

# Process notes
results = processor.run()

# Save results
processor.save(results, "output.json")

# List available presets
presets = NotesToX.list_available_presets()
```

See [`examples/python_api_usage.py`](examples/python_api_usage.py) for more examples.

## Creating Custom Presets

Creating a new preset requires **no code**, just two files:

### 1. Create a YAML Config

`src/notes_to_x/presets/my_preset.yaml`:

```yaml
name: my_preset
description: What this preset does
prompt_template: my_prompt.txt

variables:
  - name: MY_VARIABLE
    description: What this variable is for
    required: true

  - name: OPTIONAL_VAR
    description: Optional setting
    default: default_value

note_parser: raw  # or "dated" for notes with date headers
output_format: json
```

### 2. Create a Prompt Template

`src/notes_to_x/prompts/my_prompt.txt`:

```
You are analyzing notes to {MY_VARIABLE}.

Optional setting: {OPTIONAL_VAR}

Instructions:
1. Extract relevant information
2. Structure according to requirements
3. Output in JSON format

Output EXACTLY in this JSON format:

{
  "field1": "value",
  "field2": ["list", "of", "values"]
}
```

### 3. Use Your Preset

```bash
notes-to-x ./notes --preset my_preset --my-variable "some value"
```

See [`examples/custom_preset/`](examples/custom_preset/) for a complete example.

## Flexible Note Parsing

**notes-to-x supports fully configurable note parsing!** You can define exactly how your notes are structured through YAML configuration - no code changes required.

### Quick Examples

**Legacy format (simple):**
```yaml
note_parser: raw  # or "dated"
```

**New flexible format:**
```yaml
note_parser:
  split_strategy: date_headers  # How to split files into notes
  split_config:
    pattern: '^# \d{2}/\d{2}/\d{4}'  # Regex for splitting

  date_extraction: header  # How to extract dates
  date_config:
    pattern: '^# (\d{2}/\d{2}/\d{4})'  # Regex to capture date
    format: '%d/%m/%Y'  # strptime format
```

### Parsing Strategies

**1. Split Strategies** (how to divide files):
- `single`: 1 file = 1 note (e.g., daily note files like `2024-11-05.md`)
- `date_headers`: Split on date headers (e.g., `# DD/MM/YYYY`)
- `delimiter`: Split on custom patterns (e.g., `---`)

**2. Date Extraction** (how to find dates):
- `filename`: Extract from filename (`2024-11-05.md` → `2024-11-05`)
- `header`: Extract from content using regex
- `frontmatter`: Extract from YAML frontmatter (coming soon)
- `none`: No date extraction needed

### Real-World Examples

**Obsidian-style daily notes** (one file per day):
```yaml
note_parser:
  split_strategy: single
  date_extraction: filename
  date_config:
    pattern: '(\d{4}-\d{2}-\d{2})'
```

**Monthly journal** (multiple dated entries per file):
```yaml
note_parser:
  split_strategy: date_headers
  split_config:
    pattern: '^# \d{2}/\d{2}/\d{4}'
  date_extraction: header
  date_config:
    pattern: '^# (\d{2}/\d{2}/\d{4})'
    format: '%d/%m/%Y'
```

**See [`examples/custom_preset/PARSING_EXAMPLES.md`](examples/custom_preset/PARSING_EXAMPLES.md) for complete documentation and more examples.**

## Supported LLM Models

notes-to-x uses [LiteLLM](https://docs.litellm.ai/), which supports:

- **OpenAI**: `openai/gpt-4`, `openai/gpt-4-turbo`, `openai/gpt-3.5-turbo`
- **Anthropic**: `anthropic/claude-3-opus`, `anthropic/claude-3-sonnet`, `anthropic/claude-3-haiku`
- **Local models**: Any model supported by LiteLLM
- **Many more providers**: See [LiteLLM docs](https://docs.litellm.ai/docs/providers)

### Model Recommendations

**For development/testing:**
- Fast and cheap: `openai/gpt-3.5-turbo`, `anthropic/claude-3-haiku`
- Quick iteration without high token costs

**For production:**
- Good balance: `openai/gpt-4-turbo`, `anthropic/claude-3-sonnet`
- Best quality: `openai/gpt-4`, `anthropic/claude-3-opus`
- Higher cost but better analysis and extraction

### 💡 Tip: Use LLM Workbenches for Better Results

For optimal prompt quality and token efficiency, consider using **LLM provider workbenches** instead of local templates:

- **Anthropic Workbench**: https://console.anthropic.com/workbench
- **OpenAI Playground**: https://platform.openai.com/playground

**Why workbenches may be better:**
- ✅ **Optimized prompts**: Provider-tuned templates designed for their specific models
- ✅ **Token efficiency**: Better prompt engineering = fewer tokens = lower costs
- ✅ **Interactive testing**: Test and refine prompts before committing to code
- ✅ **Model-specific features**: Access to features like prompt caching, system instructions optimization

**How to use with notes-to-x:**
1. Design and test your prompt in the workbench
2. Save the optimized prompt configuration
3. Use it in your pipeline via the prompt template or directly in code

This approach can significantly improve result quality while reducing API costs compared to locally-defined templates.

## Project Structure

```
notes-to-x/
├── src/notes_to_x/
│   ├── __init__.py           # Main API (NotesToX class)
│   ├── cli.py                # Command-line interface
│   ├── template.py           # Template rendering utilities
│   ├── core/                 # Core processing components
│   │   ├── loader.py         # Note loading
│   │   ├── parsers.py        # Note parsers (dated, raw)
│   │   ├── processor.py      # Main orchestrator
│   │   ├── llm_client.py     # LLM wrapper
│   │   └── output.py         # Output writers
│   ├── presets/              # Preset configurations (YAML)
│   │   ├── skills.yaml
│   │   ├── summary.yaml
│   │   └── blog.yaml
│   └── prompts/              # Prompt templates
│       ├── skills.txt
│       ├── summary.txt
│       └── blog.txt
├── examples/                 # Usage examples
│   ├── python_api_usage.py
│   └── custom_preset/        # How to create custom presets
└── README.md
```

## Design Philosophy

- **Simple**: No over-engineering, straightforward architecture
- **Configuration-driven**: Create new transformations without writing code
- **Lightweight**: Minimal dependencies, easy to understand and modify
- **Flexible**: Easy to extend with custom presets and parsers

## FAQ

### Can I use local LLM models?

Yes! LiteLLM supports many local model providers. See their [documentation](https://docs.litellm.ai/docs/providers) for setup instructions.

### Can I process notes in languages other than English?

Yes! All presets support the `NOTES_LANGUAGE` variable. Just set it to your language.

### How do I use content from files in variables?

Prefix the value with `@` to load from a file:

```bash
notes-to-x ./notes --preset skills --career-context "@career.txt"
```

### Can I add more output formats besides JSON?

Currently only JSON is supported, but the framework is designed to easily add more formats (Markdown, PDF, etc.) in `src/notes_to_x/core/output.py`.

## Contributing

Contributions are welcome! Some ideas:

- New built-in presets (e.g., meeting notes, project documentation)
- Additional note parsers (e.g., YAML frontmatter support)
- More output formats (Markdown, HTML, PDF)
- Chunking strategies for large note collections

## License

[Your chosen license]

## Credits

Built with:
- [LiteLLM](https://github.com/BerriAI/litellm) - Universal LLM API
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [PyYAML](https://pyyaml.org/) - YAML parsing
