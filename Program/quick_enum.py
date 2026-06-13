import subprocess
SEQT = r'G:\4\ord\study\AI && PPS vs BOCF\Program\seqtool.exe'

pps = set()
for s in ['0','0,1','0,1,2','0,1,2,3','0,1,2,3,4',
          '0,1,0,0,3','0,1,0,0,3,3','0,1,0,0,3,3,3','0,1,0,0,3,3,3,3',
          '0,1,0,0,3,3,3,3,3','0,1,0,0,3,3,3,3,3,3',
          '0,1,0,0,4','0,1,0,1','0,1,0,2','0,1,0,2,2','0,1,0,3','0,1,1',
          '0,1,2,0,0,4','0,1,2,0,1','0,1,2,0,2','0,1,2,0,3','0,1,2,2',
          '0,1,2,3,0,0,5','0,1,2,3,0,1','0,1,2,3,0,2','0,1,2,3,0,3','0,1,2,3,0,4','0,1,2,3,2','0,1,2,3,3']:
    r = subprocess.run([SEQT, 'PPS', 'expand', '-s', s, '-n', '0'], capture_output=True, text=True, timeout=5)
    if 'IsStandard: Yes' in r.stdout: pps.add(s)

print(f'PPS: {len(pps)} standard limits')
for l in sorted(pps, key=lambda x: (len(x.split(',')), x)): print(f'  {l}')
