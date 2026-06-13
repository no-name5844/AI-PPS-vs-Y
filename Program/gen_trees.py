#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TraceMark 完整树展开生成器
- Y: 种子 1,2 + 1,3（唯一需要的大种子）
- PPS: 种子 0, 0,1, 0,1,2, 0,1,2,3, 0,1,2,3,4
- 输出到 analysis_dump/ 目录
"""
import subprocess, sys, io, os
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
SEQT = str(Path(__file__).parent / "seqtool.exe")
OUT_DIR = str(Path(__file__).parent / "analysis_dump")
os.makedirs(OUT_DIR, exist_ok=True)

_cache = {}

def expand(system, expr, n):
    k = f"{system}:{expr}:{n}"
    if k in _cache:
        return _cache[k]
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
            parts = line.strip().split()
            if parts and all(p.lstrip('-').isdigit() for p in parts):
                seq = [int(p) for p in parts]
                break
    _cache[k] = (seq, std)
    return seq, std


def describe(seq):
    if not seq:
        return "()"
    tail = seq[-min(5, len(seq)):]
    ts = set(tail)
    if len(ts) == 1:
        tv = tail[0]
        i = len(seq) - 1
        while i >= 0 and seq[i] == tv:
            i -= 1
        pre = seq[:i + 1] if i >= 0 else []
        return f"pre={pre} +inf_{tv}"
    s = ",".join(str(x) for x in seq[:10])
    if len(seq) > 10:
        s += f"...(len={len(seq)})"
    return s


def gen_tree(system, seeds, max_depth, expand_n, out_path):
    """生成表达式树并写入文件"""
    lines = []
    lines.append(f"# {system} Tree Expansion")
    lines.append(f"# Seeds: {seeds}  MaxDepth: {max_depth}  ExpandN: {expand_n}")
    lines.append("")
    visited = set()

    def walk(expr, depth, indent=""):
        key = f"{system}:{expr}"
        if key in visited or depth > max_depth:
            return
        visited.add(key)

        seq, std = expand(system, expr, expand_n)
        desc = describe(seq)
        lim_tag = "[L]" if len(seq) > 0 else "[S]"
        lines.append(f"{indent}{lim_tag} {expr:30s}  std={std}  {desc}")

        if not seq or not std:
            return

        # 提取基本列项
        terms = extract_fs(seq, expr, system, expand_n)
        if depth < max_depth:
            for t in terms[:expand_n]:
                walk(t, depth + 1, indent + "  ")

    for seed in seeds:
        lines.append(f"## SEED: {system} {seed}")
        walk(seed, 0, "")
        lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return len(visited)


def extract_fs(seq, orig, system, n):
    """从展开序列提取基本列各项"""
    if not seq:
        return []
    tail = seq[-min(5, len(seq)):]
    ts = set(tail)
    if len(ts) == 1:
        tv = tail[0]
        i = len(seq) - 1
        while i >= 0 and seq[i] == tv:
            i -= 1
        pre = seq[:i + 1] if i >= 0 else []
        cur = list(pre) if pre else []
        terms = []
        for k in range(n):
            t = ",".join(str(x) for x in cur)
            if t and t != orig:
                terms.append(t)
            cur = cur + [tv]
        return terms
    terms = []
    for n2 in range(1, n + 1):
        s2, _ = expand(system, orig, n2)
        if s2:
            t = ",".join(str(x) for x in s2)
            if t != orig:
                terms.append(t)
    return terms


def main():
    import sys
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    expand_n = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print(f"深度={depth} 展开数={expand_n}")

    # ── Y Tree ──
    print("生成 Y 树...")
    y_seeds = ["1,2", "1,3"]
    y_nodes = gen_tree("Y", y_seeds, depth, expand_n,
                       os.path.join(OUT_DIR, "y_tree_full.txt"))
    print(f"  Y: {y_nodes} 节点")

    # ── PPS Tree ──
    print("生成 PPS 树...")
    pps_seeds = [",".join(str(i) for i in range(k + 1)) for k in range(6)]
    pps_nodes = gen_tree("PPS", pps_seeds, depth, expand_n,
                         os.path.join(OUT_DIR, "pps_tree_full.txt"))
    print(f"  PPS: {pps_nodes} 节点")

    print(f"\n完成: {OUT_DIR}/")
    print(f"  y_tree_full.txt")
    print(f"  pps_tree_full.txt")


if __name__ == "__main__":
    main()
