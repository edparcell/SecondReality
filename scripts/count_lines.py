#!/usr/bin/env python3
"""
count_lines.py — Line-of-code counter for the Second Reality project.

Classifies each source line as: blank / comment / data / code.

"Data" lines are pre-computed lookup tables and embedded binary blobs —
lines that carry no algorithmic logic, just numeric values the code reads
at runtime.  They inflate the raw line count without representing human-
written logic.

Detection rules
---------------
ASM / INC  — line starts with a data-directive keyword:
               dw, db, dd, dq, dt  (Word / Byte / Doubleword / Quadword / Ten-byte)
             These cover sine tables, palette tables, protection blobs,
             zoom jump-tables (dw OFFSET label), etc.

C / H      — line consists almost entirely of comma-separated numeric
             literals (decimal or 0x hex), with optional braces/semicolons
             and at most a trailing // comment.
             Rule: ≥3 numeric tokens AND the non-whitespace portion is
             ≥80% "numeric punctuation" chars (digits, commas, minus,
             0x-prefix chars, braces, semicolons).

GLSL / Python / Markdown — no data classification applied
             (they contain no embedded lookup tables).

Usage:
    python scripts/count_lines.py [repo_root]
"""

import re
import sys
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# ASM data directive: dw / db / dd / dq / dt  (case-insensitive)
_ASM_DATA_RE = re.compile(r'^\s*(dw|db|dd|dq|dt)\b', re.IGNORECASE)

# A single numeric literal: decimal integer or 0x hex
_NUM = r'-?(?:0x[0-9a-fA-F]+|[0-9]+)'
# C data line: optional { or ,  then 3+ comma-separated numbers, then optional ,;}
# plus optional // comment at end
_C_DATA_RE = re.compile(
    r'^\s*[\{,]?\s*'
    + _NUM
    + r'(?:\s*,\s*' + _NUM + r'){2,}'   # at least 2 more = 3 total
    + r'\s*[,;\}]?\s*(?://.*)?$'
)
# Characters considered "numeric punctuation" for the density check
_NUM_CHARS = re.compile(r'[0-9,\-\{\};\sxXaAbBcCdDeEfF]')

# Comment starters per extension
_COMMENT_STARTS = {
    ".c":    ("//", "/*"),
    ".h":    ("//", "/*"),
    ".asm":  (";",),
    ".inc":  (";",),
    ".py":   ("#",),
    ".frag": ("//", "/*"),
    ".vert": ("//", "/*"),
}


# ---------------------------------------------------------------------------
# Per-line classifier
# ---------------------------------------------------------------------------

def classify(line: str, ext: str) -> str:
    """Return 'blank' | 'comment' | 'data' | 'code'."""
    s = line.strip()
    if not s:
        return "blank"

    # Comment?
    for prefix in _COMMENT_STARTS.get(ext, ()):
        if s.startswith(prefix):
            return "comment"

    # Data?
    if ext in (".asm", ".inc"):
        if _ASM_DATA_RE.match(s):
            return "data"

    elif ext in (".c", ".h"):
        if _C_DATA_RE.match(s):
            # Density check: non-whitespace chars must be ≥80% numeric-ish
            non_ws = s.replace(" ", "").replace("\t", "")
            numeric_chars = len(_NUM_CHARS.sub("", non_ws)) == 0 or (
                len(_NUM_CHARS.findall(non_ws)) / max(len(non_ws), 1) >= 0.80
            )
            if numeric_chars:
                return "data"

    return "code"


# ---------------------------------------------------------------------------
# File and directory counters
# ---------------------------------------------------------------------------

def count_file(path: Path) -> dict[str, int]:
    ext = path.suffix.lower()
    counts: dict[str, int] = defaultdict(int)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return counts
    for line in text.splitlines():
        counts["total"] += 1
        counts[classify(line, ext)] += 1
    return dict(counts)


def gather(root: Path, extensions: list[str], subdir: str) -> tuple[dict, int]:
    totals: dict[str, int] = defaultdict(int)
    file_count = 0
    search_root = root / subdir.rstrip("/")
    if not search_root.exists():
        return dict(totals), 0
    for path in sorted(search_root.rglob("*")):
        if path.suffix.lower() in extensions and path.is_file():
            for k, v in count_file(path).items():
                totals[k] += v
            file_count += 1
    return dict(totals), file_count


def h(n: int) -> str:
    return f"{n:,}"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

