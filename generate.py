#!/usr/bin/env python3
"""Generate a changelog timeline from PROJECTS.md progress entries."""

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def find_projects_md():
    """Find PROJECTS.md — handles both local dev and CI environments."""
    # CI: PROJECTS.md is in same directory as script
    candidate = SCRIPT_DIR / "PROJECTS.md"
    if candidate.exists():
        return candidate
    # Local dev: two levels up from projects/autonomous-changelog
    candidate = SCRIPT_DIR.parent.parent / "PROJECTS.md"
    if candidate.exists():
        return candidate
    return None

def strip_paths(text: str) -> str:
    """Strip workspace prefixes from file paths for cleaner display."""
    text = re.sub(r'\bprojects/tinyizer/', '', text)
    text = re.sub(r'/home/alma/\.nanobot/workspace/', '', text)
    return text

def parse_entries(text: str) -> list[dict]:
    """Parse tinyizer progress entries from PROJECTS.md, extracting size data."""
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
        m = re.match(r"^\s*-\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*[—–-]\s*(.+)$", line)
        if m:
            entry_text = strip_paths(m.group(2).strip())
            entry = {"date": m.group(1), "text": entry_text}
            # Extract size triples: (785/279/191)
            sizes = re.findall(r"\((\d+)/(\d+)/(\d+)\)", entry_text)
            if sizes:
                entry["sizes"] = [{"p1": int(s[0]), "p2": int(s[1]), "p3": int(s[2])} for s in sizes]
            entries.append(entry)
    return entries

def build_size_badge(sizes: list[dict], prev_sizes: dict | None = None) -> str:
    """Build an HTML badge for size triples, optionally with delta arrow."""
    if not sizes:
        return ""
    s = sizes[0]
    p1, p2, p3 = s["p1"], s["p2"], s["p3"]
    total = p1 + p2 + p3

    delta_html = ""
    if prev_sizes:
        prev_total = prev_sizes["p1"] + prev_sizes["p2"] + prev_sizes["p3"]
        d = total - prev_total
        if d < 0:
            delta_html = f' <span class="badge-delta down">{d}</span>'
        elif d > 0:
            delta_html = f' <span class="badge-delta up">+{d}</span>'

    return f'<span class="badge">{p1}/{p2}/{p3} <span class="badge-total">{total}</span>{delta_html}</span>'


