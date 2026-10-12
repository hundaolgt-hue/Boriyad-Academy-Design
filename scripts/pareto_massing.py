#!/usr/bin/env python3
"""Pareto front of (total footprint, sum of levels) for topology T1, per
scenario. Shows how much open ground is bought by building taller, and where
the footprint floor actually comes from."""
import json, math
site=json.load(open("data/site.json")); prog=json.load(open("data/program.json"))
AREA=site["area_m2"]; GU=prog["totals"]["gross_up_factor"]
def g(keys,src): return sum(prog["blocks"][k][src] for k in keys)*GU
REQ={"B_compliant":{"kindergarten":g(["kindergarten"],"adopt_net_m2"),
                    "primary":g(["primary","central_office"],"adopt_net_m2"),
                    "secondary":g(["secondary"],"adopt_net_m2")},
     "A_client":{"kindergarten":g(["kindergarten"],"client_net_m2"),
                 "primary":g(["primary","central_office"],"client_net_m2"),
                 "secondary":g(["secondary"],"client_net_m2")}}
PLAY={"kindergarten":(15,10),"primary":(25,20),"secondary":(30,20)}
MAXLEV={"kindergarten":3,"primary":7,"secondary":7}
SCH=("kindergarten","primary","secondary")
DEPTH={"kindergarten":17.0,"primary":20.0,"secondary":20.0}
BANDW=53.3   # representative band width; the north band is the tightest at ~50 m
MINPLATE={"kindergarten":0,"primary":500,"secondary":500}   # vertical efficiency floor

def fp_for(s,n,req,roof_play,plate_floor):
    need=req[s]/n
    d=DEPTH[s]
    L=need/d
    if roof_play:
        pl,ps=PLAY[s]
        if d<ps: return None
        L=max(L,pl)
    f=L*d
    if plate_floor: f=max(f,MINPLATE[s])
    L=f/d
    return f if L<=BANDW else None

for scen in ("A_client","B_compliant"):
    req=REQ[scen]
    print(f"\n=== {scen}  (required GFA {sum(req.values()):,.0f} m2) ===")
    for roof_play,plate_floor,label in ((True,True,"playgrounds on roofs + plate floor"),
                                        (True,False,"playgrounds on roofs only"),
                                        (False,False,"no roof-playground constraint")):
        rows=[]
        for nK in range(1,MAXLEV["kindergarten"]+1):
            for nP in range(1,MAXLEV["primary"]+1):
                for nS in range(1,MAXLEV["secondary"]+1):
                    fs={}
                    ok=True
                    for s,n in (("kindergarten",nK),("primary",nP),("secondary",nS)):
                        f=fp_for(s,n,req,roof_play,plate_floor)
                        if f is None: ok=False; break
                        fs[s]=f
                    if not ok: continue
                    tot=sum(fs.values())
                    if tot>0.63*AREA: continue
                    rows.append((tot,nK+nP+nS,(nK,nP,nS),fs))
        rows.sort()
        front=[]
        bestlv=99
        for tot,lvs,ns,fs in rows:
            if lvs<bestlv: front.append((tot,lvs,ns,fs)); bestlv=lvs
        print(f"\n  -- {label} --")
        print(f"     {'footprint':>10}{'cov%':>7}{'open':>8}{'levels':>9}   K/P/S plates")
        for tot,lvs,ns,fs in front[:6]:
            plates="  ".join(f"{s[:1].upper()}{fs[s]:.0f}x{ns[i]}" for i,s in enumerate(SCH))
            print(f"     {tot:>10,.0f}{100*tot/AREA:>7.1f}{AREA-tot:>8,.0f}"
                  f"   G+{ns[0]-1}/{ns[1]-1}/{ns[2]-1}   {plates}")
