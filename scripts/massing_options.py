#!/usr/bin/env python3
"""Comparative massing study for the Boriyad campus.

Six topologies are generated and scored against the same constraint set and
the same resolved programme, so the choice can be argued from numbers rather
than from preference.

  S1  east-west bands, buildings EAST on the road, yards west
  S2  east-west bands, buildings WEST, yards east onto the road
  S3  north-south strips, buildings east, yards west
  S4  primary and secondary stacked vertically in one shared-structure block,
      kindergarten separate - two bands instead of three
  S5  compact blocks (aspect ratio driven toward 1) in east-west bands
  S6  deep bars, 21 m everywhere, to shorten the buildings and widen the yards

Writes data/massing_options.json.
"""
import json, math, os, itertools

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
site = json.load(open(os.path.join(HERE, "data", "site.json")))
prog = json.load(open(os.path.join(HERE, "data", "program_resolved.json")))
cfg = prog["config"]
AREA = site["area_m2"]
SCHOOLS = ("kindergarten", "primary", "secondary")
STUD = prog["capacity"]["total_students"]

def west(y):  return 41.882 + 0.25783 * (y - 61.305)
def east(y):  return 109.918 + 0.030569 * (y - 49.453)
def south(x): return 49.453 + 0.174196 * (109.918 - x)
def north(x): return 127.622 + 0.158867 * (x - 58.980) if x < 66.779 \
              else 128.861 + 0.110606 * (x - 66.779)
Y_LO, Y_HI = 61.305, 127.622
SB = cfg["setback_m"]

def band(y0, y1):
    if y1 <= y0 or y1 > Y_HI: return None
    x0 = west(y1) + SB["west"]
    x1 = east(y0) - SB["east"]
    if y0 < Y_LO:
        x0 = max(x0, 109.918 - (y0 - 49.453) / 0.174196 + SB["west"])
    if y0 < south(x0) + SB["south"] or y1 > north(x0) - SB["north"]: return None
    return (x0, x1)

def band_area(a, b):
    a, b = max(a, Y_LO), min(b, Y_HI)
    return 0.0 if b <= a else 82.330 * (b - a) - 0.11363 * (b * b - a * a)

Y_TOP = Y_HI
while Y_TOP > Y_LO and band(Y_TOP - 17.0, Y_TOP) is None: Y_TOP -= 0.25
Y_BOT = Y_LO
while Y_BOT < Y_TOP and band(Y_BOT, Y_BOT + 17.0) is None: Y_BOT += 0.25

# ---------------- demand ----------------
def plate_options(school, gfa):
    """(levels, plate) pairs that satisfy the GFA, level cap and plate floor."""
    out = []
    for n in range(1, cfg["max_levels"][school] + 1):
        out.append((n, max(gfa / n, cfg["min_plate_m2"][school])))
    return out

DEM = {}
for s in SCHOOLS:
    st = cfg["enrolment"][s]
    asm = st * cfg["standing_rate_m2_per_student"][s]
    pit = cfg["playing_ground_m2"][s]
    yard = max(asm, pit) if cfg["overlap_assembly_with_pitch"] else asm + pit
    DEM[s] = {"students": st, "gfa": prog["compound_gfa_m2"][s],
              "assembly": asm, "yard": yard,
              "yard_need": yard * (1 + cfg["yard_circulation_factor"]),
              "rect": cfg["playing_ground_min_rect_m"][s],
              "gate": cfg["gate_and_dropoff_m2"][s]}
PAV = prog.get("central_office_standalone_m2", 0.0)
PAV_FP = PAV / 2.0 if PAV else 0.0
MAXD, MINL = cfg["max_bar_depth_m"], cfg["min_bar_length_m"]
KGJ = cfg["separation"]["kg_joint_m"]
PSJ = cfg["separation"]["shared_structure_joint_m"] \
      if cfg["separation"]["primary_secondary_may_share_structure"] else KGJ
MIN_OPEN = max(cfg.get("min_open_at_grade_m2", 0),
               cfg.get("min_open_at_grade_per_student_m2", 0) * STUD)
GH, UH = cfg["ground_floor_h_m"], cfg["upper_floor_h_m"]

def rect_fits(w, d, pr):
    if not cfg.get("enforce_playing_ground_rect", True): return True
    return (w >= pr[0] and d >= pr[1]) or (w >= pr[1] and d >= pr[0])

