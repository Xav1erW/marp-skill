---
name: marp
description: "Convert content to Marp slideshows with Awesome Marp templates. Use this skill whenever the user wants to create slides - agent controls each page via JSON. Triggers when user mentions creating slides, Marp, slide generation, or requests turning content into a presentation."
---

# Marp Skill

Convert content to beautiful Marp slideshows using the Awesome Marp template system.
**Agent controls every page** via structured JSON input.

---

## Architecture

```
Agent → Page JSON Array → build_slides.py → Marp Markdown
```

| Layer | Responsibility |
|-------|---------------|
| `scripts/build_slides.py` | Template stitching, JSON rendering |
| **Agent** | **Page planning, layout selection, content filling** |
| Output | Complete Marp slideshow |

---

## Quick Start

**⚠️ STRICT RULE: Content in JSON must NOT contain:**
- Markdown titles (`##`, `###`, etc.) or any heading syntax
- Marp comments like `<!-- _class:xxx -->` or `<!-- footer:xxx -->`
- Any template-specific directives

All template selection and formatting is handled by JSON fields. Put slide titles in `page_title`; put only body content in `content`, `left_content`, `right_content`, etc. Body content may contain paragraphs, bullets, math, images, and emphasis, but must not contain Markdown title headers or template directives.

**Agent generates slides by passing JSON to the build script:**

```bash
python scripts/build_slides.py \
    --pages-json '[
        {"template": "cover_e", "title": "My Title", "author": "Me"},
        {"template": "trans", "section_title": "Section 1"},
        {"template": "fixedtitleA", "page_title": "Topic", "content": "Content here"}
    ]' \
    --output slides.md
```

Or use a JSON file:
```bash
python scripts/build_slides.py --pages-file pages.json --output slides.md
```

---

## Page JSON Format

Each page is a JSON object with a `template` field and corresponding content:

```json
{
    "template": "cover_e",
    "title": "Slide Title",
    "subtitle": "Subtitle",
    "author": "Author Name",
    "date": "2026.04.07"
}
```

### Available Templates

| Template | Description | Key Fields |
|----------|-------------|------------|
| `cover_e` | Full cover with dual logos | title, subtitle, author, date |
| `cover_a/b/c/d` | Other cover styles | title, subtitle, author, date |
| `trans` | Section transition | section_title |
| `toc_b` | **Recommended TOC** (required) | entries: ["sec1", "sec2", ...] |
| `toc_a` | Simple TOC (deprecated) | entries: [[title, page], ...] |
| `fixedtitleA` | Content page | page_title, content |
| `cols_2` | Two columns 50:50 | page_title, left_content, right_content |
| `cols_2_64` | Two columns 60:40 | page_title, left_content, right_content |
| `cols_2_73` | Two columns 70:30 | page_title, left_content, right_content |
| `cols_2_46` | Two columns 40:60 | page_title, left_content, right_content |
| `cols_2_37` | Two columns 30:70 | page_title, left_content, right_content |
| `cols_3` | Three columns | page_title, left_content, middle_content, right_content |
| `rows_2` | Two rows | page_title, top_content, bottom_content |
| `bq-blue/purple/green/red/black` | Quote box | quote_content |
| `cols2_ol_sq` | Ordered list | items: [item1, item2, ...] |
| `cols2_ol_ci` | Ordered list (circle) | items |
| `cols2_ul_sq` | Unordered list | items |
| `cols2_ul_ci` | Unordered list (circle) | items |
| `lastpage` | Thank you page | email, wechat |

---

## Agent Workflow

### Step 1: Plan Page Structure

Decide the page sequence based on content:
1. Cover page (`cover_e`)
2. Table of contents (`toc_b`) - **required**
3. Section transitions (`trans`)
4. Content pages (`fixedtitleA`, `cols_*`, etc.)
5. Last page (`lastpage`)

### Step 2: Choose Layouts

