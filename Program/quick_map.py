import subprocess, json, sys
from pathlib import Path

SEQT = r'G:\4\ord\study\AI && PPS vs BOCF\Program\seqtool.exe'
OUT = str(Path.home() / "WorkBuddy" / "2026-06-07-17-38-56" / "quick_map.json")

def is_std(system, s):
    r = subprocess.run([SEQT, system, 'expand', '-s', s, '-n', '0'], capture_output=True, text=True, timeout=5)
    return 'IsStandard: Yes' in r.stdout

def compare(system, a, b):
    r = subprocess.run([SEQT, system, 'compare', '-s', a, '-s', b], capture_output=True, text=True, timeout=10)
    if 'Seq1 < Seq2' in r.stdout: return -1
    if 'Seq1 > Seq2' in r.stdout: return 1
    return 0

# PPS list (all known)
pps_raw = ['0','0,0','0,1','0,1,0','0,1,0,0',
    '0,1,0,0,3','0,1,0,0,3,0','0,1,0,0,3,0,0',
    '0,1,0,0,3,0,0,6','0,1,0,0,3,0,0,6,0,0,9',
    '0,1,0,0,3,3','0,1,0,0,3,3,0','0,1,0,0,3,3,0,0',
    '0,1,0,0,3,3,3','0,1,0,0,3,3,3,3',
    '0,1,0,0,3,3,3,3,3','0,1,0,0,3,3,3,3,3,3',
    '0,1,0,0,4','0,1,0,1','0,1,0,2','0,1,0,2,2','0,1,0,3',
    '0,1,1','0,1,2',
    '0,1,2,0','0,1,2,0,0','0,1,2,0,0,4',
    '0,1,2,0,1','0,1,2,0,2','0,1,2,0,3',
    '0,1,2,2','0,1,2,3',
    '0,1,2,3,0','0,1,2,3,0,0','0,1,2,3,0,0,5',
    '0,1,2,3,0,1','0,1,2,3,0,2','0,1,2,3,0,3','0,1,2,3,0,4',
    '0,1,2,3,2','0,1,2,3,3','0,1,2,3,4']

pps = [s for s in pps_raw if is_std('PPS', s)]

# Y list - comprehensive
y_raw = ['1','1,1','1,1,1','1,1,1,1',
    '1,2','1,2,1','1,2,1,1','1,2,1,1,1',
    '1,2,1,2','1,2,1,2,1','1,2,1,2,1,1','1,2,1,2,1,1,1',
    '1,2,1,2,1,2','1,2,1,2,1,2,1,2',
    '1,2,2','1,2,2,1','1,2,2,1,1',
    '1,2,2,1,2','1,2,2,2',
    '1,2,3','1,2,3,1','1,2,3,1,1',
    '1,2,3,1,2','1,2,3,2',
    '1,2,4','1,2,4,1','1,2,4,1,1',
    '1,2,4,1,2','1,2,4,2','1,2,4,3','1,2,4,4','1,2,4,5','1,2,4,6','1,2,4,7','1,2,4,8',
    '1,2,4,8','1,2,4,8,1','1,2,4,8,1,1',
    '1,2,4,8,1,2','1,2,4,8,2',
    '1,2,4,8,16','1,2,4,8,16,32',
    '1,3','1,3,1','1,3,1,1','1,3,2','1,3,3','1,3,4','1,3,5','1,3,6','1,3,7','1,3,8',
    '1,3,9','1,3,9,1,2',
    '1,4','1,5']

y_exprs = [s for s in y_raw if is_std('Y', s)]

print(f"PPS: {len(pps)} standard, Y: {len(y_exprs)} standard")

# Sort PPS
import functools
pps_sorted = sorted(pps, key=functools.cmp_to_key(lambda a,b: compare('PPS', a, b)))
y_sorted = sorted(y_exprs, key=functools.cmp_to_key(lambda a,b: compare('Y', a, b)))

print("\n=== PPS ORDER (first 20) ===")
for i, e in enumerate(pps_sorted[:20]): print(f"  [{i:2d}] {e}")

print("\n=== Y ORDER (first 20) ===")  
for i, e in enumerate(y_sorted[:20]): print(f"  [{i:2d}] {e}")

print(f"\n=== POSITION MAP (first {min(len(pps_sorted), len(y_sorted))}) ===")
m = min(len(pps_sorted), len(y_sorted))
matches = []
for i in range(m):
    matches.append({'idx': i, 'pps': pps_sorted[i], 'y': y_sorted[i]})
    if pps_sorted[i] != y_sorted[i]:  # don't print trivial matches
        print(f"  [{i:2d}] pps {pps_sorted[i]:25s} = y {y_sorted[i]:25s}")

with open(OUT, 'w') as f:
    json.dump({'pps': pps_sorted, 'y': y_sorted, 'matches': matches}, f, indent=2)
print(f"\nSaved {len(matches)} matches")
