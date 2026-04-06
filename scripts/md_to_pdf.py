#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import markdown


def _browser_path() -> str:
    candidates = [
        "msedge",
        "chrome",
        "chromium",
        "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
        "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    ]
    for c in candidates:
        if shutil.which(c):
            return shutil.which(c) or c
        if Path(c).exists():
            return c
    raise RuntimeError("No headless browser found (Edge/Chrome).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Markdown to pretty PDF")
    parser.add_argument("input_md", type=Path)
    parser.add_argument("output_pdf", type=Path)
    args = parser.parse_args()

    src = args.input_md
    out = args.output_pdf
    if not src.is_file():
        raise FileNotFoundError(f"Input file not found: {src}")

    html_body = markdown.markdown(
        src.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "toc", "sane_lists", "nl2br"],
    )
    css = """
    body { font-family: 'Segoe UI', Arial, sans-serif; margin: 36px; color: #1f2937; line-height: 1.5; }
    h1, h2, h3 { color: #111827; margin-top: 1.2em; }
    h1 { border-bottom: 2px solid #e5e7eb; padding-bottom: 6px; }
    table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 13px; }
    th, td { border: 1px solid #d1d5db; padding: 8px; vertical-align: top; }
    th { background: #f3f4f6; }
    code { background: #eef2ff; color: #111827; padding: 2px 4px; border-radius: 4px; }
    pre { background: #f8fafc; color: #111827; border: 1px solid #d1d5db; padding: 10px; border-radius: 6px; overflow-x: auto; }
    pre code { background: transparent; color: #111827; }
    blockquote { border-left: 4px solid #9ca3af; margin: 10px 0; padding-left: 10px; color: #4b5563; }
    ul, ol { margin-left: 20px; }
    @page { size: A4; margin: 18mm 14mm; }
    """
    html_doc = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{src.stem}</title>
  <style>{css}</style>
</head>
<body>
{html_body}
</body>
</html>"""

    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / f"{src.stem}.html"
        html_path.write_text(html_doc, encoding="utf-8")
        browser = _browser_path()
        subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--allow-file-access-from-files",
                f"--print-to-pdf={str(out.resolve())}",
                html_path.resolve().as_uri(),
            ],
            check=True,
        )

    print(f"PDF written: {out}")


if __name__ == "__main__":
    main()
