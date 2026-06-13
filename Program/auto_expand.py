#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TraceMark 自动展开器 - 持续运行，不断生成展开数据。
保存到 analysis_dump/expand_data/ 目录。
"""
import subprocess, os, time, json
from pathlib import Path
from collections import deque

SEQT = str(Path(__file__).parent / "seqtool.exe")
OUT_DIR = str(Path.home() / "WorkBuddy" / "2026-06-07-17-38-56" / "expand_data")
os.makedirs(OUT_DIR, exist_ok=True)

DELAY = 0.05  # 每次调用间隔(秒)

def run(system, expr, n):
    """运行 seqtool expand，返回 (seq, is_standard)"""
    cmd = [SEQT, system, "expand", "-s", expr, "-n", str(n)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    out = r.stdout.strip(); err = r.stderr.strip()
    std = "IsStandard: Yes" in out
    seq = []
    if "After expand" in out:
        a = out.split("After expand")[-1]
        if ":" in a:
            ac = a.split(":", 1)[1].strip()
            if ac.startswith("(") and ")" in ac:
                end = ac.index(")")
                seq = [int(x.strip()) for x in ac[1:end].split(",") if x.strip()]
    if not seq:
        for line in (out + "\n" + err).split("\n"):
            p = line.strip().split()
            if p and all(x.lstrip('-').isdigit() for x in p):
                seq = [int(x) for x in p]; break
    time.sleep(DELAY)
    return seq, std

def extract_fs(seq, orig, system, max_n=6):
    """从展开序列提取基本列各项"""
    if not seq: return []
    tail = seq[-min(5, len(seq)):]
    ts = set(tail)
    if len(ts) == 1:
        tv = tail[0]; i = len(seq) - 1
        while i >= 0 and seq[i] == tv: i -= 1
        pre = seq[:i+1] if i >= 0 else []
        cur = list(pre) if pre else []; terms = []
        for k in range(max_n):
            t = ",".join(str(x) for x in cur)
            if t and t != orig: terms.append(t)
            cur = cur + [tv]
        return terms
    terms = []
    for n2 in range(1, max_n + 1):
        s2, _ = run(system, orig, n2)
        if s2:
            t = ",".join(str(x) for x in s2)
            if t != orig: terms.append(t)
    return terms

def main():
    visited = set()
    queue = deque()
    results = {}

    # 种子
    for n in range(8):
        queue.append(("PPS", ",".join(str(i) for i in range(n+1)), 0))
    queue.append(("Y", "1,2", 0))
    queue.append(("Y", "1,3", 0))

    batch = []
    last_save = time.time()

    print("AutoExpand started. Output:", OUT_DIR)
    print("Press Ctrl+C to stop.\n")

    try:
        while queue:
            system, expr, depth = queue.popleft()
            key = f"{system}:{expr}"
            if key in visited or depth > 5:
                continue
            visited.add(key)

            seq, std = run(system, expr, 6)
            if not std:
                continue

            fs = extract_fs(seq, expr, system, 6)
            results[key] = {"seq": seq, "std": std, "depth": depth, "fs": fs}

            status = f"[{len(visited):5d}] {system}:{expr:30s} depth={depth} std={std} fs={len(fs)}"
            print(status)
            batch.append(status)

            for t in fs[:4]:
                if f"{system}:{t}" not in visited:
                    queue.append((system, t, depth + 1))

            # 定期保存
            if time.time() - last_save > 30:
                _save(results, batch)
                batch = []
                last_save = time.time()

    except KeyboardInterrupt:
        print("\nStopping...")

    _save(results, batch)
    print(f"\nDone. {len(visited)} expressions saved.")


def _save(results, batch):
    ts = time.strftime("%Y%m%d_%H%M%S")
    # 保存完整结果
    out = {"timestamp": ts, "count": len(results), "data": {}}
    for k, v in results.items():
        out["data"][k] = {
            "seq": v["seq"],
            "std": v["std"],
            "depth": v["depth"],
            "fs": v["fs"]
        }
    with open(os.path.join(OUT_DIR, f"expand_{ts}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    # 保存日志
    with open(os.path.join(OUT_DIR, f"log_{ts}.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(batch))
    print(f"  Saved expand_{ts}.json ({len(results)} entries)")


if __name__ == "__main__":
    main()