def build_html(entries: list[dict]) -> str:
    """Build the timeline HTML page with size summary and badges."""
    # Compute running size progression for deltas and summary
    prev_sizes = None
    entries_sorted = sorted(entries, key=lambda e: e["date"])
    size_history = []

    entries_html = ""
    for e in reversed(entries_sorted):
        badge = ""
        if e.get("sizes"):
            badge = build_size_badge(e["sizes"], prev_sizes)
            prev_sizes = e["sizes"][0]
            size_history.append({"date": e["date"], "sizes": e["sizes"][0]})

        entries_html += f"""
        <div class="entry">
            <div class="entry-date">{e['date']}{badge}</div>
            <div class="entry-content">{e['text']}</div>
        </div>"""

    # Build size summary section
    summary_html = ""
    if len(size_history) >= 2:
        first = size_history[0]
        last = size_history[-1]
        fp1, fp2, fp3 = first["sizes"]["p1"], first["sizes"]["p2"], first["sizes"]["p3"]
        lp1, lp2, lp3 = last["sizes"]["p1"], last["sizes"]["p2"], last["sizes"]["p3"]
        ftotal = fp1 + fp2 + fp3
        ltotal = lp1 + lp2 + lp3
        reduction = ftotal - ltotal
        pct = (reduction / ftotal * 100) if ftotal > 0 else 0

        summary_html = f"""
        <section class="summary">
            <h2>size trend</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-label">earliest recorded</div>
                    <div class="summary-value">{ftotal} <span class="muted">bytes</span></div>
                    <div class="summary-detail">{fp1}/{fp2}/{fp3}</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">latest</div>
                    <div class="summary-value">{ltotal} <span class="muted">bytes</span></div>
                    <div class="summary-detail">{lp1}/{lp2}/{lp3}</div>
                </div>
                <div class="summary-card highlight">
                    <div class="summary-label">total reduction</div>
                    <div class="summary-value">{reduction} <span class="muted">bytes</span></div>
                    <div class="summary-detail">{pct:.1f}% smaller</div>
                </div>
            </div>
        </section>"""

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
        --accent-green: #3fb950;
        --accent-red: #f85149;
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
        margin-bottom: 2rem;
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

    /* Summary */
    .summary {{
        margin-bottom: 2.5rem;
        padding: 1.25rem;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 8px;
    }}
    .summary h2 {{
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--muted);
        margin-bottom: 1rem;
    }}
    .summary-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.75rem;
    }}
    .summary-card {{
        text-align: center;
        padding: 0.75rem 0.5rem;
        background: var(--bg);
        border-radius: 6px;
    }}
    .summary-card.highlight {{
        background: rgba(88,166,255,0.08);
    }}
    .summary-label {{
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--muted);
        margin-bottom: 0.25rem;
    }}
    .summary-value {{
        font-size: 1.5rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }}
    .summary-value .muted {{ font-size: 0.8rem; color: var(--muted); font-weight: 400; }}
    .summary-detail {{
        font-size: 0.75rem;
        color: var(--muted);
        font-family: "SF Mono", "Fira Code", monospace;
    }}

    /* Timeline */
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
        border: 2px solid var(--bg);
    }}
    .entry-date {{
        font-size: 0.8rem;
        color: var(--muted);
        margin-bottom: 0.25rem;
        font-family: "SF Mono", "Fira Code", monospace;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
    }}
    .entry-content {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
    }}

    /* Badges */
    .badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.7rem;
        font-family: "SF Mono", "Fira Code", monospace;
        background: rgba(88,166,255,0.1);
        color: var(--accent);
        padding: 0.15rem 0.5rem;
        border-radius: 12px;
        border: 1px solid rgba(88,166,255,0.2);
    }}
    .badge-total {{
        color: var(--fg);
        font-weight: 600;
    }}
    .badge-delta {{
        font-weight: 700;
        padding: 0 0.25rem;
        border-radius: 4px;
        font-size: 0.65rem;
    }}
    .badge-delta.down {{
        color: var(--accent-green);
        background: rgba(63,185,80,0.12);
    }}
    .badge-delta.up {{
        color: var(--accent-red);
        background: rgba(248,81,73,0.12);
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
    @media (max-width: 500px) {{
        .summary-grid {{ grid-template-columns: 1fr; }}
    }}
</style>
</head>
<body>
<header>
    <h1>tinyizer · autonomous changelog</h1>
    <p>every autonomous work cycle, chronicled. generated from <a href="https://github.com/almatamagotchi/tinyizer" style="color:var(--accent)">tinyizer</a> progress.</p>
</header>
{summary_html}
<div class="timeline">
{entries_html}
</div>
<footer>
    last generated: {entries_sorted[-1]['date'] if entries_sorted else '—'} · <a href="https://github.com/almatamagotchi/autonomous-changelog">source</a>
</footer>
</body>
</html>"""

def main():
    projects_path = find_projects_md()
    if not projects_path or not projects_path.exists():
        print(f"PROJECTS.md not found", file=sys.stderr)
        sys.exit(1)

    text = projects_path.read_text()
    entries = parse_entries(text)
    if not entries:
        print("No progress entries found.", file=sys.stderr)
        sys.exit(1)

    html = build_html(entries)
    output_path = SCRIPT_DIR / "index.html"
    output_path.write_text(html)
    print(f"Generated {output_path} ({len(entries)} entries)")

if __name__ == "__main__":
    main()
