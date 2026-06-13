"""Brute force: enumerate ALL standard PPS/Y expressions by length."""
import subprocess, json, functools, itertools, sys, time
from pathlib import Path

SEQT = r'G:\4\ord\study\AI && PPS vs BOCF\Program\seqtool.exe'
OUT = str(Path.home() / "WorkBuddy" / "2026-06-07-17-38-56" / "brute_map.json")

_cache = {}
def is_std(system, expr):
    if expr in _cache: return _cache[expr]
    r = subprocess.run([SEQT, system, 'expand', '-s', expr, '-n', '0'],
                      capture_output=True, text=True, timeout=5)
    result = 'IsStandard: Yes' in r.stdout
    _cache[expr] = result
    return result

def compare(system, a, b):
    r = subprocess.run([SEQT, system, 'compare', '-s', a, '-s', b],
                      capture_output=True, text=True, timeout=10)
    if 'Seq1 < Seq2' in r.stdout: return -1
    if 'Seq1 > Seq2' in r.stdout: return 1
    return 0

def enum_pps(max_len=7, max_val=15):
    """Enumerate PPS standard expressions starting with 0."""
    results = set()
    # Always include 0
    if is_std('PPS', '0'): results.add('0')
    
    for L in range(2, max_len + 1):
        # First element must be 0 for L>1
        prefixes = [['0']]
        for pos in range(1, L-1):
            new_prefixes = []
            for p in prefixes:
                for v in range(max_val + 1):
                    new_prefixes.append(p + [v])
            prefixes = new_prefixes
            if len(prefixes) > 10000:  # limit explosion
                prefixes = prefixes[:10000]
        
        for p in prefixes[:5000]:  # limit per length
            for last in range(max_val + 1):
                expr = ','.join(str(x) for x in (p + [last]))
                if is_std('PPS', expr):
                    results.add(expr)
        
        print(f"  PPS len={L}: {len(results)} total standard")
        if len(results) >= 60: break
    
    return list(results)

def enum_y(max_len=7, max_val=20):
    """Enumerate Y standard expressions starting with 1."""
    results = set()
    if is_std('Y', '1'): results.add('1')
    
    for L in range(2, max_len + 1):
        prefixes = [['1']]
        for pos in range(1, L-1):
            new_prefixes = []
            for p in prefixes:
                for v in range(1, max_val + 1):
                    new_prefixes.append(p + [v])
            prefixes = new_prefixes
            if len(prefixes) > 10000:
                prefixes = prefixes[:10000]
        
        for p in prefixes[:5000]:
            for last in range(1, max_val + 1):
                expr = ','.join(str(x) for x in (p + [last]))
                if is_std('Y', expr):
                    results.add(expr)
        
        print(f"  Y len={L}: {len(results)} total standard")
        if len(results) >= 60: break
    
    return list(results)

print("=== PPS Brute Force ===")
pps = enum_pps(max_len=6, max_val=10)
print(f"PPS: {len(pps)} standard")

print("\n=== Y Brute Force ===")
y_exprs = enum_y(max_len=5, max_val=10)
print(f"Y: {len(y_exprs)} standard")

print("\n=== Sorting ===")
pps_sorted = sorted(pps, key=functools.cmp_to_key(lambda a,b: compare('PPS', a, b)))
y_sorted = sorted(y_exprs, key=functools.cmp_to_key(lambda a,b: compare('Y', a, b)))

print(f"\n=== LIMIT-ONLY MAP ===")
pps_limits = [e for e in pps_sorted if not e.endswith(',0') and e != '0']
y_limits = [e for e in y_sorted if not e.endswith(',1') and e != '1']
print(f"PPS limits: {len(pps_limits)}, Y limits: {len(y_limits)}")

m = min(len(pps_limits), len(y_limits))
for i in range(m):
    print(f"  [{i:2d}] pps {pps_limits[i]:25s} = y {y_limits[i]:25s}")

with open(OUT, 'w') as f:
    json.dump({'pps_limits': pps_limits, 'y_limits': y_limits}, f, indent=2)
print(f"\nSaved")
