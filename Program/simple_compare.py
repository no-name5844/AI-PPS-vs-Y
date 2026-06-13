#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单对比: PPS种子 vs Y浅层 的基本列结构 (+1偏移)"""
import subprocess, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
SEQT = str(Path(__file__).parent / "seqtool.exe")

def e(s, x, n):
    r = subprocess.run([SEQT, s, "expand", "-s", x, "-n", str(n)],
                       capture_output=True, text=True, timeout=15)
    o = r.stdout.strip()
    seq = []
    if "After expand" in o:
        a = o.split("After expand")[-1]
        if ":" in a:
            ac = a.split(":", 1)[1].strip()
            if ac.startswith("(") and ")" in ac:
                end = ac.index(")")
                seq = [int(x.strip()) for x in ac[1:end].split(",") if x.strip()]
    if not seq:
        for l in o.split("\n"):
            p = l.strip().split()
            if p and all(x.lstrip('-').isdigit() for x in p): seq = [int(x) for x in p]; break
    return seq

OUT = str(Path(__file__).parent / "analysis_dump" / "simple_compare.txt")
Path(OUT).parent.mkdir(exist_ok=True)

lines = ["# PPS vs Y 简单结构对比 (+1偏移)", ""]

# ── PPS 种子层 ──
lines.append("## PPS 种子基本列")
lines.append("")
pps_seeds = ["0,1", "0,1,2", "0,1,2,3"]
for ps in pps_seeds:
    fs = [e("PPS", ps, n) for n in range(1, 6)]
    lines.append(f"### pps {ps}")
    for i, fv in enumerate(fs, 1):
        shifted = ",".join(str(x+1) for x in fv)
        lines.append(f"  f[{i}] = {fv}   (+1→ {shifted})")
    lines.append("")

# ── Y 浅层 (从 1,3 树) ──
lines.append("## Y 浅层基本列 (从1,3树)")
lines.append("")
y_exprs = ["1,2", "1,3", "1,2,4", "1,2,3,4", "1,2,3", "1,2,2", "1,2,4,8", "1,2,4,7,11"]
for ye in y_exprs:
    f1 = e("Y", ye, 1)
    f2 = e("Y", ye, 2)
    f3 = e("Y", ye, 3)
    lines.append(f"### y {ye}")
    lines.append(f"  f[1] = {f1}")
    lines.append(f"  f[2] = {f2}")
    if f3: lines.append(f"  f[3] = {f3}")
    lines.append("")

# ── 模式对比: "前缀+无限X" 结构 ──
lines.append("## 模式对比: 前缀+无限X")
lines.append("")
lines.append("| 系统 | 表达式 | 前缀 | +1前缀 | 无限值 |")
lines.append("|:--|:--|:--|:--|:--|")
for label, sys_name, exprs in [("PPS", "PPS", pps_seeds), ("Y", "Y", ["1,2", "1,2,3", "1,2,3,4"])]:
    for ex in exprs:
        s = e(sys_name, ex, 6)
        if not s: continue
        tail = s[-min(5, len(s)):]
        ts = set(tail)
        if len(ts) == 1:
            tv = tail[0]; i = len(s)-1
            while i >= 0 and s[i] == tv: i -= 1
            pre = s[:i+1] if i >= 0 else []
            pre1 = [x+1 for x in pre]
            lines.append(f"| {label} | {ex:14s} | {pre} | {pre1} | {tv} |")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Written to {OUT}")