def score(items, label, note, nbands):
    """items: list of dicts with school, bar(x0,y0,x1,y1), levels, yard_area,
       yard_strip(w,d), band(y0,y1)"""
    fp = sum((i["bar"][2] - i["bar"][0]) * (i["bar"][3] - i["bar"][1]) for i in items) + PAV_FP
    opn = AREA - fp
    gates = sum(DEM[i["school"]]["gate"] for i in items)
    used = fp + sum(DEM[i["school"]]["yard"] for i in items) + gates \
           + cfg["perimeter_and_fire_m2"] + (cfg["gate_pavilion_m2"] - PAV_FP if PAV else 0)
    ew = sum(1 for i in items
             if (i["bar"][2] - i["bar"][0]) >= (i["bar"][3] - i["bar"][1]))
    lv = sum(i["levels"] for i in items)
    gfa = sum(DEM[i["school"]]["gfa"] for i in items) + PAV
    facade = sum(2 * ((i["bar"][2] - i["bar"][0]) + (i["bar"][3] - i["bar"][1]))
                 * (GH + (i["levels"] - 1) * UH) for i in items)
    hmax = GH + (max(i["levels"] for i in items) - 1) * UH
    # how far each yard sits from the assumed road on the east boundary
    road_setback = sum((east((i["band"][0] + i["band"][1]) / 2) -
                        (i["yard_cx"])) for i in items) / len(items)
    # At 9 deg N the assembly runs 07:30-08:00 with the sun low in the east.
    # A yard west of its building is shaded then, and sheltered from the
    # October-May north-east trades that carry the dust.
    shaded = sum(1 for i in items if i["yard_cx"] < (i["bar"][0] + i["bar"][2]) / 2)
    fails = []
    if used > AREA: fails.append("C1 ground demand")
    if fp > cfg["max_site_coverage"] * AREA: fails.append("C2 coverage")
    if opn < MIN_OPEN: fails.append("C3 open at grade")
    if hmax > cfg["max_height_m"]: fails.append("C5 height")
    return {"id": label, "note": note, "bands": nbands, "feasible": not fails,
            "fails": fails,
            "footprint_m2": round(fp, 1), "coverage_pct": round(100 * fp / AREA, 1),
            "open_at_grade_m2": round(opn, 1),
            "open_per_student_m2": round(opn / STUD, 3),
            "ground_demand_m2": round(used, 1), "spare_m2": round(AREA - used, 1),
            "buildings_east_west": ew, "sum_levels": lv,
            "facade_per_gfa": round(facade / gfa, 3),
            "tallest_m": round(hmax, 1),
            "mean_yard_distance_from_road_m": round(road_setback, 1),
            "yards_shaded_at_assembly": shaded,
            "min_yard_slack_m2": round(min(i["yard_area"] - DEM[i["school"]]["yard_need"]
                                           for i in items), 1),
            "items": [{"school": i["school"], "levels": i["levels"],
                       "bar": [round(v, 2) for v in i["bar"]],
                       "plate_m2": round((i["bar"][2]-i["bar"][0])*(i["bar"][3]-i["bar"][1]), 1),
                       "yard_m2": round(i["yard_area"], 1)} for i in items]}

RESULTS = []

