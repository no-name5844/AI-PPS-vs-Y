#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TraceMark 深度枚举程序 v2
- 枚举 PPS 和 Y 极限表达式展开
- 展开基本列中的每一项（嵌套展开）
- 跨系统模式匹配（含偏移修正）
"""

import subprocess
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SEQT = str(Path(__file__).parent / "seqtool.exe")


def run_expand(system, expr, n):
    """运行 seqtool，返回 (展开序列列表, is_standard)"""
    cmd = [SEQT, system, "expand", "-s", expr, "-n", str(n)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        stdout = result.stdout.strip()

        is_standard = "IsStandard: Yes" in stdout
        seq = []

        if "After expand" in stdout:
            after = stdout.split("After expand")[-1]
            if ":" in after:
                after_colon = after.split(":", 1)[1].strip()
                if after_colon.startswith("(") and ")" in after_colon:
                    end = after_colon.index(")")
                    nums = after_colon[1:end].split(",")
                    seq = [int(x.strip()) for x in nums if x.strip()]

        if not seq:
            for line in stdout.split("\n"):
                line = line.strip()
                if not line or line.startswith("[") or "expand" in line.lower() or "IsStandard" in line:
                    continue
                parts = line.split()
                if parts and all(p.lstrip('-').isdigit() for p in parts):
                    seq = [int(p) for p in parts]
                    break

        return seq, is_standard
    except Exception as e:
        return [], False


def extract_fs_terms(seq, original_expr):
    """
    从展开序列中提取基本列各项。
    对简单展开（只加同一元素），基本列每项递增 1。
    返回形如 [(term1_str, term1_vals), ...]
    """
    orig = [int(x) for x in original_expr.split(",")]
    terms = []
    n_orig = len(orig)

    # 方法1: 检测展开模式
    if not seq:
        return terms

    # 尝试检测 "前缀 + 重复尾缀" 模式
    # 先看尾缀是否单一值重复
    tail = seq[-(min(5, len(seq))):]
    tail_set = set(tail)
    if len(tail_set) == 1:
        # 单一尾缀模式
        tail_val = tail[0]
        # 找到前缀结束位置
        i = len(seq) - 1
        while i >= 0 and seq[i] == tail_val:
            i -= 1
        prefix = seq[:i+1]

        # 基本列: prefix + k个tail_val, k = 0, 1, 2, ...
        # 实际上每展开一次加一个 tail_val
        for k in range(len(seq) - len(prefix)):
            term_vals = prefix + [tail_val] * k
            term_str = ",".join(str(x) for x in term_vals)
            terms.append((term_str, term_vals))
    else:
        # 非单一尾缀: 每个展开可能产生不同长度的序列
        # 回退：整个序列就是一项
        terms.append((",".join(str(x) for x in seq), seq))

    return terms


def main():
    pps_max = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    y_max = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    expand_n = int(sys.argv[3]) if len(sys.argv) > 3 else 8

    print("=" * 74)
    print("  TraceMark 深度枚举 v2 - PPS vs Y 记号对应分析")
    print(f"  PPS 极限: 0..{pps_max}  |  Y 极限: 1,2..1,{y_max}  |  展开次数: {expand_n}")
    print("=" * 74)

    # ============================================================
    # 阶段1: 收集所有极限展开
    # ============================================================
    print("\n--- 阶段1: 极限展开收集 ---")

    pps_limits = {}
    for n in range(pps_max + 1):
        expr = ",".join(str(i) for i in range(n + 1))
        seq, std = run_expand("PPS", expr, expand_n)
        pps_limits[expr] = {"seq": seq, "std": std, "n": n}
        print(f"  PPS [{expr:12s}] std={std} len={len(seq)}")

    y_limits = {}
    for n in range(2, y_max + 1):
        expr = f"1,{n}"
        seq, std = run_expand("Y", expr, expand_n)
        y_limits[expr] = {"seq": seq, "std": std, "n": n}
        print(f"  Y   [{expr:12s}] std={std} len={len(seq)}")

    # ============================================================
    # 阶段2: 嵌套展开 - 展开每一个基本列项
    # ============================================================
    print("\n--- 阶段2: 基本列项提取 ---")

    all_pps = {}  # expr_str -> {system, seq_at_expand, ...}
    all_y = {}

    for expr, info in pps_limits.items():
        seq = info["seq"]
        if not seq:
            continue
        terms = extract_fs_terms(seq, expr)
        for t_str, t_vals in terms:
            if t_str and t_str not in all_pps:
                all_pps[t_str] = {"system": "PPS", "vals": t_vals, "parent_limit": expr}

    for expr, info in y_limits.items():
        seq = info["seq"]
        if not seq:
            continue
        terms = extract_fs_terms(seq, expr)
        for t_str, t_vals in terms:
            if t_str and t_str not in all_y:
                all_y[t_str] = {"system": "Y", "vals": t_vals, "parent_limit": expr}

    print(f"  PPS 基本列项: {len(all_pps)} 个")
    print(f"  Y   基本列项: {len(all_y)} 个")

    # ============================================================
    # 阶段3: 跨系统模式匹配
    # ============================================================
    print("\n--- 阶段3: 跨系统模式匹配 ---")

    matched = []

    # 尝试1: 直接值偏移匹配 (PPS值+1 == Y值)
    for pps_expr, pps_info in all_pps.items():
        pps_vals = pps_info["vals"]
        pps_shifted = str([v + 1 for v in pps_vals])
        for y_expr, y_info in all_y.items():
            y_vals = y_info["vals"]
            if len(pps_vals) == len(y_vals):
                if all(a + 1 == b for a, b in zip(pps_vals, y_vals)):
                    matched.append(("shift+1", pps_expr, y_expr, pps_info["parent_limit"], y_info["parent_limit"]))

    # 尝试2: 前缀匹配（去除末尾重复元素后对比）
    for pps_expr, pps_info in all_pps.items():
        pps_vals = pps_info["vals"]
        # 去尾缀重复
        pps_prefix = list(pps_vals)
        while len(pps_prefix) > 1 and pps_prefix[-1] == pps_prefix[-2]:
            pps_prefix.pop()
        for y_expr, y_info in all_y.items():
            y_vals = y_info["vals"]
            y_prefix = list(y_vals)
            while len(y_prefix) > 1 and y_prefix[-1] == y_prefix[-2]:
                y_prefix.pop()
            if len(pps_prefix) == len(y_prefix):
                if all(a + 1 == b for a, b in zip(pps_prefix, y_prefix)):
                    matched.append(("prefix+1", pps_expr, y_expr, pps_info["parent_limit"], y_info["parent_limit"]))

    # 去重
    seen = set()
    unique_matched = []
    for m in matched:
        key = (m[1], m[2])
        if key not in seen:
            seen.add(key)
            unique_matched.append(m)

    if unique_matched:
        print(f"\n  找到 {len(unique_matched)} 个对应:")
        for match_type, pps_e, y_e, pps_lim, y_lim in unique_matched:
            print(f"  [{match_type:10s}] pps {pps_e:20s} = y {y_e:20s}  (极限: pps {pps_lim} / y {y_lim})")
    else:
        print("  未找到直接匹配。")

    # ============================================================
    # 阶段4: 详细展开对比表
    # ============================================================
    print("\n--- 阶段4: PPS vs Y 结构对比 ---")
    print(f"{'PPS 表达式':<24s} {'PPS 展开':<40s} || {'Y 表达式':<24s} {'Y 展开':<40s}")
    print("-" * 130)

    # 对齐显示同级的极限
    max_n = max(pps_max, y_max - 1)
    for n in range(max_n + 1):
        pps_key = ",".join(str(i) for i in range(n + 1))
        y_key = f"1,{n+1}" if n >= 1 else None

        pps_seq = pps_limits.get(pps_key, {}).get("seq", [])
        y_seq = y_limits.get(y_key, {}).get("seq", []) if y_key else []

        pps_str = ",".join(str(x) for x in pps_seq[:20])
        y_str = ",".join(str(x) for x in y_seq[:20])
        if len(pps_seq) > 20:
            pps_str += "..."
        if len(y_seq) > 20:
            y_str += "..."

        pps_label = f"pps {pps_key}"
        y_label = f"y {y_key}" if y_key else ""

        print(f"{pps_label:<24s} {pps_str:<40s} || {y_label:<24s} {y_str:<40s}")

    # ============================================================
    # 阶段5: 生成已知对应表（基于 R1+R2 的确定性推导）
    # ============================================================
    print("\n--- 阶段5: R1+R2 确定性对应链 ---")
    print("(以下由公理和R2纯逻辑推出，不含猜测)")

    # R1: pps 0 = y 1
    print("  [R1 ] pps 0          = y 1")

    # R2 from R1
    print("  [R2 ] pps 0,0        = y 1,1")

    # Known: pps 0,1 = y 1,2
    print("  [Exp] pps 0,1        = y 1,2")

    # R2 chain from pps 0,1 = y 1,2
    print("  [R2 ] pps 0,1,0      = y 1,2,1")
    print("  [R2 ] pps 0,1,0,0    = y 1,2,1,1")
    print("  [R2 ] pps 0,1,0,0,0  = y 1,2,1,1,1")

    # Known: pps 0,1,0,0,3 = y 1,2,1,2
    print("  [Exp] pps 0,1,0,0,3  = y 1,2,1,2")

    # R2 chain from pps 0,1,0,0,3 = y 1,2,1,2
    print("  [R2 ] pps 0,1,0,0,3,0      = y 1,2,1,2,1")
    print("  [R2 ] pps 0,1,0,0,3,0,0    = y 1,2,1,2,1,1")
    print("  [R2 ] pps 0,1,0,0,3,0,0,0  = y 1,2,1,2,1,1,1")


if __name__ == "__main__":
    main()
