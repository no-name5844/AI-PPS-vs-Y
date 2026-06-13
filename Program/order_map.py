#!/usr/bin/env python3
"""Comprehensive enumeration of PPS and Y standard expressions, then order-mapping."""

import subprocess, sys, os, json, time
from pathlib import Path

SEQT = r'G:\4\ord\study\AI && PPS vs BOCF\Program\seqtool.exe'
OUT = str(Path.home() / "WorkBuddy" / "2026-06-07-17-38-56" / "order_map.json")

_cache = {}
def expand(system, expr, n):
    k = f'{system}:{expr}:{n}'
    if k in _cache: return _cache[k]
    r = subprocess.run([SEQT, system, 'expand', '-s', expr, '-n', str(n)], 
                       capture_output=True, text=True, timeout=30)
    o = r.stdout.strip()
    std = 'IsStandard: Yes' in o
    seq = []
    if 'After expand' in o:
        after = o.split('After expand')[-1]
        if ':' in after:
            ac = after.split(':', 1)[1].strip()
            if ac.startswith('(') and ')' in ac:
                end = ac.index(')')
                seq = [int(x.strip()) for x in ac[1:end].split(',') if x.strip()]
    if not seq:
        for line in o.split('\n'):
            parts = line.strip().split()
            if parts and all(p.lstrip('-').isdigit() for p in parts):
                seq = [int(p) for p in parts]
                break
    _cache[k] = (seq, std)
    return seq, std

def fs_terms(seq, orig, system, n):
    if not seq: return []
    tail = seq[-min(5, len(seq)):]
    ts = set(tail)
    if len(ts) == 1:
        tv = tail[0]
        i = len(seq) - 1
        while i >= 0 and seq[i] == tv: i -= 1
        pre = seq[:i+1] if i >= 0 else []
        cur = list(pre) if pre else []
        terms = []
        for k in range(n):
            t = ','.join(str(x) for x in cur)
            if t and t != orig: terms.append(t)
            cur = cur + [tv]
        return terms
    terms = []
    for n2 in range(n):
        s2, _ = expand(system, orig, n2)
        if s2:
            t = ','.join(str(x) for x in s2)
            if t != orig: terms.append(t)
    return terms

def enum_system(system, seeds, max_depth=6, max_len=10):
    """DFS enumerate all standard expressions."""
    visited = set()
    results = []
    
    def dfs(expr, depth):
        if depth > max_depth: return
        if expr in visited: return
        visited.add(expr)
        
        seq, std = expand(system, expr, 10)
        if not std: return
        if len(expr.split(',')) > max_len: return
        
        results.append(expr)
        
        # Get fs terms and recurse
        terms = fs_terms(seq, expr, system, 5)
        for i, t in enumerate(terms):
            if i >= 3: break  # limit children to 3
            time.sleep(0.03)
            dfs(t, depth + 1)
    
    for seed in seeds:
        dfs(seed, 0)
    return results

print("Enumerating PPS...")
pps_exprs = enum_system('PPS', ['0', '0,1', '0,1,2', '0,1,2,3'], max_depth=6, max_len=9)
print(f"PPS: {len(pps_exprs)} standard expressions")

print("Enumerating Y...")
y_exprs = enum_system('Y', ['1', '1,2', '1,3'], max_depth=6, max_len=9)
print(f"Y: {len(y_exprs)} standard expressions")

# Sort PPS expressions
print("\nSorting PPS...")
pps_sorted = []
for e in pps_exprs:
    pps_sorted.append(e)
# Simple sort by dictionary order (the systems use internal dict order)
# We'll use the compare tool

# Build comparison matrix (pairwise)
# This is O(n^2) but for reasonable n it's ok

def sort_exprs(exprs, system):
    """Sort expressions by their internal ordering using compare tool."""
    n = len(exprs)
    if n <= 1: return list(exprs)
    
    # Use insertion sort with compare tool
    sorted_list = [exprs[0]]
    for i in range(1, min(n, 50)):  # limit to 50
        e = exprs[i]
        # Binary search insertion position
        lo, hi = 0, len(sorted_list)
        while lo < hi:
            mid = (lo + hi) // 2
            r = subprocess.run([SEQT, system, 'compare', '-s', e, '-s', sorted_list[mid]],
                              capture_output=True, text=True, timeout=10)
            if 'Seq1 < Seq2' in r.stdout:
                hi = mid
            else:
                lo = mid + 1
        sorted_list.insert(lo, e)
        if i % 10 == 0:
            print(f"  {system} sorted {i+1}/{min(n,50)}")
    return sorted_list

pps_limited = pps_exprs[:50] if len(pps_exprs) > 50 else pps_exprs
y_limited = y_exprs[:50] if len(y_exprs) > 50 else y_exprs

print(f"\nSorting {len(pps_limited)} PPS expressions...")
pps_sorted = sort_exprs(pps_limited, 'PPS')
print(f"Sorting {len(y_limited)} Y expressions...")
y_sorted = sort_exprs(y_limited, 'Y')

print(f"\n{'='*60}")
print(f"PPS ({len(pps_sorted)}): {pps_sorted[:10]}...")
print(f"Y   ({len(y_sorted)}): {y_sorted[:10]}...")
print(f"\nIndex mapping (first 15):")
for i in range(min(15, len(pps_sorted), len(y_sorted))):
    p = pps_sorted[i]
    y = y_sorted[i]
    print(f"  [{i:2d}] pps {p:25s} ↔ y {y:25s}")

# Save
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({
        'pps': pps_sorted,
        'y': y_sorted,
        'pps_count': len(pps_exprs),
        'y_count': len(y_exprs)
    }, f, ensure_ascii=False, indent=2)
print(f"\nSaved to {OUT}")
