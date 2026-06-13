#!/usr/bin/env python3
"""Enumerate ALL standard limits by checking last-value patterns for each f[0]."""

import subprocess, json, time, sys
from pathlib import Path

SEQT = r'G:\4\ord\study\AI && PPS vs BOCF\Program\seqtool.exe'
OUT = str(Path.home() / "WorkBuddy" / "2026-06-07-17-38-56" / "enum2.json")

def is_std(system, expr):
    r = subprocess.run([SEQT, system, 'expand', '-s', expr, '-n', '0'],
                      capture_output=True, text=True, timeout=10)
    return 'IsStandard: Yes' in r.stdout

def get_f0(system, expr):
    r = subprocess.run([SEQT, system, 'expand', '-s', expr, '-n', '0'],
                      capture_output=True, text=True, timeout=10)
    o = r.stdout
    seq = []
    if 'After expand' in o:
        after = o.split('After expand')[-1]
        if ':' in after:
            ac = after.split(':', 1)[1].strip()
            if ac.startswith('(') and ')' in ac:
                end = ac.index(')')
                seq = [int(x.strip()) for x in ac[1:end].split(',') if x.strip()]
    return ','.join(str(x) for x in seq) if seq else None

def enum_from_f0(system, f0_expr, max_val=50):
    """Find all standard limits with given f[0]."""
    results = []
    parts = f0_expr.split(',') if f0_expr != '0' else ['0']
    base_len = len(parts) + 1  # length of expression = f0 length + 1
    
    for last_val in range(1, max_val + 1):
        expr = f0_expr + ',' + str(last_val)
        if is_std(system, expr):
            results.append(expr)
            if len(results) >= 10:  # limit per f0
                break
    return results

def explore(system, seeds, max_depth=5, max_len=12):
    """BFS explore standard limits."""
    all_limits = set()
    f0_queue = []
    
    # Start with seeds
    for seed in seeds:
        if is_std(system, seed):
            all_limits.add(seed)
            f0_val = get_f0(system, seed)
            if f0_val:
                f0_queue.append(f0_val)
    
    # For each f[0] value found, enumerate limits
    processed_f0 = set()
    depth = 0
    
    while f0_queue and depth < max_depth:
        next_queue = []
        for f0 in f0_queue:
            if f0 in processed_f0: continue
            if len(f0.split(',')) > max_len: continue
            processed_f0.add(f0)
            
            new_limits = enum_from_f0(system, f0, max_val=30)
            for lim in new_limits:
                if lim not in all_limits:
                    all_limits.add(lim)
                    new_f0 = get_f0(system, lim)
                    if new_f0 and new_f0 not in processed_f0:
                        next_queue.append(new_f0)
                time.sleep(0.02)
        
        f0_queue = next_queue
        depth += 1
        print(f"  {system} depth {depth}: {len(all_limits)} limits, queue={len(f0_queue)}")
    
    return sorted(all_limits, key=lambda x: (len(x.split(',')), x))

print("=== PPS Enumeration ===")
pps_limits = explore('PPS', ['0', '0,1', '0,1,2', '0,1,2,3'], max_depth=6, max_len=10)
print(f"PPS: {len(pps_limits)} limits")
for l in pps_limits[:30]:
    print(f"  pps {l}")

print("\n=== Y Enumeration ===")
y_limits = explore('Y', ['1', '1,2', '1,3'], max_depth=6, max_len=10)
print(f"Y: {len(y_limits)} limits")
for l in y_limits[:30]:
    print(f"  y {l}")

with open(OUT, 'w') as f:
    json.dump({'pps': pps_limits, 'y': y_limits}, f)
print(f"\nSaved to {OUT}")
