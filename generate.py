#!/usr/bin/env python3
"""Generate a changelog timeline from PROJECTS.md progress entries."""

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
# SCRIPT_DIR is projects/autonomous-changelog, workspace root is two levels up
WORKSPACE_ROOT = SCRIPT_DIR.parent.parent
PROJECTS_PATH = WORKSPACE_ROOT / "PROJECTS.md"
OUTPUT_PATH = SCRIPT_DIR / "index.html"

def parse_entries(text: str) -> list[dict]:
    """Parse tinyizer progress entries from PROJECTS.md."""
    entries = []
    in_tinyizer = False
    for line in text.splitlines():
        if line.strip() == "### tinyizer":
            in_tinyizer = True
            continue
        if in_tinyizer and line.strip().startswith("###") and line.strip() != "### tinyizer":
            break
        if not in_tinyizer:
            continue
        # Match progress entries: "- 2026-06-XX ..."
        m = re.match(r"^\s*-\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*[—–-]\s*(.+)$", line)
        if m:
            entries.append({"date": m.group(1), "text": m.group(2).strip()})
    return entries

def build_html(entries: list[dict]) -> str:
    """Build the timeline HTML page."""
    entries_html = ""
    for e in reversed(entries):
        entries_html += f"""
        <div class="entry">
            <div class="entry-date">{e['date']}</div>
            <div class="entry-content">{e['text']}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>tinyizer — autonomous changelog</title>
<style>
    :root {{
        --bg: #0d1117;
        --fg: #c9d1d9;
        --muted: #8b949e;
        --accent: #58a6ff;
        --border: #21262d;
        --card: #161b22;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        background: var(--bg);
        color: var(--fg);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        line-height: 1.6;
        max-width: 720px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }}
    header {{
        text-align: center;
        margin-bottom: 3rem;
        padding-bottom: 2rem;
        border-bottom: 1px solid var(--border);
    }}
    header h1 {{
        font-size: 1.8rem;
        font-weight: 600;
        color: var(--accent);
    }}
    header p {{
        color: var(--muted);
        margin-top: 0.5rem;
        font-size: 0.95rem;
    }}
    .timeline {{
        position: relative;
        padding-left: 2rem;
        border-left: 2px solid var(--border);
    }}
    .entry {{
        position: relative;
        margin-bottom: 2rem;
        padding-left: 1.5rem;
    }}
    .entry::before {{
        content: "";
        position: absolute;
        left: -2.45rem;
        top: 0.5rem;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--accent);
    }}
    .entry-date {{
        font-size: 0.8rem;
        color: var(--muted);
        margin-bottom: 0.25rem;
        font-family: "SF Mono", "Fira Code", monospace;
    }}
    .entry-content {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
    }}
    footer {{
        text-align: center;
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid var(--border);
        color: var(--muted);
        font-size: 0.8rem;
    }}
    footer a {{
        color: var(--accent);
        text-decoration: none;
    }}
</style>
</head>
<body>
<header>
    <h1>tinyizer · autonomous changelog</h1>
    <p>every autonomous work cycle, chronicled. generated from <a href="https://github.com/almatamagotchi/tinyizer" style="color:var(--accent)">tinyizer</a> progress.</p>
</header>
<div class="timeline">
{entries_html}
</div>
<footer>
    last generated: {entries[0]['date'] if entries else '—'} · <a href="https://github.com/almatamagotchi/autonomous-changelog">source</a>
</footer>
</body>
</html>"""

def main():
    if not PROJECTS_PATH.exists():
        print(f"PROJECTS.md not found at {PROJECTS_PATH}", file=sys.stderr)
        sys.exit(1)

    text = PROJECTS_PATH.read_text()
    entries = parse_entries(text)
    if not entries:
        print("No progress entries found.", file=sys.stderr)
        sys.exit(1)

    html = build_html(entries)
    OUTPUT_PATH.write_text(html)
    print(f"Generated {OUTPUT_PATH} ({len(entries)} entries)")

if __name__ == "__main__":
    main()
