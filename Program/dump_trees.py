#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TraceMark 完整展开 dump
将所有 PPS 和 Y 树展开结果保存到 analysis/ 目录。
"""
import subprocess, sys, io, os
from pathlib import Path
from collections import OrderedDict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SEQT = str(Path(__file__).parent / "seqtool.exe")
OUT_DIR = str(Path(__file__).parent / "analysis_dump")
os.makedirs(OUT_DIR, exist_ok=True)


def expand(system, expr, n):
    cmd = [SEQT, system, "expand", "-s", expr, "-n", str(n)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    out = r.stdout.strip()
    std = "IsStandard: Yes" in out
    seq = []
    if "After expand" in out:
        after = out.split("After expand")[-1]
        if ":" in after:
            ac = after.split(":", 1)[1].strip()
            if ac.startswith("(") and ")" in ac:
                end = ac.index(")")
                seq = [int(x.strip()) for x in ac[1:end].split(",") if x.strip()]
    if not seq:
        for line in out.split("\n"):
            line = line.strip()
            if not line or line.startswith("[") or "expand" in line.lower() or "IsStandard" in line:
                continue
            parts = line.split()
            if parts and all(p.lstrip('-').isdigit() for p in parts):
                seq = [int(p) for p in parts]
                break
    return seq, std


def describe(seq):
    if not seq: return "空"
    tail = seq[-min(5, len(seq)):]
    ts = set(tail)
    if len(ts) == 1:
        i = len(seq)-1
        while i >= 0 and seq[i] == tail[0]: i -= 1
        pre = seq[:i+1] if i >= 0 else []
        return f"前缀{pre}+无限{tail[0]}"
    s = ",".join(str(x) for x in seq[:15])
    if len(seq) > 15: s += "..."
    return s


def tree_dump(system, expr, depth, max_depth, expand_n, visited, lines, indent=""):
    key = f"{system}:{expr}"
    if key in visited or depth > max_depth:
        return
    visited.add(key)
    seq, std = run_or_get(system, expr, expand_n)
    if not std and not seq:
        lines.append(f"{indent}[{system}] {expr} (base/successor)")
        return

    desc = describe(seq)
    lines.append(f"{indent}[{system}] {expr}  std={std}  |→ {desc}")

    # Extract fundamental sequence terms
    terms = extract_terms(seq, expr, system, expand_n)
    for i, term in enumerate(terms[:expand_n]):
        tree_dump(system, term, depth + 1, max_depth, expand_n, visited, lines, indent + "  ")


# Cache to avoid repeated calls
_cache = {}

def run_or_get(system, expr, n):
    key = f"{system}:{expr}:{n}"
    if key in _cache:
        return _cache[key]
    result = expand(system, expr, n)
    _cache[key] = result
    return result


def extract_terms(seq, orig_expr, system, expand_n):
    """从展开序列提取基本列项"""
    if not seq: return []
    orig = [int(x) for x in orig_expr.split(",")]

    # Detect single-value tail pattern
    tail = seq[-min(5, len(seq)):]
    ts = set(tail)
    if len(ts) == 1:
        tv = tail[0]
        i = len(seq) - 1
        while i >= 0 and seq[i] == tv: i -= 1
        pre = seq[:i+1] if i >= 0 else []

        # Reconstruct terms: each fundamental sequence term adds one tv
        start = list(pre) if pre else []
        terms = []
        for k in range(expand_n):
            term_str = ",".join(str(x) for x in start)
            if term_str and term_str != orig_expr:
                terms.append(term_str)
            start = start + [tv]
        return terms

    # For non-uniform tails, expand individually
    terms = []
    for n in range(1, expand_n + 1):
        s, _ = run_or_get(system, orig_expr, n)
        if s:
            term_str = ",".join(str(x) for x in s)
            if term_str != orig_expr:
                terms.append(term_str)
    return terms


def main():
    pps_max = 3
    y_max = 4
    depth_max = 4
    expand_n = 5

    # ── PPS dump ──
    pps_seeds = [",".join(str(i) for i in range(k+1)) for k in range(pps_max+1)]
    pps_lines = ["# PPS 树状展开 dump", f"# 种子: {pps_seeds}  最大深度: {depth_max}  展开: {expand_n}", ""]
    for seed in pps_seeds:
        pps_lines.append(f"\n## 种子: pps {seed}")
        tree_dump("PPS", seed, 0, depth_max, expand_n, set(), pps_lines, "")
    with open(os.path.join(OUT_DIR, "pps_tree.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(pps_lines))
    print(f"PPS dump: {OUT_DIR}/pps_tree.txt ({len(pps_lines)} 行)")

    # ── Y dump ──
    y_seeds = [f"1,{k}" for k in range(2, y_max+1)]
    y_lines = ["# Y 树状展开 dump", f"# 种子: {y_seeds}  最大深度: {depth_max}  展开: {expand_n}", ""]
    for seed in y_seeds:
        y_lines.append(f"\n## 种子: y {seed}")
        tree_dump("Y", seed, 0, depth_max, expand_n, set(), y_lines, "")
    with open(os.path.join(OUT_DIR, "y_tree.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(y_lines))
    print(f"Y dump: {OUT_DIR}/y_tree.txt ({len(y_lines)} 行)")

    # ── 对比 dump ──
    comp_lines = ["# PPS vs Y 结构对比", ""]
    comp_lines.append(f"{'PPS 表达式':<30s} {'展开模式':<40s} || {'Y 表达式':<30s} {'展开模式'}")
    comp_lines.append("-" * 140)

    all_pps = OrderedDict()
    for seed in pps_seeds:
        seq, std = run_or_get("PPS", seed, expand_n)
        if seq:
            all_pps[seed] = (seq, std, describe(seq))

    all_y = OrderedDict()
    for seed in y_seeds:
        seq, std = run_or_get("Y", seed, expand_n)
        if seq:
            all_y[seed] = (seq, std, describe(seq))

    max_n = max(pps_max, y_max - 1)
    for n in range(max_n + 1):
        pk = ",".join(str(i) for i in range(n + 1))
        yk = f"1,{n+1}" if n >= 1 else None
        pd = all_pps.get(pk, (None, None, "—"))[2]
        yd = all_y.get(yk, (None, None, "—"))[2] if yk else "—"
        comp_lines.append(f"pps {pk:<27s} {pd:<40s} || y {yk or '—':<28s} {yd}")

    with open(os.path.join(OUT_DIR, "comparison.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(comp_lines))
    print(f"对比: {OUT_DIR}/comparison.txt ({len(comp_lines)} 行)")

    print("\nDone!")


if __name__ == "__main__":
    main()
