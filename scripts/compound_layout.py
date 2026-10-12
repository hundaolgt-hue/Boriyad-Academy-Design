#!/usr/bin/env python3
"""Three separate COMPOUNDS, one per school: a horizontal territory of the site
containing that school's building, its own yard and its own gate, with nothing
outdoor shared.

Client decisions, 12 Oct 2026:
  1 assembly area and hard pitch are the SAME surface, overlapped
  2 dense standing rates
  3 all three schools assemble simultaneously, so all three yards coexist
  4 staff do not intermingle either
  5 roof decks acceptable, sparingly - agricultural plot and greenery go up
  6 separate entry and drop-off per school
Primary and secondary may share structure, so they need no movement joint
between them; the kindergarten does.
"""
import json, math, itertools

site=json.load(open("data/site.json")); prog=json.load(open("data/program.json"))
AREA=site["area_m2"]; GU=prog["totals"]["gross_up_factor"]
def g(k,src): return sum(prog["blocks"][x][src] for x in k)*GU
NEED={"A_client":{"kindergarten":g(["kindergarten"],"client_net_m2"),
                  "primary":g(["primary","central_office"],"client_net_m2"),
                  "secondary":g(["secondary"],"client_net_m2")},
      "B_compliant":{"kindergarten":g(["kindergarten"],"adopt_net_m2"),
                     "primary":g(["primary","central_office"],"adopt_net_m2"),
                     "secondary":g(["secondary"],"adopt_net_m2")}}
MAXLEV={"kindergarten":3,"primary":7,"secondary":7}
RATE={"kindergarten":0.36,"primary":0.36,"secondary":0.45}      # dense, m2/student
STUD={"kindergarten":540,"primary":1750,"secondary":640}
PITCH={"kindergarten":150,"primary":500,"secondary":600}
YARD={s: max(RATE[s]*STUD[s], PITCH[s]) for s in STUD}
GATE={"kindergarten":220,"primary":200,"secondary":180}          # gate + drop-off + forecourt
MAXDEPTH=21.0                                                    # daylight limit on a bar
PERIM=250                                                        # perimeter and fire access

# site width between the east and west boundaries, valid 61.305 <= y <= 127.622
def width(y): return 82.330 - 0.22726*y
def band_area(a,b): return 82.330*(b-a) - 0.11363*(b*b - a*a)
Y0,Y1 = 61.305, 127.622

print("YARD PER COMPOUND  (assembly overlapped with the pitch, dense rates)\n")
print(f"{'school':<14}{'students':>9}{'assembly':>10}{'pitch':>8}{'yard':>8}{'gate+drop':>11}")
for s in ("kindergarten","primary","secondary"):
    print(f"{s:<14}{STUD[s]:>9,}{RATE[s]*STUD[s]:>10,.0f}{PITCH[s]:>8,}{YARD[s]:>8,.0f}{GATE[s]:>11,}")
print(f"{'TOTAL':<14}{sum(STUD.values()):>9,}{'':>10}{'':>8}{sum(YARD.values()):>8,.0f}{sum(GATE.values()):>11,}")

print(f"\n\nTERRITORY REQUIRED PER COMPOUND  (building footprint at max levels + yard + gate)\n")
for scen,req in NEED.items():
    print(f"  --- {scen} ---")
    terr={}
    for s in req:
        fp=req[s]/MAXLEV[s]
        terr[s]=fp+YARD[s]+GATE[s]
        print(f"     {s:<13} footprint {fp:>6.0f} (G+{MAXLEV[s]-1})  + yard {YARD[s]:>5,.0f}"
              f"  + gate {GATE[s]:>4}  = {terr[s]:>6,.0f} m2")
    tot=sum(terr.values())
    print(f"     {'TOTAL':<13} {tot:>50,.0f} m2   + perimeter {PERIM}  = {tot+PERIM:>6,.0f}")
    print(f"     site {AREA:,.0f} m2  ->  spare {AREA-tot-PERIM:>6,.0f} m2"
          f"   {'OK' if AREA-tot-PERIM>0 else 'FAILS'}\n")

print("\nSHAPE TEST — three stacked territories, each holding its own bar and yard\n")
for scen,req in NEED.items():
    terr={s: req[s]/MAXLEV[s]+YARD[s]+GATE[s] for s in req}
    best=None
    for order in itertools.permutations(("kindergarten","primary","secondary")):
        for d1 in [v/2 for v in range(36,61)]:          # territory depths, 18-30 m
            for d2 in [v/2 for v in range(36,61)]:
                d3=(Y1-Y0)-d1-d2
                if not 18<=d3<=30: continue
                ys=[Y0,Y0+d1,Y0+d1+d2,Y1]
                rows=[]; ok=True
                for i,s in enumerate(order):
                    a,b=ys[i],ys[i+1]
                    A=band_area(a,b)
                    fp=req[s]/MAXLEV[s]
                    d=min(MAXDEPTH,b-a)
                    barL=fp/d
                    if barL>width(b)-4.0: ok=False; break   # bar must fit the band width
                    if A < terr[s]: ok=False; break
                    rows.append((s,a,b,A,fp,barL,d,A-terr[s]))
                if not ok: continue
                slack=min(r[7] for r in rows)
                if best is None or slack>best[0]: best=(slack,rows,order)
    print(f"  --- {scen} ---")
    if best is None:
        print("     NO ARRANGEMENT FOUND\n"); continue
    for s,a,b,A,fp,barL,d,sl in best[1]:
        print(f"     {s:<13} territory y {a:>5.1f}-{b:>5.1f} ({b-a:>4.1f} m deep, {A:>6,.0f} m2)  "
              f"bar {barL:>5.1f} x {d:<4.1f} = {fp:>5.0f} m2  slack {sl:>6,.0f} m2")
    print(f"     tightest compound has {best[0]:,.0f} m2 to spare\n")
