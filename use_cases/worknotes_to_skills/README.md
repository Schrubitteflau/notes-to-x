# Work Notes to Skills Extractor

Extract skills and achievements from work notes using LLM processing.

## Directory Structure

```
worknotes_to_skills/
├── notes/              # Your work notes (markdown files)
├── pipeline.yaml       # Pipeline configuration
├── prompt.jinja2       # LLM prompt template
├── .env               # Your configuration (create from .env.example)
└── output/            # Generated output files
```

## Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` to configure your settings:
   - `MODEL`: The LLM model to use (requires API key in environment)
   - `CAREER_CONTEXT`: Context about your career/role
   - `NOTES_LANGUAGE`: Language of your notes
   - `OUTPUT_PATH`: Where to save the extracted skills

3. Make sure you have your LLM API key set:
   ```bash
   # For Anthropic Claude
   export ANTHROPIC_API_KEY="your-key-here"

   # For OpenAI
   export OPENAI_API_KEY="your-key-here"
   ```

## Usage

From this directory, run:

```bash
# Process all notes in the notes/ folder
notes-to-x run pipeline.yaml --source notes/

# Or specify individual files
notes-to-x run pipeline.yaml --source notes/Novembre.md
```

## Pipeline Stages

The pipeline processes your notes through these stages:

1. **Load Markdown** - Reads markdown files
2. **Segment by Title** - Splits by H1 headers (dates)
3. **Extract Date** - Extracts date from each section
4. **Build Prompt** - Creates LLM prompt from template
5. **Build User Message** - Formats note content
6. **Call LLM** - Processes with AI to extract skills
7. **Write Output** - Saves results to JSON

## Customization

### Modify the Pipeline

Edit `pipeline.yaml` to:
- Add/remove processing stages
- Change segmentation rules
- Adjust LLM parameters
- Change output format

### Modify the Prompt

Edit `prompt.jinja2` to:
- Change the extraction instructions
- Modify the output format
- Add additional fields to extract
- Customize for your use case

## Output Format

The pipeline generates a JSON file with this structure:

```json
[
  {
    "file": "Novembre.md",
    "date": "05/11/2024",
    "results": [
      {
        "summary": "Implemented real-time WebSocket notifications for dashboard using Socket.io...",
        "hard_skills": ["WebSocket", "Socket.io", "JavaScript", "Real-time systems"],
        "soft_skills": ["Problem-solving", "Technical implementation"]
      }
    ]
  }
]
```