# ---------------- S1 / S2 / S5 / S6 : east-west bands ----------------
def ew_bands(label, note, side, aspect_target=None, deepest_first=False):
    best = None
    for order in itertools.permutations(SCHOOLS):
        joints = [KGJ if "kindergarten" in (order[i], order[i+1]) else PSJ for i in range(2)]
        for ystart in [Y_BOT + v / 4 for v in range(0, 9)]:
            for d1 in [v / 4 for v in range(68, 129)]:
                for d2 in [v / 4 for v in range(68, 129)]:
                    d3 = Y_TOP - ystart - d1 - d2 - sum(joints)
                    if not 17 <= d3 <= 32: continue
                    ys = [(ystart, ystart + d1),
                          (ystart + d1 + joints[0], ystart + d1 + joints[0] + d2),
                          (Y_TOP - d3, Y_TOP)]
                    items, ok = [], True
                    for i, s in enumerate(order):
                        a, b = ys[i]
                        bx = band(a, b)
                        if bx is None: ok = False; break
                        A = band_area(a, b)
                        cand = None
                        for n, pl in plate_options(s, DEM[s]["gfa"]):
                            if GH + (n - 1) * UH > cfg["max_height_m"]: continue
                            drange = [min(MAXD, b - a) - k * 0.5 for k in range(0, 16)]
                            if deepest_first:
                                drange = drange[:3]      # stay at the deep end
                            for d in drange:
                                if d is None or d < 14 or d > min(MAXD, b - a): continue
                                L = pl / d
                                if L < MINL: continue
                                if aspect_target and L / d > aspect_target: continue
                                if side == "east":
                                    bar = (bx[1] - L, b - d, bx[1], b)
                                    yw = (bx[1] - L) - bx[0] - 3.0
                                    ycx = bx[0] + yw / 2
                                else:
                                    bar = (bx[0], b - d, bx[0] + L, b)
                                    yw = bx[1] - (bx[0] + L) - 3.0
                                    ycx = bx[0] + L + 3.0 + yw / 2
                                ya = A - pl
                                if yw < 6 or ya < DEM[s]["yard_need"]: continue
                                if not rect_fits(yw, b - a, DEM[s]["rect"]): continue
                                cand = {"school": s, "bar": bar, "levels": n,
                                        "yard_area": ya, "yard_cx": ycx, "band": (a, b)}
                                break
                            if cand: break
                        if not cand: ok = False; break
                        items.append(cand)
                    if not ok: continue
                    r = score(items, label, note, 3)
                    key = (r["feasible"], r["open_per_student_m2"], -r["sum_levels"])
                    if best is None or key > best[0]: best = (key, r)
    return best[1] if best else {"id": label, "note": note, "bands": 3,
                                 "feasible": False, "fails": ["no arrangement"]}

RESULTS.append(ew_bands("S1", "East-west bands, buildings east on the road, yards west", "east"))
RESULTS.append(ew_bands("S2", "East-west bands, buildings west, yards east onto the road", "west"))
RESULTS.append(ew_bands("S5", "Compact blocks, aspect ratio held near 1, in east-west bands",
                        "east", aspect_target=1.6))
RESULTS.append(ew_bands("S6", "Deepest bars the band allows, shortening the buildings "
                        "to widen the yards", "east", deepest_first=True))

# ---------------- S3 : north-south strips ----------------
def ns_strips():
    best = None
    X_LO, X_HI = 48.0, 110.0
    for order in itertools.permutations(SCHOOLS):
        joints = [KGJ if "kindergarten" in (order[i], order[i+1]) else PSJ for i in range(2)]
        for w1 in [v / 2 for v in range(36, 61)]:
            for w2 in [v / 2 for v in range(36, 61)]:
                xs = [(X_LO, X_LO + w1),
                      (X_LO + w1 + joints[0], X_LO + w1 + joints[0] + w2)]
                x3a = xs[1][1] + joints[1]
                if x3a + 18 > X_HI: continue
                xs.append((x3a, X_HI))
                items, ok = [], True
                for i, s in enumerate(order):
                    xa, xb = xs[i]
                    # a strip runs north-south; its usable y range is set by the
                    # diagonal north and south edges at its west edge
                    ya = max(Y_BOT, south(xa) + SB["south"])
                    yb = min(Y_TOP, north(xa) - SB["north"])
                    if yb - ya < 30: ok = False; break
                    A = (xb - xa) * (yb - ya)
                    cand = None
                    for n, pl in plate_options(s, DEM[s]["gfa"]):
                        if GH + (n - 1) * UH > cfg["max_height_m"]: continue
                        d = min(MAXD, xb - xa)          # depth is the strip width
                        L = pl / d                       # length runs north-south
                        if L < MINL or L > (yb - ya) - 14: continue
                        yw = xb - xa
                        yd = (yb - ya) - L - 3.0
                        ya_area = A - pl
                        if yd < 6 or ya_area < DEM[s]["yard_need"]: continue
                        if not rect_fits(yw, yd, DEM[s]["rect"]): continue
                        cand = {"school": s, "bar": (xa, yb - L, xb, yb), "levels": n,
                                "yard_area": ya_area, "yard_cx": (xa + xb) / 2,
                                "band": (ya, yb)}
                        break
                    if not cand: ok = False; break
                    items.append(cand)
                if not ok: continue
                r = score(items, "S3", "North-south strips, buildings north, yards south", 3)
                key = (r["feasible"], r["open_per_student_m2"], -r["sum_levels"])
                if best is None or key > best[0]: best = (key, r)
    return best[1] if best else {"id": "S3",
        "note": "North-south strips, buildings north, yards south",
        "bands": 3, "feasible": False, "fails": ["no arrangement"]}
