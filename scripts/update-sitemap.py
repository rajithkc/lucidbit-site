#!/usr/bin/env python3
"""Refresh only sitemap URLs whose HTML changed; never bump every URL per deploy."""
from datetime import date
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlparse

root = Path(__file__).resolve().parent.parent
changed = set()
for args in (["git", "diff", "--name-only", "HEAD", "--"],
             ["git", "ls-files", "--others", "--exclude-standard"]):
    changed.update(subprocess.check_output(args, cwd=root, text=True).splitlines())
p = root / "sitemap.xml"
s = p.read_text()

def update(match):
    block = match.group()
    loc = re.search(r"<loc>(.*?)</loc>", block)
    if not loc:
        return block
    path = unquote(urlparse(loc[1]).path).lstrip("/")
    if not path or path.endswith("/"):
        path += "index.html"
    if path in changed:
        return re.sub(r"<lastmod>.*?</lastmod>",
                      f"<lastmod>{date.today().isoformat()}</lastmod>", block)
    return block

updated = re.sub(r"<url>.*?</url>", update, s, flags=re.S)
if updated != s:
    p.write_text(updated)
