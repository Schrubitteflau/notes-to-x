# Pipeline Stages

This document explains the different types of stages in the pipeline and how they work together.

## Stage Types

Stages are organized by their **granularity** (what they operate on) and **position** in the pipeline.

### 1. Sources (`source.*`)

**Purpose:** Initialize contexts from the file system
**Input:** None (generates contexts from scratch)
**Output:** List of contexts (1:N)
**Operates on:** File system

**When to use:** First stage to collect input files (called via `generate()` method)

**Examples:**

- `source.folder` - Collect files from a directory

```yaml
- kind: source.folder
  options:
    path: ./notes
    extensions: [".md", ".txt"]
```

---

### 2. Loaders (`load.*`)

**Purpose:** Load file content into context
**Input:** File path (via `ctx.file.path`)
**Output:** Same context with content loaded (1:1)
**Operates on:** File level

**When to use:** After source stage, before processing content

**Examples:**

- `load.markdown` - Load markdown files with optional frontmatter parsing
- `load.plaintext` - Load plain text files

```yaml
- kind: load.markdown
  options:
    parse_frontmatter: false
```

---

### 3. Segmenters (`segment.*`)

**Purpose:** Split file content into individual notes
**Input:** File content (via `ctx.file.content`)
**Output:** Multiple contexts, one per note (1:N)
**Operates on:** Content splitting

**When to use:** After loading, to divide files into logical units

**Examples:**

- `segment.single` - No splitting, treat whole file as one note
- `segment.by_title` - Split by markdown headers (e.g., `# Title`)
- `segment.by_delimiter` - Split by custom delimiter pattern

```yaml
- kind: segment.by_title
  options:
    level: 1 # Split on H1 headers
```

**Note:** After this stage, pipeline processes **N contexts** instead of 1

---

### 4. Enrichers (`enrich.*`)

**Purpose:** Extract and add metadata to notes
**Input:** Note content and metadata
**Output:** Same context enriched with metadata (1:1)
**Operates on:** Note level

**When to use:** After segmentation, to extract structured data

**Examples:**

- `enrich.date_from_title` - Extract date from note title
- `enrich.date_from_filename` - Extract date from filename
- `enrich.metadata` - Add custom metadata fields

```yaml
- kind: enrich.date_from_title
  options:
    pattern: '(\d{2}/\d{2}/\d{4})'
    format: "%d/%m/%Y"
```

---

### 5. Transforms (`transform.*`)

**Purpose:** Prepare data for LLM processing
**Input:** Note content and metadata
**Output:** Same context with prompts/messages (1:1)
**Operates on:** Note level

**When to use:** After enrichment, to build LLM inputs

**Examples:**

- `transform.prompt` - Build system prompt from Jinja2 template
- `transform.build_user_message` - Build user message from note content
- `llm.call` - Call LLM and store results

```yaml
- kind: transform.prompt
  options:
    template: "prompt.jinja2"
    system_prompt: true

- kind: llm.call
  options:
    model: "{{ MODEL }}"
    temperature: 0.2
    mock: false
```

---

## Pipeline Order

Stages must follow this typical order:

```
1. Source    -> Collect files from disk
2. Loader    -> Load file contents
3. Segmenter -> Split into individual notes
4. Enricher  -> Extract metadata (dates, etc.)
5. Transform -> Build prompts and call LLM
```

**Example Pipeline:**

```yaml
pipeline:
  # 1. Collect markdown files
  # (Handled automatically by CLI --source flag)

  # 2. Load content
  - kind: load.markdown
    options:
      parse_frontmatter: false

  # 3. Split by headers (1 file -> N notes)
  - kind: segment.by_title
    options:
      level: 1

  # 4. Extract date from each note
  - kind: enrich.date_from_title
    options:
      pattern: '(\d{2}/\d{2}/\d{4})'
      format: "%d/%m/%Y"

  # 5. Build LLM prompts
  - kind: transform.prompt
    options:
      template: "prompt.jinja2"

  - kind: transform.build_user_message
    options:
      include_date: true

  # 6. Call LLM
  - kind: llm.call
    options:
      model: "{{ MODEL }}"
      temperature: 0.2
```

---

## Key Concepts

### Granularity Levels

| Level    | Operates On             | Count      | Typical Stages                    |
| -------- | ----------------------- | ---------- | --------------------------------- |
| **File** | Entire file             | 1:1 or 1:N | Sources, Loaders                  |
| **Note** | Individual note/segment | 1:1 or 1:N | Segmenters, Enrichers, Transforms |

### Context Flow

```
Source Stage:
  [] -> [ctx1, ctx2, ctx3]  (creates contexts)

Loader Stage:
  [ctx1, ctx2, ctx3] -> [ctx1+content, ctx2+content, ctx3+content]  (1:1)

Segmenter Stage:
  [ctx1, ctx2, ctx3] -> [ctx1a, ctx1b, ctx2a, ctx2b, ctx2c, ctx3a]  (1:N)

Enricher Stage:
  [ctx1a, ctx1b, ...] -> [ctx1a+date, ctx1b+date, ...]  (1:1)

Transform Stage:
  [ctx1a+date, ...] -> [ctx1a+prompt, ...]  (1:1)
```

### 1:1 vs 1:N Stages

- **1:1 stages:** Input 1 context -> Output 1 context (same context modified)

  - Examples: Loaders, Enrichers, most Transforms

- **1:N stages:** Input 1 context -> Output N contexts (splitting/segmentation)
  - Examples: Segmenters
  - After a 1:N stage, all subsequent stages process N contexts