RESULTS.append(ns_strips())

# ---------------- S4 : primary and secondary stacked vertically ----------
def stacked():
    """One shared-structure block carries primary on the lower floors and
       secondary above, each with its own cores and its own entrance. Two bands
       instead of three, so the freed band becomes yard."""
    best = None
    WHY = set()
    gfa_ps = DEM["primary"]["gfa"] + DEM["secondary"]["gfa"]
    for ystart in [Y_BOT + v / 4 for v in range(0, 9)]:
        for d1 in [v / 4 for v in range(68, 129)]:
            d2 = Y_TOP - ystart - d1 - KGJ
            if not 17 <= d2 <= 34: continue
            for kg_first in (True, False):
                ys = [(ystart, ystart + d1), (ystart + d1 + KGJ, Y_TOP)]
                plan = [("kindergarten", ys[0]), ("PS", ys[1])] if kg_first \
                       else [("PS", ys[0]), ("kindergarten", ys[1])]
                items, ok = [], True
                for who, (a, b) in plan:
                    bx = band(a, b)
                    if bx is None: ok = False; break
                    A = band_area(a, b)
                    if who == "kindergarten":
                        sset, gfa, cap = ["kindergarten"], DEM["kindergarten"]["gfa"], \
                                         cfg["max_levels"]["kindergarten"]
                    else:
                        sset, gfa, cap = ["primary", "secondary"], gfa_ps, 7
                    need = sum(DEM[s]["yard_need"] for s in sset)
                    cand = None
                    for n in range(1, cap + 1):
                        if GH + (n - 1) * UH > cfg["max_height_m"]: continue
                        pl = max(gfa / n, max(cfg["min_plate_m2"][s] for s in sset))
                        for k in range(0, 16):
                            d = min(MAXD, b - a) - k * 0.5
                            if d < 14: break
                            L = pl / d
                            if L < MINL: continue
                            yw = (bx[1] - L) - bx[0] - 3.0
                            ya = A - pl
                            if yw < 6 or ya < need:
                                WHY.add("yard area or width"); continue
                            if len(sset) == 1:
                                rect_ok = rect_fits(yw, b - a, DEM[sset[0]]["rect"])
                            else:
                                # two schools share the block, so each needs its own
                                # clear pitch: one yard west, one east of the building
                                spare = (bx[1] - bx[0]) - L - 6.0
                                rect_ok = False
                                for wW in [v for v in range(8, int(spare) + 1)]:
                                    wE = spare - wW
                                    if wE < 8: break
                                    if rect_fits(wW, b - a, DEM["primary"]["rect"]) and \
                                       rect_fits(wE, b - a, DEM["secondary"]["rect"]):
                                        rect_ok = True; break
                                if not rect_ok:
                                    # or one yard west and one in the depth left over
                                    rest = (b - a) - d - 3.0
                                    rect_ok = rect_fits(yw, b - a, DEM["primary"]["rect"]) and \
                                              rect_fits(bx[1] - bx[0], rest, DEM["secondary"]["rect"])
                            if not rect_ok:
                                WHY.add(f"no room for two clear pitches beside a "
                                        f"{L:.0f} m long block in a {bx[1]-bx[0]:.0f} m band")
                                continue
                            cand = {"school": sset[0] if len(sset) == 1 else "primary+secondary",
                                    "bar": (bx[1] - L, b - d, bx[1], b), "levels": n,
                                    "yard_area": ya, "yard_cx": bx[0] + yw / 2,
                                    "band": (a, b), "_set": sset}
                            break
                        if cand: break
                    if not cand: ok = False; break
                    items.append(cand)
                if not ok: continue
                fp = sum((i["bar"][2]-i["bar"][0])*(i["bar"][3]-i["bar"][1]) for i in items) + PAV_FP
                opn = AREA - fp
                gates = sum(DEM[s]["gate"] for i in items for s in i["_set"])
                yards = sum(i["yard_area"] for i in items)
                yard_req = sum(DEM[s]["yard"] for i in items for s in i["_set"])
                used = fp + yard_req + gates + cfg["perimeter_and_fire_m2"] + \
                       (cfg["gate_pavilion_m2"] - PAV_FP if PAV else 0)
                ew = sum(1 for i in items if (i["bar"][2]-i["bar"][0]) >= (i["bar"][3]-i["bar"][1]))
                lv = sum(i["levels"] for i in items)
                gfa_all = DEM["kindergarten"]["gfa"] + gfa_ps + PAV
                facade = sum(2*((i["bar"][2]-i["bar"][0])+(i["bar"][3]-i["bar"][1]))
                             * (GH+(i["levels"]-1)*UH) for i in items)
                hmax = GH + (max(i["levels"] for i in items) - 1) * UH
                fails = []
                if used > AREA: fails.append("C1 ground demand")
                if fp > cfg["max_site_coverage"]*AREA: fails.append("C2 coverage")
                if opn < MIN_OPEN: fails.append("C3 open at grade")
                if hmax > cfg["max_height_m"]: fails.append("C5 height")
                r = {"id": "S4",
                     "note": "Primary over secondary in one shared-structure block, "
                             "separate cores and entrances; kindergarten separate",
                     "bands": 2, "feasible": not fails, "fails": fails,
                     "footprint_m2": round(fp,1), "coverage_pct": round(100*fp/AREA,1),
                     "open_at_grade_m2": round(opn,1),
                     "open_per_student_m2": round(opn/STUD,3),
                     "ground_demand_m2": round(used,1), "spare_m2": round(AREA-used,1),
                     "buildings_east_west": ew, "sum_levels": lv,
                     "facade_per_gfa": round(facade/gfa_all,3), "tallest_m": round(hmax,1),
                     "mean_yard_distance_from_road_m": round(
                         sum(east((i["band"][0]+i["band"][1])/2) - i["yard_cx"]
                             for i in items)/len(items), 1),
                     "min_yard_slack_m2": round(min(
                         i["yard_area"] - sum(DEM[s]["yard_need"] for s in i["_set"])
                         for i in items), 1),
                     "items": [{"school": i["school"], "levels": i["levels"],
                                "bar": [round(v,2) for v in i["bar"]],
                                "plate_m2": round((i["bar"][2]-i["bar"][0])*(i["bar"][3]-i["bar"][1]),1),
                                "yard_m2": round(i["yard_area"],1)} for i in items]}
                key = (r["feasible"], r["open_per_student_m2"], -r["sum_levels"])
                if best is None or key > best[0]: best = (key, r)
    if best: return best[1]
    return {"id": "S4", "note": "Primary over secondary in one shared-structure block, "
            "separate cores and entrances; kindergarten separate",
            "bands": 2, "feasible": False,
            "fails": sorted(WHY)[:2] or ["no arrangement"]}
