#!/usr/bin/env python3
"""
Marp Slides Builder - Template Stitching Script

This script handles the template stitching for Marp slideshow generation.
All templates are pre-defined here.

Architecture:
    Agent -> JSON pages -> build_slides.py -> Marp markdown

Usage (Agent-driven JSON mode):
    python build_slides.py --pages-json '[
        {"template": "cover_e", "title": "My Title", "author": "Me"},
        {"template": "trans", "section_title": "Section 1"},
        {"template": "fixedtitleA", "content": "Content here"}
    ]' --output slides.md

    python build_slides.py --pages-file pages.json --output slides.md

Usage (Builder API):
    from build_slides import MarpSlidesBuilder
    builder = MarpSlidesBuilder(title="My Slides", ...)
    builder.add_cover().add_content(...).add_lastpage()
    output = builder.build()
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# =============================================================================
# TEMPLATES - All pre-defined, agent only fills content
# =============================================================================

TEMPLATES = {

    # -------------------------------------------------------------------------
    # YAML Header
    # -------------------------------------------------------------------------
    "yaml_header": """---
marp: true
size: 16:9
theme: {theme}
paginate: true
headingDivider: [2,3]
footer: \\ *{author}* *{title}* *{date}*
---
""",

    # -------------------------------------------------------------------------
    # Cover Pages (5 styles)
    # -------------------------------------------------------------------------
    "cover_a": """
<!-- _class: cover_a -->
<!-- _header: "" -->
<!-- _footer: "" -->
<!-- _paginate: "" -->

# {title}
###### {subtitle}

{author} | {date}
""",

    "cover_b": """
<!-- _class: cover_b -->
<!-- _header: "" -->
<!-- _footer: "" -->
<!-- _paginate: "" -->

# {title}
###### {subtitle}

{author}
{date}
""",

    "cover_c": """
<!-- _class: cover_c -->
<!-- _paginate: "" -->
<!-- _footer: {footer_text} -->
<!-- _header: ![](./images/logo2.png) -->

# <!-- fit -->{title}
###### {subtitle}

{author}
{date}
""",

    "cover_d": """
<!-- _class: cover_d -->
<!-- _paginate: "" -->
<!-- _footer: "{footer_text}" -->

# <!-- fit -->{title}
###### {subtitle}

{author}
{date}
""",

    "cover_e": """
<!-- _class: cover_e -->
<!-- _header: ![](./images/logo2.png) -->
<!-- _footer: ![](./images/footer2.png) -->
<!-- _paginate: "" -->

# <!-- fit -->{title}
###### {subtitle}

{author}
{date}
""",

    # -------------------------------------------------------------------------
    # Table of Contents (2 styles)
    # -------------------------------------------------------------------------
    "toc_a": """
<!-- _class: toc_a -->
<!-- _header: "CONTENTS" -->
<!-- _footer: "" -->
<!-- _paginate: "" -->

{toc_entries}
""",

    "toc_b": """
<!-- _header: 目录<br>CONTENTS<br>![](./images/logo2.png)-->
<!-- _class: toc_b largetext -->
<!-- _footer: "" -->
<!-- _paginate: "" -->

<style>
section.toc_b>ul {{
    transform: translate(0, -50%);
}}
</style>

{toc_entries}
""",

    # -------------------------------------------------------------------------
    # Transition Page
    # -------------------------------------------------------------------------
    "trans": """
## {section_title}

<!-- _class: trans -->
<!-- _footer: "" -->
<!-- _paginate: "" -->
""",

    # -------------------------------------------------------------------------
    # Content Pages
    # -------------------------------------------------------------------------
    "content_default": """
## {page_title}

{content}
""",

    "fixedtitleA": """
## {page_title}
<!-- _class: fixedtitleA -->
{content}
""",

    "fixedtitleB": """

## {page_title}
<!-- _class: fixedtitleB -->

<div class="div">

{content}

</div>
""",

    # -------------------------------------------------------------------------
    # Two Column Layouts
    # -------------------------------------------------------------------------
    "cols_2": """
## {page_title}
<!-- _class: cols-2 -->

