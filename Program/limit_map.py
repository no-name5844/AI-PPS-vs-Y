import subprocess, json, functools
from pathlib import Path

SEQT = r'G:\4\ord\study\AI && PPS vs BOCF\Program\seqtool.exe'
OUT = str(Path.home() / "WorkBuddy" / "2026-06-07-17-38-56" / "limit_map.json")

def is_std(system, s):
    r = subprocess.run([SEQT, system, 'expand', '-s', s, '-n', '0'], capture_output=True, text=True, timeout=5)
    return 'IsStandard: Yes' in r.stdout

def compare(system, a, b):
    r = subprocess.run([SEQT, system, 'compare', '-s', a, '-s', b], capture_output=True, text=True, timeout=10)
    if 'Seq1 < Seq2' in r.stdout: return -1
    if 'Seq1 > Seq2' in r.stdout: return 1
    return 0

# PPS limits only (end in >0)
pps_raw = ['0','0,1',
    '0,1,1','0,1,2',
    '0,1,0,1','0,1,0,2','0,1,0,3',
    '0,1,0,0,3','0,1,0,0,3,0,0,6','0,1,0,0,3,0,0,6,0,0,9',
    '0,1,0,0,3,3','0,1,0,0,3,3,3','0,1,0,0,3,3,3,3',
    '0,1,0,0,3,3,3,3,3','0,1,0,0,3,3,3,3,3,3',
    '0,1,0,0,4','0,1,0,2','0,1,0,2,2',
    '0,1,2','0,1,2,2','0,1,2,3',
    '0,1,2,0,1','0,1,2,0,2','0,1,2,0,3','0,1,2,0,0,4',
    '0,1,2,3','0,1,2,3,2','0,1,2,3,3','0,1,2,3,4',
    '0,1,2,3,0,1','0,1,2,3,0,2','0,1,2,3,0,3','0,1,2,3,0,4','0,1,2,3,0,0,5']

pps = [s for s in pps_raw if is_std('PPS', s)]

# Y limits only (end in >1)
y_raw = ['1','1,2',
    '1,2,1,2','1,2,1,2,1,2','1,2,1,2,1,2,1,2',
    '1,2,2','1,2,2,1,2','1,2,2,2',
    '1,2,3','1,2,3,1,2','1,2,3,2',
    '1,2,4','1,2,4,1,2','1,2,4,2','1,2,4,3','1,2,4,4','1,2,4,5','1,2,4,6','1,2,4,7','1,2,4,8',
    '1,2,4,8','1,2,4,8,1,2','1,2,4,8,2',
    '1,2,4,8,16','1,2,4,8,16,32',
    '1,3','1,3,2','1,3,3','1,3,4','1,3,5','1,3,6','1,3,7','1,3,8',
    '1,3,9','1,3,9,1,2',
    '1,4','1,5']

y_exprs = [s for s in y_raw if is_std('Y', s)]

print(f"PPS limits: {len(pps)}, Y limits: {len(y_exprs)}")

pps_sorted = sorted(pps, key=functools.cmp_to_key(lambda a,b: compare('PPS', a, b)))
y_sorted = sorted(y_exprs, key=functools.cmp_to_key(lambda a,b: compare('Y', a, b)))

print(f"\n=== LIMIT-ONLY POSITION MAP ===")
m = min(len(pps_sorted), len(y_sorted))
for i in range(m):
    print(f"  [{i:2d}] pps {pps_sorted[i]:30s} = y {y_sorted[i]:30s}")

with open(OUT, 'w') as f:
    json.dump({'pps_limits': pps_sorted, 'y_limits': y_sorted}, f, indent=2)
print(f"\nSaved")
