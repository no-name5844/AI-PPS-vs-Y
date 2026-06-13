#!/usr/bin/env python3
"""Deep search: enumerate Y tree from y1,3 and find PPS counterparts by R3 clamp."""

import subprocess, sys, os, json, time
from pathlib import Path

SEQT = r'G:\4\ord\study\AI && PPS vs BOCF\Program\seqtool.exe'
OUT = str(Path.home() / "WorkBuddy" / "2026-06-07-17-38-56" / "deep_search.json")

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
    """Extract first n fundamental sequence terms."""
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

def get_y_fs(y_expr, n_terms=5):
    """Get Y fundamental sequence terms."""
    seq, std = expand('Y', y_expr, 10)
    return fs_terms(seq, y_expr, 'Y', n_terms)

def get_pps_fs(pps_expr, n_terms=5):
    """Get PPS fundamental sequence terms."""
    seq, std = expand('PPS', pps_expr, 10)
    return fs_terms(seq, pps_expr, 'PPS', n_terms)

def y_to_pps(y_expr):
    """Convert Y expression to PPS using known correspondences (R2 chain)."""
    known = {
        '1': '0',
        '1,1': '0,0',
        '1,2': '0,1',
        '1,2,1': '0,1,0',
        '1,2,1,1': '0,1,0,0',
        '1,2,1,2': '0,1,0,0,3',
        '1,2,1,2,1': '0,1,0,0,3,0',
        '1,2,1,2,1,1': '0,1,0,0,3,0,0',
        '1,2,2': '0,1,0,0,3,3',
        '1,2,2,1': '0,1,0,0,3,3,0',
        '1,2,2,1,1': '0,1,0,0,3,3,0,0',
    }
    if y_expr in known:
        return known[y_expr]
    
    # Try R2 reverse: if Y ends with 1 and removing it matches known
    parts = y_expr.split(',')
    if parts[-1] == '1':
        base = ','.join(parts[:-1])
        pps_base = y_to_pps(base)
        if pps_base:
            # Wait, R2 is A,0 → B,1. So Y 1 at end means PPS base ended with 0
            return pps_base + ',0'
    
    return None

def pps_compare(a, b):
    """Compare two PPS expressions."""
    r = subprocess.run([SEQT, 'PPS', 'compare', '-s', a, '-s', b],
                       capture_output=True, text=True, timeout=10)
    if 'Seq1 < Seq2' in r.stdout: return -1
    if 'Seq1 > Seq2' in r.stdout: return 1
    if 'Seq1 == Seq2' in r.stdout: return 0
    return None

# Known PPS expressions to find Y counterparts for
pps_targets = [
    '0,1,0,0,4',
    '0,1,0,1',
    '0,1,0,2',
    '0,1,0,2,2',
    '0,1,0,3',
    '0,1,1',
]

# Enumerate Y tree nodes up to depth D from seeds
def enumerate_y_tree(seeds, max_depth=5, max_len=8):
    """DFS enumerate Y standard expressions."""
    visited = set()
    results = []
    
    def dfs(expr, depth):
        if depth > max_depth: return
        key = expr
        if key in visited: return
        visited.add(key)
        
        seq, std = expand('Y', expr, 10)
        if not std: return
        
        results.append((expr, seq))
        if len(expr.split(',')) > max_len: return
        
        # Extract fs terms and recurse
        terms = fs_terms(seq, expr, 'Y', 5)
        for t in terms[:4]:
            time.sleep(0.05)  # small delay
            dfs(t, depth + 1)
    
    for seed in seeds:
        dfs(seed, 0)
    
    return results

print("Enumerating Y tree...")
y_nodes = enumerate_y_tree(['1,2', '1,3'], max_depth=5, max_len=10)
print(f"Found {len(y_nodes)} Y standard expressions")

# For each PPS target, try R3 clamp with Y candidates
print("\nR3 clamp search:")
for pps_t in pps_targets:
    pps_fs = get_pps_fs(pps_t, 5)
    pps_fs_y = [y_to_pps(t) for t in pps_fs] if pps_t in {} else None
    
    # Get actual PPS f terms
    pps_seq, _ = expand('PPS', pps_t, 10)
    pps_real_fs = []
    for n in range(5):
        s, _ = expand('PPS', pps_t, n)
        if s:
            pps_real_fs.append(','.join(str(x) for x in s))
    
    print(f"\npps {pps_t}: fs = {pps_real_fs}")
    
    candidates = []
    for y_expr, y_seq in y_nodes:
        y_terms = fs_terms(y_seq, y_expr, 'Y', 5)
        if len(y_terms) < 3: continue
        
        # Try R3 clamp in PPS space (convert Y terms to PPS)
        clamp_ok = True
        for n in range(min(3, len(pps_real_fs))):
            pps_fn = pps_real_fs[n]
            found_lower = False
            found_upper = False
            for m in range(len(y_terms)):
                y_pps = y_to_pps(y_terms[m])
                if not y_pps: continue
                cmp = pps_compare(y_pps, pps_fn)
                if cmp is not None and cmp <= 0:
                    found_lower = True
                if cmp is not None and cmp >= 0:
                    found_upper = True
            if not found_lower or not found_upper:
                clamp_ok = False
                break
        
        if clamp_ok:
            candidates.append(y_expr)
    
    if candidates:
        print(f"  Matches: {candidates[:3]}")
    else:
        print(f"  No matches in Y tree (depth 5)")

# Save results
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({'y_count': len(y_nodes), 'results': {}}, f, ensure_ascii=False)
print(f"\nSaved to {OUT}")