<div class=ldiv>

{left_content}

</div>

<div class=rdiv>

{right_content}

</div>
""",

    "cols_2_64": """
## {page_title}
<!-- _class: cols-2-64 -->

<div class=limg>

{left_content}

</div>

<div class=rdiv>

{right_content}

</div>
""",

    "cols_2_73": """
## {page_title}
<!-- _class: cols-2-73 -->

<div class=limg>

{left_content}

</div>

<div class=rdiv>

{right_content}

</div>
""",

    "cols_2_46": """
## {page_title}
<!-- _class: cols-2-46 -->

<div class=ldiv>

{left_content}

</div>

<div class=rimg>

{right_content}

</div>
""",

    "cols_2_37": """
## {page_title}
<!-- _class: cols-2-37 -->

<div class=ldiv>

{left_content}

</div>

<div class=rimg>

{right_content}

</div>
""",

    "cols_3": """
## {page_title}
<!-- _class: cols-3 -->

<div class=ldiv>

{left_content}

</div>

<div class=mdiv>

{middle_content}

</div>

<div class=rdiv>

{right_content}

</div>
""",

    "rows_2": """
## {page_title}
<!-- _class: rows-2 -->

<div class="timg">

{top_content}

</div>

<div class="bimg">

{bottom_content}

</div>
""",

    "pin_3": """
## {page_title}
<!-- _class: pin-3 -->

<div class="tdiv">

{top_content}

</div>

<div class="limg">

{left_content}

</div>

<div class="rimg">

{right_content}

</div>
""",

    # -------------------------------------------------------------------------
    # Quote Boxes (5 colors)
    # -------------------------------------------------------------------------
    "bq_purple": """
<!-- _class: bq-purple -->

> {quote_content}
""",

    "bq_blue": """
<!-- _class: bq-blue -->

> {quote_content}
""",

    "bq_green": """
<!-- _class: bq-green -->

> {quote_content}
""",

    "bq_red": """
<!-- _class: bq-red -->

> {quote_content}
""",

    "bq_black": """
<!-- _class: bq-black -->

> {quote_content}
""",

    # -------------------------------------------------------------------------
    # List Layouts
    # -------------------------------------------------------------------------
    "cols2_ol_sq": """
<!-- _class: cols2_ol_sq fglass -->

{list_items}
""",

    "cols2_ol_ci": """
<!-- _class: cols2_ol_ci fglass -->

{list_items}
""",

    "cols2_ul_sq": """
<!-- _class: cols2_ul_sq fglass -->

{list_items}
""",

    "cols2_ul_ci": """
<!-- _class: cols2_ul_ci fglass -->

{list_items}
""",

    "col1_ol_sq": """
<!-- _class: col1_ol_sq fglass -->

{list_items}
""",

    "col1_ol_ci": """
<!-- _class: col1_ol_ci fglass -->

{list_items}
""",

    # -------------------------------------------------------------------------
    # Navigation Bar
    # -------------------------------------------------------------------------
    "navbar": """
<!-- _class: navbar -->
<!-- _header: \\ {header_content}-->

{content}
""",

    "navbar_fixedtitleA": """
<!-- _header: \\ {header_content}-->
<!-- _class: navbar fixedtitleA -->

{content}
""",

    # -------------------------------------------------------------------------
    # Footnote Page
    # -------------------------------------------------------------------------
    "footnote": """
<!-- _class: footnote -->

<div class="tdiv">

{body_content}

</div>

<div class="bdiv">

{footnote_content}

</div>
""",

    # -------------------------------------------------------------------------
    # Caption
    # -------------------------------------------------------------------------
    "caption": """
<!-- _class: caption -->

{image_content}

<div class="caption">
{caption_text}
</div>
""",

    # -------------------------------------------------------------------------
    # Last Page
    # -------------------------------------------------------------------------
    "lastpage": """
<!-- _class: lastpage -->
<!-- _footer: "" -->

###### 感谢交流 ~

**{email}** | **{wechat}**
""",

    # -------------------------------------------------------------------------
    # Page Separator
    # -------------------------------------------------------------------------
    "page_separator": """

