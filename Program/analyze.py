#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TraceMark 底向上递归分析
- 从已知对应出发(R1: pps0=y1)
- R2链扩展后继
- R3夹逼验证极限
- 迭代直到无法新增
"""
import subprocess, sys, io, os
from pathlib import Path
from collections import OrderedDict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
SEQT = str(Path(__file__).parent / "seqtool.exe")

_cache = {}
def e(s, x, n):
    k = f"{s}:{x}:{n}"
    if k in _cache: return _cache[k]
    r = subprocess.run([SEQT, s, "expand", "-s", x, "-n", str(n)],
                       capture_output=True, text=True, timeout=15)
    o = r.stdout.strip()
    std = "IsStandard: Yes" in o
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
            if p and all(x.lstrip('-').isdigit() for x in p):
                seq = [int(p) for p in p]; break
    _cache[k] = (seq, std)
    return seq, std


def pps_to_y(pps_expr, known):
    """用已知对应+R2链，将PPS表达式转换为Y表达式"""
    if pps_expr in known:
        return known[pps_expr]
    # R2反向: 如果末尾是,0，去掉,0递归转换再加,1
    if pps_expr.endswith(",0"):
        base = pps_expr[:-2]
        y_base = pps_to_y(base, known)
        if y_base is not None:
            return y_base + ",1"
    return None


def y_to_pps(y_expr, known):
    """反向: Y→PPS"""
    for pk, yk in known.items():
        if yk == y_expr:
            return pk
    if y_expr.endswith(",1"):
        base = y_expr[:-2]
        pps_base = y_to_pps(base, known)
        if pps_base is not None:
            return pps_base + ",0"
    return None


def within_system_compare(sys_name, a, b):
    """在同一系统内比较两个表达式的大小"""
    r = subprocess.run([SEQT, sys_name, "compare", "-s", a, "-s", b],
                       capture_output=True, text=True, timeout=10)
    out = r.stdout.strip()
    if "Seq1 > Seq2" in out:
        return 1   # a > b
    elif "Seq1 < Seq2" in out:
        return -1  # a < b
    elif "Seq1 == Seq2" in out:
        return 0
    return None


def extract_fs(seq, orig, system, n):
    if not seq: return []
    tail = seq[-min(5, len(seq)):]
    ts = set(tail)
    if len(ts) == 1:
        tv = tail[0]; i = len(seq) - 1
        while i >= 0 and seq[i] == tv: i -= 1
        pre = seq[:i + 1] if i >= 0 else []
        cur = list(pre) if pre else []
        terms = []
        for k in range(n):
            t = ",".join(str(x) for x in cur)
            if t and t != orig: terms.append(t)
            cur = cur + [tv]
        return terms
    terms = []
    for n2 in range(1, n + 1):
        s2, _ = e(system, orig, n2)
        if s2:
            t = ",".join(str(x) for x in s2)
            if t != orig: terms.append(t)
    return terms


def verify_r3(pps_expr, y_expr, known, n_check=5):
    """R3夹逼验证: pps_expr = y_expr?"""
    pps_seq, _ = e("PPS", pps_expr, n_check + 2)
    y_seq, _ = e("Y", y_expr, n_check + 2)

    pps_fs = extract_fs(pps_seq, pps_expr, "PPS", n_check)
    y_fs = extract_fs(y_seq, y_expr, "Y", n_check + 2)

    if not pps_fs or not y_fs:
        return False

    for n, pps_fn in enumerate(pps_fs[:n_check]):
        # 转换pps_fn到Y
        y_equiv = pps_to_y(pps_fn, known)
        if y_equiv is None:
            return False  # 无法转换，暂不能验证

        # 找m: y_fs[m] ≤ y_equiv
        found_m = False
        for m, y_fm in enumerate(y_fs):
            if within_system_compare("Y", y_fm, y_equiv) <= 0:
                found_m = True
                break
        if not found_m:
            return False

        # 找k: y_equiv ≤ y_fs[k]
        found_k = False
        for k, y_fk in enumerate(y_fs):
            if within_system_compare("Y", y_equiv, y_fk) <= 0:
                found_k = True
                break
        if not found_k:
            return False

    return True


def main():
    # 初始已知对应
    known = OrderedDict()
    known["0"] = "1"  # R1

    expand_n = 6
    n_check = 5

    print("=" * 70)
    print("  TraceMark 底向上递归分析")
    print(f"  初始: pps 0 = y 1")
    print("=" * 70)

    round_num = 0
    while True:
        round_num += 1
        added_this_round = 0

        # 步骤1: R2链扩展
        new_r2 = OrderedDict()
        for pk, yk in known.items():
            pk2 = pk + ",0"
            yk2 = yk + ",1"
            if pk2 not in known:
                # 验证Y侧标准
                seq, std = e("Y", yk2, 3)
                if std:
                    new_r2[pk2] = yk2
        known.update(new_r2)
        added_this_round += len(new_r2)

        # 步骤2: 尝试R3验证 - 遍历Y树中与已知PPS长度相近的limit
        # 收集候选PPS limit表达式（从PPS种子树中）
        pps_limits = set()
        y_limits = set()

        # 从种子出发收集
        def collect_pps_limits(expr, depth=0):
            if depth > 3: return
            seq, std = e("PPS", expr, expand_n)
            if not std: return
            fs = extract_fs(seq, expr, "PPS", expand_n)
            if fs:
                pps_limits.add(expr)
                for t in fs[:4]:
                    collect_pps_limits(t, depth + 1)

        for n in range(6):
            seed = ",".join(str(i) for i in range(n + 1))
            collect_pps_limits(seed)

        def collect_y_limits(expr, depth=0):
            if depth > 3: return
            seq, std = e("Y", expr, expand_n)
            if not std: return
            fs = extract_fs(seq, expr, "Y", expand_n)
            if fs:
                y_limits.add(expr)
                for t in fs[:4]:
                    collect_y_limits(t, depth + 1)

        collect_y_limits("1,2")
        collect_y_limits("1,3")

        # 对每个未对应的PPS极限，尝试匹配Y极限
        for pk in sorted(pps_limits, key=lambda x: len(x)):
            if pk in known:
                continue
            pps_fs_seq, _ = e("PPS", pk, expand_n)
            pps_fs = extract_fs(pps_fs_seq, pk, "PPS", n_check)
            if not pps_fs:
                continue

            # 尝试用已知对应转换pps_fs[1]
            y_f1 = pps_to_y(pps_fs[0], known)
            if y_f1 is None:
                continue  # f[1]还无法转换，跳过

            # 在Y树中找基本列第一项等于y_f1的极限
            for yk in y_limits:
                if yk in known.values():
                    continue
                y_fs_seq, _ = e("Y", yk, expand_n)
                y_fs = extract_fs(y_fs_seq, yk, "Y", n_check + 3)
                if not y_fs:
                    continue
                if y_fs[0] == y_f1:
                    # 候选！验证R3
                    if verify_r3(pk, yk, known, n_check):
                        known[pk] = yk
                        added_this_round += 1
                        print(f"  [R3] pps {pk:25s} = y {yk:25s}")
                        break

        if added_this_round == 0:
            break
        print(f"  --- 第{round_num}轮: +{added_this_round}对 ---")

    # 输出最终结果
    print(f"\n{'='*70}")
    print(f"  最终结果: {len(known)} 对对应")
    print(f"{'='*70}")
    print(f"{'PPS':<30s} {'Y':<30s} {'来源'}")
    print("-" * 70)

    # 确定来源
    sources = {"0": "R1"}
    for pk in known:
        if pk in sources:
            continue
        # 检查是否是R2: 去掉,0后是否在known中
        if pk.endswith(",0"):
            base = pk[:-2]
            if base in known:
                sources[pk] = "R2"
            else:
                sources[pk] = "R3"
        else:
            sources[pk] = "R3"

    for pk in known:
        print(f"pps {pk:<27s} y {known[pk]:<28s} {sources.get(pk, '?')}")


if __name__ == "__main__":
    main()
