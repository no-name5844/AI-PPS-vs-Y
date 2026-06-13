#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TraceMark 树状递归展开程序 v3
- 从种子极限表达式出发，递归展开构建标准表达式树
- PPS vs Y 跨系统逐层对比
"""

import subprocess
import sys
import io
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SEQT = str(Path(__file__).parent / "seqtool.exe")


def run_expand(system, expr, n):
    """运行 seqtool expand，返回 (展开序列, is_standard)"""
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


def is_successor(seq):
    """判断表达式是否为后继（末尾为0的序列，或简单情况）"""
    if not seq:
        return False
    return seq[-1] == 0


def strip_trailing_repeat(seq):
    """去除尾缀重复元素"""
    if len(seq) <= 1:
        return tuple(seq)
    result = list(seq)
    while len(result) > 1 and result[-1] == result[-2]:
        result.pop()
    return tuple(result)


def tree_expand(system, expr_str, depth, max_depth, max_expand_n, visited):
    """
    递归展开表达式树。
    返回: {
        'expr': expr_str,
        'system': system,
        'depth': depth,
        'is_limit': bool,
        'fs_terms': [(term_str, ...)],  # 基本列项
        'children': [...]  # 递归子树
    }
    """
    expr_key = f"{system}:{expr_str}"
    if expr_key in visited or depth > max_depth:
        return None
    visited.add(expr_key)

    # 展开到足够深度以获取基本列项
    seq, std = run_expand(system, expr_str, max_expand_n)
    if not std or not seq:
        return {
            'expr': expr_str,
            'system': system,
            'depth': depth,
            'is_limit': False,
            'fs_terms': [],
            'children': [],
            'expand_seq': seq
        }

    # 检测是否为极限（展开序列长度 > 原表达式长度）
    orig = [int(x) for x in expr_str.split(",")]
    is_limit_expr = len(seq) > 0  # 能展开出东西的都是极限或后继

    # 提取基本列各项（展开序列中每一项是一个展开步骤的结果）
    # 对简单模式: 展开每步增加1个到若干个相同元素
    # 如: 0,1 → 0 → 0,0 → 0,0,0 → ... (基本列项: 0, 0,0, 0,0,0, ...)
    
    # 检测展开模式
    fs_terms = []
    tail = seq[-(min(5, len(seq))):]
    tail_set = set(tail)
    
    if len(tail_set) == 1 and len(seq) > 5:
        # 单一尾缀模式：基本列每项递增尾缀元素
        tail_val = tail[0]
        i = len(seq) - 1
        while i >= 0 and seq[i] == tail_val:
            i -= 1
        prefix = seq[:i+1] if i >= 0 else []
        
        # 从展开序列反推基本列各项
        # 模式: f[1] = prefix (或更短), f[k] = prefix + k个tail_val
        # 直接构造
        current = list(prefix) if prefix else []
        for k in range(max_expand_n):
            term_str = ",".join(str(x) for x in current)
            if term_str and term_str != expr_str:  # 避免循环
                fs_terms.append(term_str)
            current = current + [tail_val]
    else:
        # 非单一尾缀: 逐个展开来获取
        for n in range(1, max_expand_n + 1):
            s, _ = run_expand(system, expr_str, n)
            if s:
                term_str = ",".join(str(x) for x in s)
                if term_str != expr_str:
                    fs_terms.append(term_str)

    # 递归处理每个基本列项
    children = []
    if is_limit_expr and depth < max_depth:
        for term in fs_terms[:max_expand_n]:  # 限制深度
            child = tree_expand(system, term, depth + 1, max_depth, max_expand_n, visited)
            if child:
                children.append(child)

    return {
        'expr': expr_str,
        'system': system,
        'depth': depth,
        'is_limit': is_limit_expr and len(fs_terms) > 0,
        'fs_terms': fs_terms[:max_expand_n],
        'children': children,
        'expand_seq': seq
    }


def print_tree(node, indent=0, show_depth=1):
    """打印表达式树"""
    if node is None or node['depth'] > show_depth:
        return
    prefix = "  " * indent
    expr = node['expr']
    fs = node.get('fs_terms', [])
    limit_tag = "[L]" if node['is_limit'] else "[S]"
    seq_preview = ",".join(str(x) for x in node.get('expand_seq', [])[:8])
    print(f"{prefix}{limit_tag} {node['system']}:{expr:20s} → ({seq_preview}...)  [{len(fs)} children]")
    for child in node.get('children', []):
        print_tree(child, indent + 1, show_depth)


def main():
    pps_max_seed = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    y_max_seed   = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    max_depth    = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    expand_n     = int(sys.argv[4]) if len(sys.argv) > 4 else 6

    print("=" * 74)
    print("  TraceMark 树状展开 v3")
    print(f"  PPS种子: 0..{pps_max_seed}  Y种子: 1,2..1,{y_max_seed}")
    print(f"  最大深度: {max_depth}  展开数: {expand_n}")
    print("=" * 74)

    # ── PPS 种子: 0, 0,1, 0,1,2, ... ──
    pps_seeds = [",".join(str(i) for i in range(k + 1)) for k in range(pps_max_seed + 1)]
    # ── Y 种子: 1,2, 1,3, ... ──
    y_seeds = [f"1,{k}" for k in range(2, y_max_seed + 1)]

    print("\n## PPS 表达式树\n")
    pps_visited = set()
    pps_trees = {}
    for seed in pps_seeds:
        print(f"\n--- 种子: pps {seed} ---")
        tree = tree_expand("PPS", seed, 0, max_depth, expand_n, pps_visited)
        if tree:
            pps_trees[seed] = tree
            print_tree(tree, show_depth=2)

    print("\n\n## Y 表达式树\n")
    y_visited = set()
    y_trees = {}
    for seed in y_seeds:
        print(f"\n--- 种子: y {seed} ---")
        tree = tree_expand("Y", seed, 0, max_depth, expand_n, y_visited)
        if tree:
            y_trees[seed] = tree
            print_tree(tree, show_depth=2)

    # ── 跨系统对比 ──
    print("\n\n## 跨系统结构对比\n")
    print(f"{'PPS表达式':<24s} {'展开模式':<35s} || {'Y表达式':<24s} {'展开模式':<35s}")
    print("-" * 120)

    # 对齐：PPS level N 的种子展开 vs Y level N+1 的种子展开
    max_n = max(pps_max_seed, y_max_seed - 1)
    for n in range(max_n + 1):
        pps_key = ",".join(str(i) for i in range(n + 1))
        y_key = f"1,{n+1}" if n >= 1 else None

        pps_seq = pps_trees.get(pps_key, {}).get('expand_seq', [])
        y_seq = y_trees.get(y_key, {}).get('expand_seq', []) if y_key else []

        pps_mode = _describe_mode(pps_seq)
        y_mode = _describe_mode(y_seq)

        print(f"pps {pps_key:<20s} {pps_mode:<35s} || y {y_key if y_key else '':<22s} {y_mode:<35s}")


def _describe_mode(seq):
    """描述展开模式"""
    if not seq:
        return "空"
    tail = seq[-min(5, len(seq)):]
    tail_set = set(tail)
    if len(tail_set) == 1:
        return f"前缀+无限{tail[0]}(共{len(seq)}项)"
    elif len(tail_set) == 2 and len(tail) >= 4:
        return f"交替模式(共{len(seq)}项)"
    else:
        # 检测指数模式
        if len(seq) >= 4:
            ratios = []
            for i in range(2, min(6, len(seq))):
                if seq[i-1] > 0:
                    ratios.append(seq[i] / seq[i-1])
            if ratios and all(abs(r - ratios[0]) < 0.01 for r in ratios):
                return f"指数x{ratios[0]:.0f}(共{len(seq)}项)"
        return f"复杂模式(共{len(seq)}项)"


if __name__ == "__main__":
    main()