GROUPS = [
    ("Original C",              [".c", ".h"],        "original/"),
    ("Original ASM/INC",        [".asm", ".inc"],     "original/"),
    ("Python (parts+framework)",[".py"],              "Python/"),
    ("GLSL shaders",            [".frag", ".vert"],   "Python/"),
    ("Knowledge (Markdown)",    [".md"],              "knowledge/"),
    ("Scripts",                 [".py"],              "scripts/"),
]


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else
                Path(__file__).parent.parent).resolve()

    print(f"\nSecond Reality — Line Count Report")
    print(f"Root: {root}\n")

    col_w   = [32, 7, 8, 8, 8, 8, 8]
    headers = ["Group", "Files", "Total", "Code", "Data", "Comment", "Blank"]
    sep     = "  ".join("-" * w for w in col_w)
    fmt     = "  ".join(f"{{:<{w}}}" for w in col_w)

    print(fmt.format(*headers))
    print(sep)

    grand: dict[str, int] = defaultdict(int)
    results: dict[str, tuple[dict, int]] = {}

    for name, exts, sub in GROUPS:
        c, nf = gather(root, exts, sub)
        results[name] = (c, nf)
        print(fmt.format(
            name,
            h(nf),
            h(c.get("total",   0)),
            h(c.get("code",    0)),
            h(c.get("data",    0)),
            h(c.get("comment", 0)),
            h(c.get("blank",   0)),
        ))
        for k in ("total", "code", "data", "comment", "blank"):
            grand[k] += c.get(k, 0)

    print(sep)
    print(fmt.format(
        "TOTAL", "",
        h(grand["total"]), h(grand["code"]), h(grand["data"]),
        h(grand["comment"]), h(grand["blank"]),
    ))

    # -----------------------------------------------------------------------
    # Comparison table: original vs Python
    # -----------------------------------------------------------------------
    print("\n" + "=" * 68)
    print("  ORIGINAL (C + ASM) vs PYTHON+GLSL RECREATION")
    print("=" * 68)

    def g(name, key):
        return results[name][0].get(key, 0)

    orig_files   = results["Original C"][1]      + results["Original ASM/INC"][1]
    orig_total   = g("Original C","total")        + g("Original ASM/INC","total")
    orig_code    = g("Original C","code")         + g("Original ASM/INC","code")
    orig_data    = g("Original C","data")         + g("Original ASM/INC","data")
    orig_logical = orig_code  # data excluded

    py_files     = results["Python (parts+framework)"][1] + results["GLSL shaders"][1]
    py_total     = g("Python (parts+framework)","total") + g("GLSL shaders","total")
    py_code      = g("Python (parts+framework)","code")  + g("GLSL shaders","code")
    py_data      = g("Python (parts+framework)","data")  + g("GLSL shaders","data")
    py_logical   = py_code

    lbl = 36
    print(f"\n  {'':>{lbl}}  {'Original':>10}  {'Python+GLSL':>12}")
    print(f"  {'-'*62}")
    print(f"  {'Source files':<{lbl}}  {h(orig_files):>10}  {h(py_files):>12}")
    print(f"  {'Total lines (everything)':>{lbl}}  {h(orig_total):>10}  {h(py_total):>12}")
    print(f"  {'  of which: pre-computed data tables':>{lbl}}  {h(orig_data):>10}  {h(py_data):>12}")
    print(f"  {'  of which: logic/code lines':>{lbl}}  {h(orig_logical):>10}  {h(py_logical):>12}")
    print(f"  {'  of which: comments':>{lbl}}  "
          f"{h(g('Original C','comment')+g('Original ASM/INC','comment')):>10}  "
          f"{h(g('Python (parts+framework)','comment')+g('GLSL shaders','comment')):>12}")
    print()
    ratio_total   = py_total   / orig_total   if orig_total   else 0
    ratio_logical = py_logical / orig_logical if orig_logical else 0
    ratio_data    = py_data    / orig_data    if orig_data    else 0
    print(f"  {'Python ÷ Original  (total lines)':>{lbl}}  {'':>10}  {ratio_total:>11.3f}×")
    print(f"  {'Python ÷ Original  (logic only)':>{lbl}}  {'':>10}  {ratio_logical:>11.3f}×")
    print(f"  {'Python ÷ Original  (data only)':>{lbl}}  {'':>10}  {ratio_data:>11.3f}×")

    # -----------------------------------------------------------------------
    # Per-extension breakdown for original
    # -----------------------------------------------------------------------
    print("\n  Original — per extension:")
    print(f"  {'':4}  {'ext':6}  {'files':>6}  {'total':>7}  {'code':>7}  "
          f"{'data':>7}  {'comment':>7}  {'blank':>6}")
    for ext in [".c", ".h", ".asm", ".inc"]:
        c, nf = gather(root, [ext], "original/")
        if nf:
            print(f"       {ext:6}  {h(nf):>6}  {h(c.get('total',0)):>7}  "
                  f"{h(c.get('code',0)):>7}  {h(c.get('data',0)):>7}  "
                  f"{h(c.get('comment',0)):>7}  {h(c.get('blank',0)):>6}")

    print("\n  Python+GLSL — per extension:")
    for ext in [".py", ".frag", ".vert"]:
        c, nf = gather(root, [ext], "Python/")
        if nf:
            print(f"       {ext:6}  {h(nf):>6}  {h(c.get('total',0)):>7}  "
                  f"{h(c.get('code',0)):>7}  {h(c.get('data',0)):>7}  "
                  f"{h(c.get('comment',0)):>7}  {h(c.get('blank',0)):>6}")
    print()


if __name__ == "__main__":
    main()