---

""",
}


# =============================================================================
# Helper Functions
# =============================================================================

def format_list_items(items: List[str], ordered: bool = True) -> str:
    """Format a list of items as Markdown list."""
    if ordered:
        return "\n".join(f"- {item}" for item in items)
    else:
        return "\n".join(f"- {item}" for item in items)


def format_toc_entries(entries: List[Tuple[str, int]]) -> str:
    """Format table of contents entries."""
    return "\n".join(f"- [{title}](#{page})" for title, page in entries)


def escape_markdown(text: str) -> str:
    """Escape special Markdown characters for content areas."""
    # These don't need escaping in Marp's Markdown context
    return text


# =============================================================================
# JSON Page Renderer - Agent-driven page generation
# =============================================================================

class JsonPageRenderer:
    """
    Render Marp slides from JSON page descriptions.
    Agent controls each page via structured JSON input.

    Page JSON format:
    {
        "template": "cover_e",           // template name (required)
        "title": "Slide Title",           // for cover/fixedtitleA
        "page_title": "Slide Title",     // for content/layout pages
        "content": "..." ,               // main content
        "section_title": "...",           // for trans pages
        "author": "...",
        "date": "...",
        "subtitle": "...",
        "left_content": "...",
        "right_content": "...",
        "items": ["item1", "item2"],      // for list pages
        "quote_content": "...",
        "color": "bq-blue",
        "email": "...",
        "wechat": "...",
        "wechat_public": "..."
    }
    """

    def __init__(self, theme: str = "am_blue"):
        self.theme = theme
        self.pages: List[str] = []

    def _normalize_template(self, template: str) -> str:
        """Normalize template name: convert hyphens to underscores, add aliases."""
        # Convert hyphens to underscores for matching
        normalized = template.replace("-", "_")

        # Template aliases
        aliases = {
            "bq_blue": "bq_blue",
            "bq-blue": "bq_blue",
            "bq_blue": "bq_blue",
            "cols2": "cols_2",
            "cols2_64": "cols_2_64",
            "cols2_73": "cols_2_73",
            "cols2_46": "cols_2_46",
            "cols2_37": "cols_2_37",
            "cols3": "cols_3",
            "rows2": "rows_2",
            "pin3": "pin_3",
        }

        return aliases.get(normalized, normalized)

    def _clean_content(self, content: str) -> str:
        """Remove markdown title headers (# ## ### etc) from content."""
        lines = content.split("\n")
        cleaned = []
        for line in lines:
            # Remove leading # headers (## or ### etc) but keep the text after
            stripped = line.lstrip()
            if stripped.startswith("#"):
                # Find the first non-# character and take everything after it
                first_non_hash = line.lstrip("#")
                # Remove leading space after # (there should be one space normally)
                text = first_non_hash.lstrip() if first_non_hash else first_non_hash
                # Skip empty lines that came from headers
                if text.strip():
                    cleaned.append(text)
            else:
                cleaned.append(line)
        return "\n".join(cleaned)

    def render_page(self, page_desc: dict) -> str:
        """Render a single page from page description dict."""
        template = self._normalize_template(page_desc.get("template", "fixedtitleA"))

        # Get the template
        if template not in TEMPLATES:
            raise ValueError(f"Unknown template: {template} (normalized: {template})")

        tmpl = TEMPLATES[template]
        fmt_kwargs = {}

        # Build formatting kwargs based on template type
        if template.startswith("cover_"):
            fmt_kwargs = self._build_cover_kwargs(page_desc)
        elif template == "trans":
            fmt_kwargs = {"section_title": page_desc.get("section_title", "")}
        elif template.startswith("cols_"):
            fmt_kwargs = self._build_column_kwargs(page_desc)
        elif template.startswith("bq_"):
            fmt_kwargs = {"quote_content": page_desc.get("quote_content", "")}
        elif template in ["cols2_ol_sq", "cols2_ol_ci", "cols2_ul_sq", "cols2_ul_ci",
                          "col1_ol_sq", "col1_ol_ci"]:
            items = page_desc.get("items", [])
            fmt_kwargs = {"list_items": format_list_items(items)}
        elif template in ["fixedtitleA", "fixedtitleB"]:
            fmt_kwargs = {
                "page_title": page_desc.get("page_title", ""),
                "content": self._clean_content(page_desc.get("content", ""))
            }
        elif template == "toc_a":
            entries = page_desc.get("entries", [])
            if isinstance(entries[0], list) if entries else False:
                entries = [(e[0], e[1]) for e in entries]
            else:
                entries = [(str(e), i+1) for i, e in enumerate(entries)]
            fmt_kwargs = {"toc_entries": format_toc_entries(entries)}
        elif template == "toc_b":
            # toc_b: entries is list of section name strings
            entries = page_desc.get("entries", [])
            entries_str = "\n".join(f"* {e}" for e in entries)
            fmt_kwargs = {"toc_entries": entries_str}
        elif template == "lastpage":
            fmt_kwargs = {
                "email": page_desc.get("email", ""),
                "wechat": page_desc.get("wechat", ""),
                "wechat_public": page_desc.get("wechat_public", "")
            }
        elif template == "content_default":
            fmt_kwargs = {
                "page_title": page_desc.get("page_title", ""),
                "content": page_desc.get("content", "")
            }
        else:
            # Generic template - pass through content if available
            fmt_kwargs = {k: v for k, v in page_desc.items()
                          if k not in ["template"] and isinstance(v, str)}

        try:
            return tmpl.format(**fmt_kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required field for template {template}: {e}")

    def _build_cover_kwargs(self, page_desc: dict) -> dict:
        """Build kwargs for cover templates."""
        return {
            "title": page_desc.get("title", ""),
            "subtitle": page_desc.get("subtitle", ""),
            "author": page_desc.get("author", ""),
            "date": page_desc.get("date", ""),
            "footer_text": page_desc.get("footer_text", "")
        }

    def _build_column_kwargs(self, page_desc: dict) -> dict:
        """Build kwargs for column templates."""
        kwargs = {"page_title": page_desc.get("page_title", "")}
        for key in ["left_content", "middle_content", "right_content",
                    "top_content", "bottom_content"]:
            if key in page_desc:
                kwargs[key] = self._clean_content(page_desc[key])
        return kwargs

    def render_all(self, pages_json: List[dict]) -> str:
        """Render all pages and return complete Marp document."""
        self.pages = []

        # Build YAML header
        header = TEMPLATES["yaml_header"].format(
            theme=self.theme,
            title=pages_json[0].get("title", "Presentation") if pages_json else "Presentation",
            author=pages_json[0].get("author", "Author") if pages_json else "Author",
            date=pages_json[0].get("date", "") if pages_json else ""
        )

        # Render each page
        for page_desc in pages_json:
            page_md = self.render_page(page_desc)
            self.pages.append(page_md)

        # Only add --- after first page (cover), not between all pages
        if len(self.pages) > 1:
            return header + "\n" + self.pages[0] + "\n---\n" + "\n".join(self.pages[1:]) + "\n"
        return header + "\n" + self.pages[0] + "\n"

    def render_to_file(self, pages_json: List[dict], output_path: str) -> None:
        """Render pages and save to file."""
        content = self.render_all(pages_json)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)


def parse_document_structure(content: str) -> dict:
    """
    Parse document and extract structure.
    Returns: {title, subtitle, author, date, sections: [{heading, content, subsections}]}
    """
    lines = content.strip().split("\n")
    result = {
        "title": "",
        "subtitle": "",
        "author": "",
        "date": "",
        "sections": []
    }

    # Extract title (# heading at start)
    for line in lines:
        if line.startswith("# ") and not result["title"]:
            result["title"] = line[2:].strip()
        elif line.startswith("##### ") and not result["subtitle"]:
            result["subtitle"] = line[6:].strip()
        elif line.startswith("---") or line.startswith("***"):
            continue
        elif "@" in line and not result["author"]:
            # Try to extract author from @mentions or similar
            pass
        elif result["title"] and not result["sections"]:
            # First section starts after title
            pass

    return result


# =============================================================================
# Main Builder Class
# =============================================================================

@dataclass
class MarpSlidesBuilder:
    """
    Marp Slides Builder with template stitching.

    All templates are pre-defined in TEMPLATES dict.
    This class handles content filling and document assembly.
    """

    title: str = "Untitled"
    subtitle: str = ""
    author: str = "Author"
    date: str = ""
    theme: str = "am_blue"

    _pages: List[str] = field(default_factory=list)
    _toc_entries: List[Tuple[str, int]] = field(default_factory=list)
    _current_page: int = 1

    def __post_init__(self):
        self._pages = []
        self._toc_entries = []
        self._current_page = 1

    def add_cover(
        self,
        style: str = "cover_e",
        footer_text: str = ""
    ) -> "MarpSlidesBuilder":
        """Add a cover page."""
        template_key = f"cover_{style}" if style in ["a", "b", "c", "d", "e"] else "cover_e"

        # Map style names
        style_map = {"a": "cover_a", "b": "cover_b", "c": "cover_c", "d": "cover_d", "e": "cover_e"}
        template_key = style_map.get(style, style)

        if template_key not in TEMPLATES:
            template_key = "cover_e"

        template = TEMPLATES[template_key]

        if template_key == "cover_e":
            page = template.format(
                title=self.title,
                subtitle=self.subtitle,
                author=self.author,
                date=self.date
            )
        elif template_key == "cover_c":
            page = template.format(
                title=self.title,
                subtitle=self.subtitle,
                author=self.author,
                date=self.date,
                footer_text=footer_text
            )
        elif template_key == "cover_d":
            page = template.format(
                title=self.title,
                subtitle=self.subtitle,
                author=self.author,
                date=self.date,
                footer_text=footer_text
            )
        else:
            page = template.format(
                title=self.title,
                subtitle=self.subtitle,
                author=self.author,
                date=self.date
            )

        self._pages.append(page)
        self._current_page += 1
        return self

    def add_toc(
        self,
        style: str = "toc_a",
        entries: List[Tuple[str, int]] = None
    ) -> "MarpSlidesBuilder":
        """Add a table of contents page."""
        if entries is None:
            entries = self._toc_entries.copy()
        else:
            self._toc_entries = entries

        toc_content = format_toc_entries(entries)

        if style == "toc_b":
            page = TEMPLATES["toc_b"].format(toc_entries=toc_content)
        else:
            page = TEMPLATES["toc_a"].format(toc_entries=toc_content)

        self._pages.append(page)
        self._current_page += 1
        return self

    def add_toc_entry(self, title: str, page: int) -> "MarpSlidesBuilder":
        """Add an entry to TOC (for later rendering)."""
        self._toc_entries.append((title, page))
        return self

    def add_transition(self, section_title: str) -> "MarpSlidesBuilder":
        """Add a section transition page."""
        page = TEMPLATES["trans"].format(section_title=section_title)
        self._pages.append(page)
        self._current_page += 1
        return self

    def add_content(
        self,
        heading: str = "",
        content: str = "",
        layout: str = "default"
    ) -> "MarpSlidesBuilder":
        """Add a basic content page."""
        if layout == "fixedtitleA":
            page = TEMPLATES["fixedtitleA"].format(page_title=heading, content=content)
        elif layout == "fixedtitleB":
            page = TEMPLATES["fixedtitleB"].format(page_title=heading, content=content)
        else:
            if heading:
                page = TEMPLATES["content_default"].format(
                    page_title=heading,
                    content=content
                )
            else:
                page = content
        self._pages.append(page)
        self._current_page += 1
        return self

    def add_two_column(
        self,
        left_content: str,
        right_content: str,
        layout: str = "cols-2",
        page_title: str = ""
    ) -> "MarpSlidesBuilder":
        """Add a two-column content page."""
        layout_map = {
            "cols-2": "cols_2",
            "cols-2-64": "cols_2_64",
            "cols-2-73": "cols_2_73",
            "cols-2-46": "cols_2_46",
            "cols-2-37": "cols_2_37",
        }
        template_key = layout_map.get(layout, "cols_2")
        page = TEMPLATES[template_key].format(
            page_title=page_title,
            left_content=left_content,
            right_content=right_content
        )
        self._pages.append(page)
        self._current_page += 1
        return self

    def add_three_column(
        self,
        left_content: str,
        middle_content: str,
        right_content: str,
        page_title: str = ""
    ) -> "MarpSlidesBuilder":
        """Add a three-column content page."""
        page = TEMPLATES["cols_3"].format(
            page_title=page_title,
            left_content=left_content,
            middle_content=middle_content,
            right_content=right_content
        )
        self._pages.append(page)
        self._current_page += 1
        return self

    def add_rows(
        self,
        top_content: str,
        bottom_content: str,
        page_title: str = ""
    ) -> "MarpSlidesBuilder":
        """Add a two-row content page."""
        page = TEMPLATES["rows_2"].format(
            page_title=page_title,
            top_content=top_content,
            bottom_content=bottom_content
        )
        self._pages.append(page)
        self._current_page += 1
        return self

    def add_quote(
        self,
        quote_content: str,
        color: str = "bq-blue"
    ) -> "MarpSlidesBuilder":
        """Add a quote box page."""
        template_key = color if color in TEMPLATES else "bq_blue"
        page = TEMPLATES[template_key].format(quote_content=quote_content)
        self._pages.append(page)
        self._current_page += 1
        return self

    def add_list(
        self,
        items: List[str],
        style: str = "cols2_ol_sq",
        glass: bool = True
    ) -> "MarpSlidesBuilder":
        """Add a list page."""
        template_key = style if style in TEMPLATES else "cols2_ol_sq"
        list_content = format_list_items(items)
        page = TEMPLATES[template_key].format(list_items=list_content)
        self._pages.append(page)
        self._current_page += 1
        return self

    def add_navbar(
        self,
        header_content: str,
        content: str = "",
        fixed_title: str = ""
    ) -> "MarpSlidesBuilder":
        """Add a page with navigation bar."""
        if fixed_title == "fixedtitleA":
            page = TEMPLATES["navbar_fixedtitleA"].format(
                header_content=header_content,
                content=content
            )
        else:
            page = TEMPLATES["navbar"].format(
                header_content=header_content,
                content=content
            )
        self._pages.append(page)
        self._current_page += 1
        return self

    def add_footnote(
        self,
        body_content: str,
        footnote_content: str
    ) -> "MarpSlidesBuilder":
        """Add a footnote page."""
        page = TEMPLATES["footnote"].format(
            body_content=body_content,
            footnote_content=footnote_content
        )
        self._pages.append(page)
        self._current_page += 1
        return self

    def add_caption(
        self,
        image_content: str,
        caption_text: str
    ) -> "MarpSlidesBuilder":
        """Add a caption page."""
        page = TEMPLATES["caption"].format(
            image_content=image_content,
            caption_text=caption_text
        )
        self._pages.append(page)
        self._current_page += 1
        return self

    def add_lastpage(
        self,
        email: str = "",
        wechat: str = "",
        wechat_public: str = ""
    ) -> "MarpSlidesBuilder":
        """Add a last/thank you page."""
        page = TEMPLATES["lastpage"].format(
            email=email or self.author,
            wechat=wechat or "",
            wechat_public=wechat_public or ""
        )
        self._pages.append(page)
        return self

    def add_separator(self) -> "MarpSlidesBuilder":
        """Add a page separator."""
        self._pages.append(TEMPLATES["page_separator"])
        return self

    def add_raw(self, content: str) -> "MarpSlidesBuilder":
        """Add raw content directly."""
        self._pages.append(content)
        return self

    def build(self) -> str:
        """Build the final Marp document."""
        header = TEMPLATES["yaml_header"].format(
            theme=self.theme,
            title=self.title,
            author=self.author,
            date=self.date
        )
        return header + "\n".join(self._pages)

    def save(self, filepath: str) -> None:
        """Save the built document to a file."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.build())


# =============================================================================
# Document Parser - Automatic Document to Slides Conversion
# =============================================================================

class DocumentParser:
    """Parse a document and convert it to slides automatically."""

    def __init__(self, content: str):
        self.content = content
        self.lines = content.strip().split("\n")

    def extract_metadata(self) -> dict:
        """Extract title, subtitle, author, date from document."""
        metadata = {
            "title": "",
            "subtitle": "",
            "author": "",
            "date": ""
        }

        for i, line in enumerate(self.lines):
            # Title: first # heading
            if line.startswith("# ") and not metadata["title"]:
                metadata["title"] = line[2:].strip()

            # Subtitle: first ##### heading
            elif line.startswith("##### ") and not metadata["subtitle"]:
                metadata["subtitle"] = line[6:].strip()

            # Try to find author (look for email pattern or @handle)
            if not metadata["author"]:
                email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', line)
                if email_match:
                    metadata["author"] = line.split()[0] if line.split() else ""

            # Try to find date (look for YYYY.MM.DD or similar)
            if not metadata["date"]:
                date_match = re.search(r'\d{4}[./-]\d{1,2}[./-]\d{1,2}', line)
                if date_match:
                    metadata["date"] = date_match.group()

        # Use first few chars of first line as title if not found
        if not metadata["title"] and self.lines:
            metadata["title"] = self.lines[0][:50]

        return metadata

    def parse_sections(self) -> List[dict]:
        """Parse document into sections."""
        sections = []
        current_section = None

        for line in self.lines:
            # Skip YAML frontmatter
            if line.strip() == "---":
                continue

            # Section heading (# not ##)
            if line.startswith("# ") or line.startswith("## "):
                is_main = line.startswith("# ")
                heading_level = 1 if is_main else 2
                heading_text = line[2 if is_main else 3:].strip()

                if current_section:
                    sections.append(current_section)

                current_section = {
                    "level": heading_level,
                    "heading": heading_text,
                    "content": []
                }
            elif current_section is not None:
                current_section["content"].append(line)
            elif line.strip() and not line.startswith("<!--"):
                # Content before any heading
                if not sections:
                    sections.append({
                        "level": 0,
                        "heading": "",
                        "content": [line]
                    })

        if current_section:
            sections.append(current_section)

        return sections

    def auto_convert(self) -> MarpSlidesBuilder:
        """Automatically convert document to MarpSlidesBuilder."""
        metadata = self.extract_metadata()
        sections = self.parse_sections()

        builder = MarpSlidesBuilder(
            title=metadata["title"],
            subtitle=metadata["subtitle"],
            author=metadata["author"] or "Author",
            date=metadata["date"] or ""
        )

        # Add cover
        builder.add_cover(style="cover_e")

        # Add TOC placeholder (entries added as we build)
        toc_entries = []
        page_counter = 3  # Start counting pages

        for section in sections:
            if section["level"] == 1:
                # Main section - add transition
                builder.add_transition(section["heading"])
                toc_entries.append((section["heading"], page_counter))
                page_counter += 1
            elif section["level"] == 2:
                # Subsection - add content
                content = "\n".join(section["content"])
                builder.add_content(
                    heading=f"## {section['heading']}",
                    content=content,
                    layout="fixedtitleA"
                )
                page_counter += 1

        # Update TOC with actual page numbers
        # (In practice, pages would need to be renumbered)

        # Add last page
        builder.add_lastpage()

        return builder


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    import json as json_lib

    parser = argparse.ArgumentParser(
        description="Marp Slides Builder - Template Stitching Script"
    )
    parser.add_argument(
        "--input", "-i",
        help="Input document file (Markdown)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for generated slides"
    )
    parser.add_argument(
        "--pages-json", "-p",
        help="JSON string describing pages (Agent-driven mode)"
    )
    parser.add_argument(
        "--pages-file", "-f",
        help="JSON file describing pages (Agent-driven mode)"
    )
    parser.add_argument(
        "--title", "-t",
        default="Untitled",
        help="Presentation title"
    )
    parser.add_argument(
        "--subtitle", "-s",
        default="",
        help="Presentation subtitle"
    )
    parser.add_argument(
        "--author", "-a",
        default="Author",
        help="Author name"
    )
    parser.add_argument(
        "--date", "-d",
        default="",
        help="Date"
    )
    parser.add_argument(
        "--theme", "-th",
        default="am_blue",
        choices=["am_blue", "am_dark", "am_green", "am_red", "am_brown", "am_purple"],
        help="Color theme"
    )
    parser.add_argument(
        "--interactive", "-I",
        action="store_true",
        help="Interactive mode"
    )

    args = parser.parse_args()

    # Agent-driven JSON mode
    if args.pages_json:
        try:
            pages_data = json_lib.loads(args.pages_json)
        except json_lib.JSONDecodeError as e:
            print(f"Error: Invalid JSON: {e}")
            sys.exit(1)

        renderer = JsonPageRenderer(theme=args.theme)
        output = renderer.render_all(pages_data)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Slides saved to: {args.output}")
        else:
            print(output)
        return

    # Agent-driven JSON file mode
    if args.pages_file:
        with open(args.pages_file, "r", encoding="utf-8") as f:
            pages_data = json_lib.load(f)

        renderer = JsonPageRenderer(theme=args.theme)
        renderer.render_to_file(pages_data, args.output)
        print(f"Slides saved to: {args.output}")
        return

    if args.interactive:
        print("Marp Slides Builder - Interactive Mode")
        print("=" * 50)
        title = input("Title: ") or "Untitled"
        subtitle = input("Subtitle: ") or ""
        author = input("Author: ") or "Author"
        date = input("Date: ") or ""

        builder = MarpSlidesBuilder(
            title=title,
            subtitle=subtitle,
            author=author,
            date=date,
            theme=args.theme
        )

        print("\nAdding cover page...")
        builder.add_cover(style="cover_e")

        print("\nAdding TOC...")
        print("Enter TOC entries (empty to finish):")
        while True:
            entry = input("  Entry (title, page): ")
            if not entry.strip():
                break
            try:
                title, page = entry.split(",")
                builder.add_toc_entry(title.strip(), int(page.strip()))
            except ValueError:
                print("  Invalid format. Use: title, page")

        builder.add_toc(style="toc_a")

        print("\nAdding content pages...")
        print("Enter content (empty line to finish current, 'done' to finish):")
        current_content = []
        while True:
            line = input()
            if line.lower() == "done":
                break
            if not line.strip():
                if current_content:
                    builder.add_content(
                        content="\n".join(current_content),
                        layout="fixedtitleA"
                    )
                    current_content = []
            else:
                current_content.append(line)

        print("\nAdding last page...")
        builder.add_lastpage()

        output = builder.build()
        print("\n" + "=" * 50)
        print("Generated Slides:")
        print("=" * 50)
        print(output)

    elif args.input:
        # Read input file
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()

        # Auto-convert
        parser = DocumentParser(content)
        builder = parser.auto_convert()

        # Override with CLI args
        if args.title != "Untitled":
            builder.title = args.title
        if args.subtitle:
            builder.subtitle = args.subtitle
        if args.author != "Author":
            builder.author = args.author
        if args.date:
            builder.date = args.date
        builder.theme = args.theme

        output = builder.build()

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Slides saved to: {args.output}")
        else:
            print(output)

    else:
        # Show help
        parser.print_help()
        print("\n" + "=" * 50)
        print("Agent-driven mode (recommended):")
        print("  python build_slides.py --pages-json '[{\"template\":\"cover_e\",\"title\":\"...\"}]' -o slides.md")
        print("  python build_slides.py --pages-file pages.json -o slides.md")
        print("\nBuilder API mode:")
        print("  from build_slides import MarpSlidesBuilder")
        print("  builder = MarpSlidesBuilder(title='My Slides', ...)")
        print("  builder.add_cover().add_content(...).add_lastpage()")
        print("  output = builder.build()")
        print("\nLegacy document mode:")
        print("  python build_slides.py --input document.md -o slides.md")


if __name__ == "__main__":
    main()