RESULTS.append(stacked())

RESULTS.sort(key=lambda r: r["id"])
json.dump({"programme": {"variant": prog["programme_variant"],
                         "students": STUD,
                         "classrooms": prog["capacity"]["total_classrooms"]},
           "options": RESULTS},
          open(os.path.join(HERE, "data", "massing_options.json"), "w"), indent=2)

print(f"Massing options — {STUD:,} students, variant '{prog['programme_variant']}', "
      f"min open {MIN_OPEN:,.0f} m2\n")
print(f"{'':<4}{'bands':>6}{'foot':>7}{'cov%':>6}{'open':>7}{'/stud':>7}{'spare':>7}"
      f"{'E-W':>5}{'lv':>4}{'fac/GFA':>9}{'yard<-road':>11}{'shade':>6}{'slack':>7}  result")
for r in RESULTS:
    if not r.get("footprint_m2"):
        print(f"{r['id']:<4}{r['bands']:>6}{'':>7}{'':>6}{'':>7}{'':>7}{'':>7}"
              f"{'':>5}{'':>4}{'':>9}{'':>11}{'':>6}{'':>7}  {'; '.join(r['fails'])}")
        continue
    print(f"{r['id']:<4}{r['bands']:>6}{r['footprint_m2']:>7,.0f}{r['coverage_pct']:>6.1f}"
          f"{r['open_at_grade_m2']:>7,.0f}{r['open_per_student_m2']:>7.2f}{r['spare_m2']:>7,.0f}"
          f"{r['buildings_east_west']:>5}{r['sum_levels']:>4}{r['facade_per_gfa']:>9.3f}"
          f"{r['mean_yard_distance_from_road_m']:>11.1f}"
          f"{r.get('yards_shaded_at_assembly','-'):>6}{r['min_yard_slack_m2']:>7,.0f}  "
          f"{'OK' if r['feasible'] else 'FAIL ' + ', '.join(r['fails'])}")
print("\n" + "\n".join(f"  {r['id']}  {r['note']}" for r in RESULTS))
print("\nwrote data/massing_options.json")
