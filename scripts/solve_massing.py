#!/usr/bin/env python3
"""Massing feasibility search for the Boriyad Youth Academy campus.

Two candidate topologies are evaluated against two programme scenarios.

  T1 "Three Bars" : three parallel true east-west bars separated by movement
                    joints; each school's playing ground sits on its own roof.
  T2 "Court"      : two east-west bars plus one north-south volume on the east
                    road edge; one shared open court at grade.

  Scenario A : the client space programme as issued (school_space_program.docx)
  Scenario B : that programme reconciled against Qajeelfama Lakk. 04/2016

Each bar is sized to its own requirement rather than filling its band, so the
63 per cent coverage ceiling is respected. The site boundary is piecewise
linear, so the widest axis-aligned rectangle in a horizontal band is solved in
closed form rather than searched.

Writes data/seed_layouts.json.
"""
import json, math

site = json.load(open("data/site.json"))
prog = json.load(open("data/program.json"))
AREA = site["area_m2"]
GU = prog["totals"]["gross_up_factor"]
MAXCOV = 0.63

def _gfa(keys, src):
    return sum(prog["blocks"][k][src] for k in keys) * GU

NEED_B = {"kindergarten": _gfa(["kindergarten"], "adopt_net_m2"),
          "primary":      _gfa(["primary", "central_office"], "adopt_net_m2"),
          "secondary":    _gfa(["secondary"], "adopt_net_m2")}
NEED_A = {"kindergarten": _gfa(["kindergarten"], "client_net_m2"),
          "primary":      _gfa(["primary", "central_office"], "client_net_m2"),
          "secondary":    _gfa(["secondary"], "client_net_m2")}
SCENARIOS = {"B_compliant": NEED_B, "A_client": NEED_A}

SCHOOLS = ("kindergarten", "primary", "secondary")
PLAY   = {"kindergarten": (15, 10), "primary": (25, 20), "secondary": (30, 20)}
MAXLEV = {"kindergarten": 3, "primary": 7, "secondary": 7}
SB     = {"west": 3.0, "east": 2.0, "south": 2.0, "north": 2.0}
GAPS   = (3.0, 4.0, 5.0)
TOL    = 0.0           # target the full requirement; H6 allows 3% tolerance
MINLEN = 24.0          # shortest sensible bar
Y_LO, Y_HI = 61.0, 128.0

def west_at(y):  return 41.882 + 0.25783 * (y - 61.305)
def east_at(y):  return 109.918 + 0.030569 * (y - 49.453)
def south_at(x): return 49.453 + 0.174196 * (109.918 - x)
def north_at(x): return 127.622 + 0.158867 * (x - 58.980) if x < 66.779 \
                 else 128.861 + 0.110606 * (x - 66.779)

def band(y0, y1):
    """(x_west, x_east) of the widest axis-aligned rectangle between y0 and y1,
       after setbacks, or None."""
    if y1 <= y0 or y1 > 127.622:
        return None
    x0 = west_at(y1) + SB["west"]
    x1 = east_at(y0) - SB["east"]
    if y0 < 61.305:
        x0 = max(x0, 109.918 - (y0 - 49.453) / 0.174196 + SB["west"])
    if y0 < south_at(x0) + SB["south"]:
        return None
    if y1 > north_at(x0) - SB["north"]:
        return None
    return (x0, x1) if x1 - x0 >= MINLEN else None

def ar(r): return (r[2] - r[0]) * (r[3] - r[1])

def play_fits(w, d, need):
    L, S = need
    return (w >= L and d >= S) or (w >= S and d >= L)

def size_bar(school, depth, lmax, req, roof_playground):
    """Fewest levels and shortest length meeting the GFA requirement in a band
       of the given depth. Returns (levels, length) or None."""
    for n in range(1, MAXLEV[school] + 1):
        L = req[school] * (1 - TOL) / n / depth
        if roof_playground:
            pl, ps = PLAY[school]
            if depth < ps:
                continue
            L = max(L, pl)
        L = max(L, MINLEN)
        if L <= lmax:
            return (n, round(L, 2))
    return None

results = {}

