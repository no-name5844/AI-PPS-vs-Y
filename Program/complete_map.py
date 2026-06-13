#!/usr/bin/env python3
"""Complete order-isomorphism mapping by enumerating and sorting all standard expressions."""

import subprocess, sys, os, json, time, itertools
from pathlib import Path

SEQT = r'G:\4\ord\study\AI && PPS vs BOCF\Program\seqtool.exe'
OUT = str(Path.home() / "WorkBuddy" / "2026-06-07-17-38-56" / "complete_map.json")

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

def enum_system(system, seeds, max_depth=4, max_len=8, max_nodes=200):
    visited = set()
    results = []
    
    def dfs(expr, depth):
        if depth > max_depth: return
        if expr in visited: return
        if len(results) >= max_nodes: return
        visited.add(expr)
        
        seq, std = expand(system, expr, 10)
        if not std: return
        if len(expr.split(',')) > max_len: return
        
        results.append(expr)
        
        terms = fs_terms(seq, expr, system, 4)
        for i, t in enumerate(terms):
            if i >= 2: break
            time.sleep(0.02)
            dfs(t, depth + 1)
    
    for seed in seeds:
        if len(results) >= max_nodes: break
        dfs(seed, 0)
    return results

def sort_by_compare(exprs, system):
    """Sort using compare tool (insertion, limited)."""
    n = len(exprs)
    if n <= 1: return list(exprs)
    
    # Use Python sort with comparison function
    def cmp(a, b):
        r = subprocess.run([SEQT, system, 'compare', '-s', a, '-s', b],
                          capture_output=True, text=True, timeout=10)
        if 'Seq1 < Seq2' in r.stdout: return -1
        if 'Seq1 > Seq2' in r.stdout: return 1
        return 0
    
    import functools
    return sorted(exprs, key=functools.cmp_to_key(cmp))

print("Enumerating PPS...")
pps = enum_system('PPS', ['0', '0,1', '0,1,2', '0,1,2,3'], max_depth=4, max_len=8, max_nodes=100)
print(f"  PPS: {len(pps)} expressions")

print("Enumerating Y...")
y_exprs = enum_system('Y', ['1', '1,2', '1,3'], max_depth=4, max_len=8, max_nodes=100)
print(f"  Y: {len(y_exprs)} expressions")

print("Sorting PPS...")
pps_sorted = sort_by_compare(pps, 'PPS')
print("Sorting Y...")
y_sorted = sort_by_compare(y_exprs, 'Y')

print(f"\n=== MATCHING (first {min(len(pps_sorted), len(y_sorted))} entries) ===")
m = min(len(pps_sorted), len(y_sorted))
matches = []
for i in range(m):
    p = pps_sorted[i]
    y = y_sorted[i]
    matches.append({'idx': i, 'pps': p, 'y': y})
    if i < 30:
        print(f"  [{i:3d}] pps {p:30s} ↔ y {y:30s}")

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({'pps_count': len(pps), 'y_count': len(y_exprs), 'matches': matches}, f, ensure_ascii=False, indent=2)
print(f"\nSaved {len(matches)} matches to {OUT}")