```
Content Type → Recommended Template
─────────────────────────────────────
Title + bullets → fixedtitleA
Two concepts comparison → cols_2
Image + caption → cols_2_64
Quote / insight → bq-blue
Step-by-step → cols2_ol_sq
Key takeaway → bq-green
```

### Step 3: Generate JSON

Build the pages array:

```json
[
    {"template": "cover_e", "title": "Title", "subtitle": "Subtitle", "author": "Me", "date": "2026.04.07"},
    {"template": "toc_b", "entries": ["Overview", "Method", "Results"]},
    {"template": "trans", "section_title": "1. Motivation"},
    {"template": "fixedtitleA", "page_title": "VLM 瓶颈", "content": "- Point 1\n- Point 2"},
    {"template": "bq-blue", "quote_content": "Key insight here"},
    {"template": "lastpage", "email": "me@email.com", "wechat": "my_wechat"}
]
```

### Step 4: Render

Call the build script with `--pages-json` or `--pages-file`.

---

## Example: SIVS Paper Slides

```json
[
    {"template": "cover_e", "title": "Semantic Impact–Driven Visual Scheduling", "subtitle": "SIVS", "author": "Research Team", "date": "2026.04.07"},
    {"template": "toc_b", "entries": ["Motivation", "Method", "Results"]},
    {"template": "trans", "section_title": "1. Motivation"},
    {"template": "fixedtitleA", "page_title": "VLM 推理瓶颈", "content": "- 数百~上千视觉 token\n- 每步需访问完整 visual KV cache\n- 显存压力大，memory bandwidth 瓶颈"},
    {"template": "trans", "section_title": "2. Method"},
    {"template": "cols_2", "page_title": "Semantic Impact", "left_content": "**Semantic Lens**\n\n- Top-K token embedding\n- QR 正交分解\n- 投影到 decision space", "right_content": "$$\\delta_{sem} = \\Pi_{sem}(h_t^{(v)} - h_t^{(\\emptyset)})$$"},
    {"template": "trans", "section_title": "3. Results"},
    {"template": "cols_2_46", "page_title": "Main Results", "left_content": "- **87.66%** KV 压缩\n- **99.93%** 性能保留\n- **23.5%** 加速", "right_content": "**Comparison**\n\n优于 FastV / SparseVLM / LOOK-M"},
    {"template": "lastpage", "email": "research@example.com", "wechat": "research_bot"}
]
```

---

## Builder API (Alternative)

For programmatic slide building:

```python
from build_slides import MarpSlidesBuilder

builder = MarpSlidesBuilder(
    title="My Slides",
    author="Me",
    date="2026.04.07",
    theme="am_blue"
)

builder.add_cover(style="cover_e")
builder.add_toc(style="toc_b", entries=["Section 1", "Section 2"])
builder.add_transition("Section 1")
builder.add_content(heading="Topic", content="- Item 1\n- Item 2", layout="fixedtitleA")
builder.add_lastpage(email="me@email.com", wechat="my_wechat")

output = builder.build()
```

---

## Color Themes

Pass via `--theme` flag or `theme` parameter:

| Theme | Description |
|-------|-------------|
| `am_blue` | Blue (default) |
| `am_dark` | Dark mode |
| `am_green` | Green |
| `am_red` | Red |
| `am_brown` | Brown |
| `am_purple` | Purple |

---

## Font Size Modifiers

Add class to content for size adjustment:
- `tinytext` - 0.8x
- `smalltext` - 0.9x
- `largetext` - 1.15x
- `hugetext` - 1.3x

---

## QA Checklist

- [ ] Every page has a clear purpose
- [ ] Layout matches content type
- [ ] No placeholder text ("xxxx", "lorem")
- [ ] Lists ≤8 items per page
- [ ] Math formulas render correctly ($...$)
- [ ] Cover page has correct title/author/date
- [ ] Last page has contact info
