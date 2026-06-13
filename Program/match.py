#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TraceMark 逐层匹配 v2
- 以已知对应(pps 0=y 1, pps 0,1=y 1,2, pps 0,1,0,0,3=y 1,2,1,2)为锚点
- R2链自动推导后继
- 对极限表达式：比较基本列第一项的对应，递归验证
"""

import subprocess, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
SEQT = str(Path(__file__).parent / "seqtool.exe")

_cache = {}
def expand(s, e, n):
    k=f"{s}:{e}:{n}"
    if k in _cache: return _cache[k]
    r=subprocess.run([SEQT,s,"expand","-s",e,"-n",str(n)],capture_output=True,text=True,timeout=30)
    o=r.stdout.strip(); std="IsStandard: Yes" in o
    seq=[]
    if "After expand" in o:
        a=o.split("After expand")[-1]
        if ":" in a:
            ac=a.split(":",1)[1].strip()
            if ac.startswith("(") and ")" in ac:
                end=ac.index(")"); seq=[int(x.strip()) for x in ac[1:end].split(",") if x.strip()]
    if not seq:
        for l in o.split("\n"):
            p=l.strip().split()
            if p and all(x.lstrip('-').isdigit() for x in p): seq=[int(x) for x in p]; break
    _cache[k]=(seq,std); return seq,std


def fs_terms(seq, orig, s, n):
    """从展开序列反推基本列各项"""
    if not seq: return []
    tail=seq[-min(5,len(seq)):]; ts=set(tail)
    if len(ts)==1:
        tv=tail[0]; i=len(seq)-1
        while i>=0 and seq[i]==tv: i-=1
        pre=seq[:i+1] if i>=0 else []
        cur=list(pre) if pre else []; terms=[]
        for k in range(n):
            t=",".join(str(x) for x in cur)
            if t and t!=orig: terms.append(t)
            cur=cur+[tv]
        return terms
    terms=[]
    for n2 in range(1,n+1):
        s2,_=expand(s,orig,n2)
        if s2:
            t=",".join(str(x) for x in s2)
            if t!=orig: terms.append(t)
    return terms


def build_y_tree():
    """从y 1,2和y 1,3构建完整Y表达式森林,返回{expr: (seq, std, fs_terms, parent)}"""
    db={}; visited=set(); expand_n=6; depth_max=5
    def walk(e,d,parent):
        k=f"Y:{e}"
        if k in visited or d>depth_max or len(db)>2000: return
        visited.add(k)
        seq,std=expand("Y",e,expand_n)
        if not std: return
        fs=fs_terms(seq,e,"Y",expand_n)
        db[e]=(seq,std,fs,parent)
        for t in fs[:expand_n]:
            walk(t,d+1,e)
    walk("1,2",0,None)
    walk("1,3",0,None)
    return db


def main():
    print("构建Y森林(从1,2+1,3)...")
    y_db = build_y_tree()
    print(f"Y: {len(y_db)} 表达式")

    # 已知对应表
    known = {
        "0": "1",           # R1
        "0,1": "1,2",       # axiom
        "0,1,0,0,3": "1,2,1,2",  # example
    }

    # R2后继链
    def r2_match(pps_expr):
        """如果 pps_expr 以 ,0 结尾，且去掉 ,0 后有已知对应"""
        if pps_expr.endswith(",0"):
            base = pps_expr[:-2]  # 去掉 ,0
            if base in known:
                return known[base] + ",1"
        return None

    def r2_reverse(y_expr):
        """如果 y_expr 以 ,1 结尾"""
        if y_expr.endswith(",1"):
            base = y_expr[:-2]
            for pk, yk in known.items():
                if yk == base:
                    return pk + ",0"
        return None

    # 扩展已知表 (R2链)
    changed = True
    while changed:
        changed = False
        new_known = dict(known)
        for pk, yk in known.items():
            # PPS后继
            pk2 = pk + ",0"
            yk2 = yk + ",1"
            if pk2 not in new_known:
                # 验证: Y侧必须标准
                seq, std = expand("Y", yk2, 3)
                if std:
                    new_known[pk2] = yk2
                    changed = True
        known = new_known

    print(f"\n已知对应(含R2链): {len(known)} 对")

    # 尝试匹配未对应的PPS表达式
    # 方法: 对于limit表达式, 检查其f[1]是否有已知Y对应
    y_db_exprs = set(y_db.keys())
    new_matches = {}

    # 收集需要匹配的PPS表达式
    pps_to_match = set()
    # 从种子出发
    for n in range(7):
        seed = ",".join(str(i) for i in range(n+1))
        seq, std = expand("PPS", seed, 5)
        if not std: continue
        fs = fs_terms(seq, seed, "PPS", 5)  # 只枚举基本列前几项
        # 不要递归收集——太多了。只收集作为基本列项出现的
        for t in fs:
            pps_to_match.add(t)

    # 也加入已���种子的后继
    extra = set()
    for pk in list(known.keys()):
        extra.add(pk + ",0")
        extra.add(pk + ",0,0")
    pps_to_match |= extra

    # 过滤：只保留标准的
    pps_to_match_clean = set()
    for pk in pps_to_match:
        if pk in known: continue
        seq, std = expand("PPS", pk, 3)
        if std:
            pps_to_match_clean.add(pk)

    print(f"待匹配PPS: {len(pps_to_match_clean)}")

    # 对每个待匹配PPS，检查其基本列第一项是否有Y对应
    for pk in sorted(pps_to_match_clean, key=lambda x: len(x)):
        if pk in known: continue
        seq, std = expand("PPS", pk, 5)
        if not seq: continue
        fs = fs_terms(seq, pk, "PPS", 5)
        if not fs: continue

        # 获取基本列第一项
        pk_f1 = fs[0]

        # 如果是已知PPS表达式的后继（-1项）
        if pk_f1.endswith(",0"):
            pk_f1_base = pk_f1[:-2]
            if pk_f1_base in known:
                yk_f1 = known[pk_f1_base] + ",1"
                # 找Y中基本列第一项也是 yk_f1 的表达式
                for yk, (yseq, ystd, yfs, yparent) in y_db.items():
                    if not yfs: continue
                    if yfs[0] == yk_f1:
                        # 候选!
                        new_matches[pk] = (yk, f"f[1]={fs[0]}≡{yk_f1}")
                        known[pk] = yk  # 添加到known以便后续使用
                        break
        else:
            # 直接匹配
            if pk_f1 in known:
                yk_f1 = known[pk_f1]
                for yk, (yseq, ystd, yfs, yparent) in y_db.items():
                    if not yfs: continue
                    if yfs[0] == yk_f1:
                        new_matches[pk] = (yk, f"f[1]={fs[0]}≡{yk_f1}")
                        known[pk] = yk
                        break

    # 输出结果
    print(f"\n新增匹配: {len(new_matches)}")
    all_matches = dict(known)
    
    # 按PPS长度排序输出
    print(f"\n{'='*80}")
    print(f"{'PPS':<30s} {'Y':<30s} {'来源':<20s}")
    print(f"{'-'*80}")
    for pk in sorted(all_matches.keys(), key=lambda x: (len(x), x)):
        yk = all_matches[pk]
        src = "R1" if pk=="0" else ("R2" if len(pk)>len("0,1") and pk.endswith(",0") else "f[1]对齐")
        print(f"pps {pk:<27s} y {yk:<28s} {src}")


if __name__ == "__main__":
    main()
