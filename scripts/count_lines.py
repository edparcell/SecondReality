#!/usr/bin/env python3
"""
count_lines.py — Line-of-code counter for the Second Reality project.

Counts total lines, blank lines, comment lines, and code lines
for each language group, then prints a comparison table.

Usage:
    python scripts/count_lines.py [repo_root]
    (defaults to the directory containing this script's parent)
"""

import os
import sys
import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Language definitions: map file extensions to (language_name, comment_prefix)
# ---------------------------------------------------------------------------
LANGUAGES = {
    # Original source
    ".c":   ("C",           "//",   "/*"),
    ".h":   ("C header",   "//",   "/*"),
    ".asm": ("x86 ASM",    ";",    None),
    ".inc": ("ASM include", ";",    None),
    # Python recreation
    ".py":  ("Python",     "#",    None),
    ".frag":("GLSL frag",  "//",   "/*"),
    ".vert":("GLSL vert",  "//",   "/*"),
    # Documentation
    ".md":  ("Markdown",   None,   None),   # no real 'comments'
}

# Groups for the summary table
GROUPS = {
    "Original C":         ([".c", ".h"],        "original/"),
    "Original ASM":       ([".asm", ".inc"],     "original/"),
    "Python (parts+demo)":([".py"],              "Python/"),
    "GLSL shaders":       ([".frag", ".vert"],   "Python/"),
    "Knowledge (Markdown)":([".md"],             "knowledge/"),
    "Scripts":            ([".py"],              "scripts/"),
}


def is_comment_line(line: str, ext: str) -> bool:
    """Heuristic: is this (stripped) line predominantly a comment?"""
    s = line.strip()
    if not s:
        return False
    lang = LANGUAGES.get(ext, None)
    if lang is None:
        return False
    _, single, block_open = lang
    if single and s.startswith(single):
        return True
    if block_open and s.startswith(block_open):
        return True
    # ASM: lines starting with ; anywhere in leading whitespace
    if ext in (".asm", ".inc") and s.startswith(";"):
        return True
    return False


def count_file(path: Path) -> dict:
    ext = path.suffix.lower()
    counts = {"total": 0, "blank": 0, "comment": 0, "code": 0}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return counts
    for line in text.splitlines():
        counts["total"] += 1
        stripped = line.strip()
        if not stripped:
            counts["blank"] += 1
        elif is_comment_line(stripped, ext):
            counts["comment"] += 1
        else:
            counts["code"] += 1
    return counts


def gather(root: Path, extensions: list[str], subdir: str) -> dict:
    """Walk subdir under root, collecting counts for given extensions."""
    totals = defaultdict(int)
    file_count = 0
    search_root = root / subdir.rstrip("/")
    if not search_root.exists():
        return dict(totals), 0
    for path in search_root.rglob("*"):
        if path.suffix.lower() in extensions and path.is_file():
            c = count_file(path)
            for k, v in c.items():
                totals[k] += v
            file_count += 1
    return dict(totals), file_count


def human(n: int) -> str:
    return f"{n:,}"


def main():
    repo_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent
    repo_root = repo_root.resolve()

    print(f"\nSecond Reality — Line Count Report")
    print(f"Repository root: {repo_root}")
    print()

    # -----------------------------------------------------------------------
    # Per-group summary
    # -----------------------------------------------------------------------
    col_w = [32, 8, 8, 10, 10, 8]
    header = ["Group", "Files", "Total", "Code", "Comments", "Blank"]
    sep    = "  ".join("-" * w for w in col_w)
    row_fmt = "  ".join(f"{{:<{w}}}" for w in col_w)

    print(row_fmt.format(*header))
    print(sep)

    grand = defaultdict(int)
    group_results = {}

    for group_name, (exts, subdir) in GROUPS.items():
        counts, nfiles = gather(repo_root, exts, subdir)
        group_results[group_name] = (counts, nfiles)
        total   = counts.get("total",   0)
        code    = counts.get("code",    0)
        comment = counts.get("comment", 0)
        blank   = counts.get("blank",   0)
        print(row_fmt.format(
            group_name,
            human(nfiles),
            human(total),
            human(code),
            human(comment),
            human(blank),
        ))
        for k in ("total", "code", "comment", "blank"):
            grand[k] += counts.get(k, 0)

    print(sep)
    print(row_fmt.format(
        "TOTAL (all groups)",
        "",
        human(grand["total"]),
        human(grand["code"]),
        human(grand["comment"]),
        human(grand["blank"]),
    ))

    # -----------------------------------------------------------------------
    # Original vs Python comparison
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("  ORIGINAL (C + ASM) vs PYTHON RECREATION")
    print("=" * 60)

    orig_c,   orig_c_n   = group_results["Original C"]
    orig_asm, orig_asm_n = group_results["Original ASM"]
    py,       py_n       = group_results["Python (parts+demo)"]
    glsl,     glsl_n     = group_results["GLSL shaders"]

    orig_total = orig_c.get("total", 0) + orig_asm.get("total", 0)
    orig_code  = orig_c.get("code",  0) + orig_asm.get("code",  0)
    orig_files = orig_c_n + orig_asm_n

    py_total   = py.get("total",  0) + glsl.get("total",  0)
    py_code    = py.get("code",   0) + glsl.get("code",   0)
    py_files   = py_n + glsl_n

    ratio_total = py_total / orig_total if orig_total else 0
    ratio_code  = py_code  / orig_code  if orig_code  else 0

    print(f"  {'':30s}  {'Original':>10}  {'Python+GLSL':>12}")
    print(f"  {'-'*56}")
    print(f"  {'Source files':30s}  {human(orig_files):>10}  {human(py_files):>12}")
    print(f"  {'Total lines':30s}  {human(orig_total):>10}  {human(py_total):>12}")
    print(f"  {'Code lines (non-blank/comment)':30s}  {human(orig_code):>10}  {human(py_code):>12}")
    print(f"  {'':30s}  {'':>10}  {'':>12}")
    print(f"  {'Python/GLSL ÷ Original (total)':30s}  {'':>10}  {ratio_total:>11.2f}×")
    print(f"  {'Python/GLSL ÷ Original (code)':30s}  {'':>10}  {ratio_code:>11.2f}×")
    print()

    # -----------------------------------------------------------------------
    # Extension breakdown for original
    # -----------------------------------------------------------------------
    print("  Original — breakdown by extension:")
    for ext in [".c", ".h", ".asm", ".inc"]:
        counts, nf = gather(repo_root, [ext], "original/")
        if nf:
            print(f"    {ext:6s}  {human(nf):>5} files  {human(counts['total']):>7} lines  "
                  f"({human(counts['code'])} code)")

    print()
    print("  Python recreation — breakdown by type:")
    for ext in [".py", ".frag", ".vert"]:
        subdir = "Python/"
        counts, nf = gather(repo_root, [ext], subdir)
        if nf:
            print(f"    {ext:6s}  {human(nf):>5} files  {human(counts['total']):>7} lines  "
                  f"({human(counts['code'])} code)")

    print()


if __name__ == "__main__":
    main()
