# Marp Skill

A Codex-compatible skill for generating Marp slides from structured JSON.

The skill gives an agent a stable workflow:

1. Plan a page sequence.
2. Choose an Awesome Marp template for each page.
3. Fill page content as JSON.
4. Render the JSON into a complete Marp Markdown deck with `scripts/build_slides.py`.

## Install

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/Xav1erW/marp-skill.git ~/.codex/skills/marp
```

Then restart Codex so the new skill is loaded.

If you use a different agent, install this repository wherever that agent expects local skills or tools. The required skill entry point is `SKILL.md`.

## Usage

Generate slides from inline JSON:

```bash
python scripts/build_slides.py \
  --pages-json '[
    {"template": "cover_e", "title": "Demo", "subtitle": "Marp Skill", "author": "Me", "date": "2026.04.19"},
    {"template": "toc_b", "entries": ["Overview"]},
    {"template": "fixedtitleA", "page_title": "Overview", "content": "- Render from JSON"},
    {"template": "lastpage", "email": "me@example.com", "wechat": "me"}
  ]' \
  --output slides.md
```

Or from a JSON file:

```bash
python scripts/build_slides.py --pages-file pages.json --output slides.md
```

## Repository Layout

- `SKILL.md`: agent-facing skill instructions.
- `scripts/build_slides.py`: JSON-to-Marp renderer and builder API.
- `themes/`: bundled Awesome Marp themes, including the enhanced `am_blue` theme.
- `images/`: logos, cover background, and footer artwork required by the themes.
- `.vscode/settings.json`: Marp for VS Code theme discovery and HTML support.
- `references/awesome_marp_readme.md`: Awesome Marp reference material used by the skill.

When an output path is provided, the builder automatically copies `themes/`, `images/`, and
`.vscode/settings.json` beside the generated deck. Existing files with the same names are updated.

## Requirements

- Python 3.10 or newer.
- Marp or a Marp-compatible editor to preview/export the generated Markdown deck.