# ------------------------------------------------------------------ T1
for scen, req in SCENARIOS.items():
    for gap in GAPS:
        best = None
        for dK in (17, 18, 19, 20):
            for dP in (17, 18, 19, 20, 21):
                for dS in (17, 18, 19, 20, 21):
                    for y0 in [v / 2 for v in range(int(Y_LO * 2), int(Y_LO * 2) + 15)]:
                        ys = [y0, y0 + dK,
                              y0 + dK + gap, y0 + dK + gap + dP,
                              y0 + dK + gap + dP + gap, y0 + dK + gap + dP + gap + dS]
                        if ys[5] > Y_HI:
                            continue
                        bands = [band(ys[0], ys[1]), band(ys[2], ys[3]), band(ys[4], ys[5])]
                        if not all(bands):
                            continue
                        depths = [dK, dP, dS]
                        for order in (("kindergarten", "primary", "secondary"),
                                      ("kindergarten", "secondary", "primary")):
                            assign, lv, ok = {}, {}, True
                            for k, s in enumerate(order):
                                bx, d = bands[k], depths[k]
                                sized = size_bar(s, d, bx[1] - bx[0], req, True)
                                if sized is None:
                                    ok = False
                                    break
                                n, L = sized
                                lv[s] = n
                                assign[s] = (bx[1] - L, ys[2 * k], bx[1], ys[2 * k + 1])
                            if not ok:
                                continue
                            fp = sum(ar(r) for r in assign.values())
                            if fp > MAXCOV * AREA:
                                continue
                            gfa = sum(ar(assign[s]) * lv[s] for s in assign)
                            opn = AREA - fp
                            score = opn + 0.3 * gfa - 80 * sum(lv.values()) - 2 * (gap - 3)
                            if best is None or score > best[0]:
                                best = (score, assign, lv, fp, gfa, opn, None, 0, gap)
        key = ("T1_three_bars", scen)
        if best and (key not in results or best[0] > results[key][0]):
            results[key] = best

# ------------------------------------------------------------------ T2
for scen, req in SCENARIOS.items():
    for gap in GAPS:
        best = None
        for dK in (17, 18, 19, 20):
            for dP in (17, 18, 19, 20, 21):
                for y0 in [v / 2 for v in range(int(Y_LO * 2), int(Y_LO * 2) + 11)]:
                    y1 = y0 + dK
                    bK = band(y0, y1)
                    if not bK:
                        continue
                    for yN in [v / 2 for v in range(int((y1 + 20) * 2), int((Y_HI - dP) * 2) + 1)]:
                        bP = band(yN, yN + dP)
                        if not bP:
                            continue
                        ys, ye = y1 + gap, yN - gap
                        if ye - ys < 18:
                            continue
                        bM = band(ys, ye)
                        if not bM:
                            continue
                        for dE in (16, 17, 18, 19, 20, 21, 22):
                            rS = (bM[1] - dE, ys, bM[1], ye)
                            if rS[0] < bM[0] + MINLEN:
                                continue
                            for sEast in ("secondary", "primary"):
                                sMid = [s for s in SCHOOLS
                                        if s not in ("kindergarten", sEast)][0]
                                assign, lv, ok = {}, {}, True
                                nE = math.ceil(req[sEast] * (1 - TOL) / ar(rS) - 1e-9)
                                if not 1 <= nE <= MAXLEV[sEast]:
                                    continue
                                lv[sEast] = nE
                                assign[sEast] = rS
                                for s, bx, yy, d in (("kindergarten", bK, (y0, y1), dK),
                                                     (sMid, bP, (yN, yN + dP), dP)):
                                    sized = size_bar(s, d, bx[1] - bx[0], req, False)
                                    if sized is None:
                                        ok = False
                                        break
                                    n, L = sized
                                    lv[s] = n
                                    assign[s] = (bx[1] - L, yy[0], bx[1], yy[1])
                                if not ok:
                                    continue
                                fp = sum(ar(r) for r in assign.values())
                                if fp > MAXCOV * AREA:
                                    continue
                                court = (bM[0], ys, rS[0] - 2.0, ye)
                                ca = ar(court) if court[2] > court[0] else 0
                                if ca < 550:
                                    continue
                                cw, cd = court[2] - court[0], court[3] - court[1]
                                roof = {s: play_fits(assign[s][2] - assign[s][0],
                                                     assign[s][3] - assign[s][1], PLAY[s])
                                        for s in SCHOOLS}
                                crt = {s: play_fits(cw, cd, PLAY[s]) for s in SCHOOLS}
                                if not all(roof[s] or crt[s] for s in SCHOOLS):
                                    continue
                                gfa = sum(ar(assign[s]) * lv[s] for s in assign)
                                opn = AREA - fp
                                score = opn + 0.3 * gfa + 0.6 * ca - 80 * sum(lv.values())
                                if best is None or score > best[0]:
                                    best = (score, assign, lv, fp, gfa, opn,
                                            court, ca, gap, roof, crt)
        key = ("T2_court", scen)
        if best and (key not in results or best[0] > results[key][0]):
            results[key] = best

