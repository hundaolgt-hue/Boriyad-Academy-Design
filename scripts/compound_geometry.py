#!/usr/bin/env python3
"""Final three-compound geometry for drawing. Adds the 500 m2 minimum plate
floor so no school becomes a point block, and emits local coordinates."""
import json, math, itertools
site=json.load(open("data/site.json")); prog=json.load(open("data/program.json"))
AREA=site["area_m2"]; GU=prog["totals"]["gross_up_factor"]
def g(k,src): return sum(prog["blocks"][x][src] for x in k)*GU
NEED={"kindergarten":g(["kindergarten"],"client_net_m2"),
      "primary":g(["primary","central_office"],"client_net_m2"),
      "secondary":g(["secondary"],"client_net_m2")}
NEED_B={"kindergarten":g(["kindergarten"],"adopt_net_m2"),
        "primary":g(["primary","central_office"],"adopt_net_m2"),
        "secondary":g(["secondary"],"adopt_net_m2")}
MAXLEV={"kindergarten":3,"primary":7,"secondary":7}
MINPLATE={"kindergarten":0,"primary":500,"secondary":500}
YARD={"kindergarten":194,"primary":630,"secondary":600}
GATE={"kindergarten":220,"primary":200,"secondary":180}
MAXD=21.0; SBE=2.0; SBW=3.0; JOINT=3.0
def west(y): return 41.882+0.25783*(y-61.305)
def east(y): return 109.918+0.030569*(y-49.453)
def barea(a,b): return 82.330*(b-a)-0.11363*(b*b-a*a)
Y0,Y1=61.4,127.5

def plate(s,req):
    """smallest plate meeting the requirement, respecting the level cap and
       the minimum-plate floor; returns (levels, footprint)"""
    best=None
    for n in range(1,MAXLEV[s]+1):
        f=max(req[s]/n, MINPLATE[s])
        if best is None or f<best[1]: best=(n,f)
    return best

for lbl,req in (("A_client",NEED),("B_compliant",NEED_B)):
    P={s:plate(s,req) for s in req}
    TERR={s:P[s][1]+YARD[s]+GATE[s] for s in req}
    print(f"\n=== {lbl} ===")
    for s in ("kindergarten","primary","secondary"):
        print(f"  {s:<13} G+{P[s][0]-1}  plate {P[s][1]:>6.0f}  yard {YARD[s]:>4}  gate {GATE[s]:>4}"
              f"  territory {TERR[s]:>6,.0f} m2")
    print(f"  total territory {sum(TERR.values()):,.0f} + perimeter 250 = {sum(TERR.values())+250:,.0f}"
          f"  against site {AREA:,.0f}  -> {AREA-sum(TERR.values())-250:+,.0f} m2")
    # stack the three bands, widest band to the hungriest compound
    best=None
    for order in itertools.permutations(req):
        for d1 in [v/4 for v in range(68,112)]:
            for d2 in [v/4 for v in range(68,112)]:
                d3=(Y1-Y0)-d1-d2-JOINT
                if not 17<=d3<=30: continue
                ys=[(Y0,Y0+d1),(Y0+d1+JOINT,Y0+d1+JOINT+d2),(Y1-d3,Y1)]
                rows=[];ok=True
                for i,s in enumerate(order):
                    a,b=ys[i]; A=barea(a,b)
                    n,f=P[s]; d=min(MAXD,b-a); L=f/d
                    xe=east(a)-SBE; xw=west(b)+SBW
                    if L>xe-xw-10: ok=False;break
                    if A<TERR[s]: ok=False;break
                    rows.append((s,a,b,A,n,f,d,L,xe,xw,A-TERR[s]))
                if not ok: continue
                sl=min(r[10] for r in rows)
                if best is None or sl>best[0]: best=(sl,rows)
    if best is None:
        print("  SHAPE: no arrangement\n"); continue
    out={}
    for s,a,b,A,n,f,d,L,xe,xw,sl in best[1]:
        by0=b-d
        print(f"  {s:<13} band y {a:>6.2f}-{b:>6.2f} ({A:>6,.0f} m2)  "
              f"bar x {xe-L:>6.2f}-{xe:>6.2f} y {by0:>6.2f}-{b:>6.2f}  "
              f"{L:>5.1f}x{d:<4.1f} G+{n-1}  slack {sl:>5,.0f}")
        out[s]={"band_y0":round(a,2),"band_y1":round(b,2),"band_area_m2":round(A),
                "bar":{"x0":round(xe-L,2),"y0":round(by0,2),"x1":round(xe,2),"y1":round(b,2)},
                "levels":n,"plate_m2":round(f),"yard_m2":YARD[s],"gate_m2":GATE[s],
                "yard_west_limit_x":round(xw,2),"slack_m2":round(sl)}
    if lbl=="A_client":
        json.dump(out,open("data/compound_geometry.json","w"),indent=2)
        print("  -> data/compound_geometry.json")