# ------------------------------------------------------------------ report
out = {}
print(f"{'topology':<16}{'scenario':<14}{'gap':>5}{'footprint':>11}{'cov%':>7}"
      f"{'GFA':>9}{'req':>9}{'open':>8}   levels")
for name in ("T1_three_bars", "T2_court"):
    for scen in SCENARIOS:
        key = (name, scen)
        if key not in results:
            print(f"{name:<16}{scen:<14}   INFEASIBLE")
            out[f"{name}__{scen}"] = {"topology": name, "scenario": scen, "feasible": False}
            continue
        b = results[key]
        assign, lv, fp, gfa, opn, gap = b[1], b[2], b[3], b[4], b[5], b[8]
        req = sum(SCENARIOS[scen].values())
        lvs = "  ".join(f"{s[:3].upper()} G+{lv[s]-1}" for s in SCHOOLS)
        print(f"{name:<16}{scen:<14}{gap:>5.1f}{fp:>11,.0f}{100*fp/AREA:>7.1f}"
              f"{gfa:>9,.0f}{req:>9,.0f}{opn:>8,.0f}   {lvs}")
        rec = {"topology": name, "scenario": scen, "feasible": True,
               "separation_gap_m": gap,
               "volumes": {s: {
                   "x0": round(assign[s][0], 2), "y0": round(assign[s][1], 2),
                   "x1": round(assign[s][2], 2), "y1": round(assign[s][3], 2),
                   "length_ew_m": round(assign[s][2] - assign[s][0], 2),
                   "depth_ns_m": round(assign[s][3] - assign[s][1], 2),
                   "levels": lv[s],
                   "footprint_m2": round(ar(assign[s]), 1),
                   "gfa_m2": round(ar(assign[s]) * lv[s]),
                   "required_gfa_m2": round(SCENARIOS[scen][s])} for s in assign},
               "footprint_m2": round(fp, 1), "coverage_pct": round(100 * fp / AREA, 1),
               "gfa_m2": round(gfa), "required_gfa_m2": round(req),
               "open_at_grade_m2": round(opn)}
        if name == "T2_court":
            court, ca = b[6], b[7]
            rec["court"] = {"x0": round(court[0], 2), "y0": round(court[1], 2),
                            "x1": round(court[2], 2), "y1": round(court[3], 2),
                            "width_ew_m": round(court[2] - court[0], 1),
                            "depth_ns_m": round(court[3] - court[1], 1),
                            "area_m2": round(ca)}
            rec["playground_on_own_roof"] = b[9]
            rec["playground_fits_in_court"] = b[10]
        out[f"{name}__{scen}"] = rec

json.dump(out, open("data/seed_layouts.json", "w"), indent=2)

for key, r in out.items():
    if not r.get("feasible"):
        continue
    print(f"\n--- {key} ---")
    for s in SCHOOLS:
        v = r["volumes"][s]
        print(f"  {s:<13} x {v['x0']:>6.2f} - {v['x1']:>6.2f}   y {v['y0']:>6.2f} - {v['y1']:>6.2f}   "
              f"{v['length_ew_m']:>5.1f} x {v['depth_ns_m']:<4.1f} = {v['footprint_m2']:>6.1f} m2   "
              f"G+{v['levels']-1}   GFA {v['gfa_m2']:>5} (need {v['required_gfa_m2']})")
    if "court" in r:
        c = r["court"]
        print(f"  court         {c['width_ew_m']} x {c['depth_ns_m']} = {c['area_m2']} m2")
print("\nwrote data/seed_layouts.json")
