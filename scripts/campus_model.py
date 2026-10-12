#!/usr/bin/env python3
"""Solve the Boriyad campus from the resolved programme and data/config.json.

    python3 -I scripts/program_model.py      # first, resolves the schedule
    python3 -I scripts/campus_model.py       # then, solves the campus

Writes data/campus_solution.json — the geometry the Rhino model is built from.

Chain:
    enrolment -> GFA (program_model) -> plate and levels -> territory
    enrolment -> assembly area       -> yard
    territories -> three stacked bands on the surveyed boundary
    open at grade is BOTH an output and a constraint

Rules enforced (see docs/06-rhino-parametric-model.md):
  three compounds, nothing shared outdoors, one gate each
  assembly at grade, separate per school, simultaneous
  primary and secondary may share structure; the kindergarten may not
  minimum plate so no school becomes a point block
  sizing minimises footprint, not storeys
"""
import json, math, os, sys, itertools

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHOOLS = ("kindergarten", "primary", "secondary")

site = json.load(open(os.path.join(HERE, "data", "site.json")))
prog = json.load(open(os.path.join(HERE, "data", "program_resolved.json")))
cfg = prog["config"]
AREA = site["area_m2"]

# ---- site boundary, piecewise linear, local coordinates -------------------
def west(y):  return 41.882 + 0.25783 * (y - 61.305)
def east(y):  return 109.918 + 0.030569 * (y - 49.453)
def south(x): return 49.453 + 0.174196 * (109.918 - x)
def north(x): return 127.622 + 0.158867 * (x - 58.980) if x < 66.779 \
              else 128.861 + 0.110606 * (x - 66.779)
Y_LO, Y_HI = 61.305, 127.622
SB = cfg["setback_m"]

def band(y0, y1):
    """(x_west, x_east) of the widest axis-aligned rectangle between y0 and y1."""
    if y1 <= y0 or y1 > Y_HI:
        return None
    x0 = west(y1) + SB["west"]
    x1 = east(y0) - SB["east"]
    if y0 < Y_LO:
        x0 = max(x0, 109.918 - (y0 - 49.453) / 0.174196 + SB["west"])
    if y0 < south(x0) + SB["south"] or y1 > north(x0) - SB["north"]:
        return None
    return (x0, x1)

def band_area(a, b):
    """Area of the site between two y values (exact for 61.305 <= y <= 127.622)."""
    a, b = max(a, Y_LO), min(b, Y_HI)
    if b <= a:
        return 0.0
    return 82.330 * (b - a) - 0.11363 * (b * b - a * a)

# effective buildable limits after setbacks: the raw boundary corners are
# unusable because the north and south edges run diagonally
Y_TOP = Y_HI
while Y_TOP > Y_LO and band(Y_TOP - 17.0, Y_TOP) is None:
    Y_TOP -= 0.25
Y_BOT = Y_LO
while Y_BOT < Y_TOP and band(Y_BOT, Y_BOT + 17.0) is None:
    Y_BOT += 0.25

# ---- demand per compound --------------------------------------------------
def solve_plate(school, gfa):
    """Fewest-footprint (levels, plate) meeting the GFA, respecting the level
       cap and the minimum-plate floor. Objective is min footprint, not min
       storeys — open ground is scarcer than storeys on this site."""
    best = None
    for n in range(1, cfg["max_levels"][school] + 1):
        f = max(gfa / n, cfg["min_plate_m2"][school])
        if best is None or f < best[1] - 1e-9:
            best = (n, f)
    return best

demand = {}
for s in SCHOOLS:
    students = cfg["enrolment"][s]
    assembly = students * cfg["standing_rate_m2_per_student"][s]
    pitch = cfg["playing_ground_m2"][s]
    yard = max(assembly, pitch) if cfg["overlap_assembly_with_pitch"] else assembly + pitch
    gfa = prog["compound_gfa_m2"][s]
    levels, plate = solve_plate(s, gfa)
    gate = cfg["gate_and_dropoff_m2"][s]
    circ = yard * cfg.get("yard_circulation_factor", 0.15)
    demand[s] = {"students": students, "gfa_m2": round(gfa, 1),
                 "levels": levels, "plate_m2": round(plate, 1),
                 "assembly_m2": round(assembly, 1), "pitch_m2": pitch,
                 "yard_m2": round(yard, 1), "yard_circulation_m2": round(circ, 1),
                 "gate_m2": gate,
                 # the band must hold the building, the yard and the paths round
                 # it; the gate and drop-off sit at the site edge, in the wedges
                 "band_demand_m2": round(plate + yard + circ, 1),
                 "territory_m2": round(plate + yard + circ + gate, 1)}

pavilion = prog.get("central_office_standalone_m2", 0.0)
pavilion_fp = 0.0
if pavilion > 0:
    pavilion_fp = max(pavilion / 2.0, 0.0)          # a two-storey gate pavilion
    pavilion_fp = max(pavilion_fp, 0.0)

footprint = sum(d["plate_m2"] for d in demand.values()) + pavilion_fp
yards = sum(d["yard_m2"] for d in demand.values())
gates = sum(d["gate_m2"] for d in demand.values())
perim = cfg["perimeter_and_fire_m2"]
pav_ground = cfg["gate_pavilion_m2"] if pavilion > 0 else 0
used = footprint + yards + gates + perim + (pav_ground - pavilion_fp if pavilion > 0 else 0)
open_grade = AREA - footprint
min_open = max(cfg.get("min_open_at_grade_m2", 0),
               cfg.get("min_open_at_grade_per_student_m2", 0) *
               prog["capacity"]["total_students"])

checks = []
def chk(i, ok, d): checks.append((i, bool(ok), d))
chk("C1", used <= AREA, f"ground demand {used:,.0f} m2 against site {AREA:,.0f}  "
                        f"-> {AREA-used:+,.0f} m2")
chk("C2", footprint <= cfg["max_site_coverage"] * AREA,
    f"coverage {100*footprint/AREA:.1f}% (cap {100*cfg['max_site_coverage']:.0f}%)")
chk("C3", open_grade >= min_open,
    f"open at grade {open_grade:,.0f} m2, required {min_open:,.0f} "
    f"({open_grade/prog['capacity']['total_students']:.2f} m2/student)")
chk("C4", all(d["levels"] <= cfg["max_levels"][s] for s, d in demand.items()),
    "levels: " + ", ".join(f"{s[:3]} G+{d['levels']-1}" for s, d in demand.items()))
hmax = cfg["ground_floor_h_m"] + (max(d["levels"] for d in demand.values()) - 1) * cfg["upper_floor_h_m"]
chk("C5", hmax <= cfg["max_height_m"], f"tallest {hmax:.1f} m (cap {cfg['max_height_m']})")

# ---- geometry: three stacked bands ---------------------------------------
KGJ = cfg["separation"]["kg_joint_m"]
PSJ = cfg["separation"]["shared_structure_joint_m"] \
      if cfg["separation"]["primary_secondary_may_share_structure"] else KGJ
MAXD = cfg["max_bar_depth_m"]
MINL = cfg["min_bar_length_m"]

best = None
for order in itertools.permutations(SCHOOLS):
    joints = [KGJ if "kindergarten" in (order[i], order[i + 1]) else PSJ for i in range(2)]
    for ystart in [Y_BOT + v / 4 for v in range(0, 9)]:
      for d1 in [v / 4 for v in range(68, 129)]:
        for d2 in [v / 4 for v in range(68, 129)]:
            d3 = Y_TOP - ystart - d1 - d2 - sum(joints)
            if not 17 <= d3 <= 32:
                continue
            ys = [(ystart, ystart + d1),
                  (ystart + d1 + joints[0], ystart + d1 + joints[0] + d2),
                  (Y_TOP - d3, Y_TOP)]
            rows, ok = [], True
            for i, s in enumerate(order):
                a, b = ys[i]
                bx = band(a, b)
                if bx is None:
                    ok = False; break
                A = band_area(a, b)
                if A < demand[s]["band_demand_m2"]:
                    ok = False; break
                # Choose the bar depth so that the bar is a sensible building AND
                # the strip left west of it is a usable yard: big enough by area,
                # and able to hold the playing-ground rectangle either way round.
                pr = cfg["playing_ground_min_rect_m"][s]
                need_yard = demand[s]["yard_m2"] + demand[s]["yard_circulation_m2"]
                cand = None
                dd = min(MAXD, b - a)
                while dd >= 14.0:
                    LL = demand[s]["plate_m2"] / dd
                    yw = (bx[1] - LL) - bx[0] - 3.0          # 3 m path along the building
                    yd = b - a
                    fits_rect = (yw >= pr[0] and yd >= pr[1]) or (yw >= pr[1] and yd >= pr[0]) \
                                if cfg.get("enforce_playing_ground_rect", True) else True
                    # yard AREA is the whole band minus the building, including
                    # the tapered sliver to the west; only the playing-ground
                    # RECTANGLE has to sit in the clean strip beside the building
                    yard_area = A - demand[s]["plate_m2"]
                    if MINL <= LL and yard_area >= need_yard and fits_rect:
                        cand = (dd, LL, yw, yard_area); break
                    dd -= 0.5
                if cand is None:
                    ok = False; break
                d, L, yard_w, yard_a = cand
                rows.append({"school": s, "band_y0": round(a, 2), "band_y1": round(b, 2),
                             "band_area_m2": round(A, 1),
                             "bar": {"x0": round(bx[1] - L, 2), "y0": round(b - d, 2),
                                     "x1": round(bx[1], 2), "y1": round(b, 2)},
                             "bar_length_m": round(L, 2), "bar_depth_m": round(d, 2),
                             "yard_west_limit_x": round(bx[0], 2),
                             "yard": {"x0": round(bx[0], 2), "y0": round(a, 2),
                                      "x1": round(bx[1] - L - 3.0, 2), "y1": round(b, 2),
                                      "width_m": round(yard_w, 2),
                                      "depth_m": round(b - a, 2),
                                      "area_m2": round(yard_a, 1),
                                      "required_m2": round(demand[s]["yard_m2"], 1),
                                      "playing_ground_rect_m": cfg["playing_ground_min_rect_m"][s]},
                             "slack_m2": round(yard_a - demand[s]["yard_m2"]
                                               - demand[s]["yard_circulation_m2"], 1)})
            if not ok:
                continue
            slack = min(r["slack_m2"] for r in rows)
            if best is None or slack > best[0]:
                best = (slack, rows, order)

chk("C6", best is not None, "three stacked compounds fit the boundary"
    if best else "NO ARRANGEMENT — compounds do not fit the boundary")

sol = {"inputs": {k: cfg[k] for k in sorted(cfg) if not k.startswith("_")},
       "capacity": prog["capacity"], "demand": demand,
       "central_office": {"standalone_gfa_m2": round(pavilion, 1),
                          "gate_pavilion_ground_m2": pav_ground,
                          "located_with": cfg["central_office_with"]},
       "totals": {"footprint_m2": round(footprint, 1),
                  "coverage_pct": round(100 * footprint / AREA, 1),
                  "yards_m2": round(yards, 1), "gates_m2": gates,
                  "perimeter_m2": perim,
                  "ground_demand_m2": round(used, 1),
                  "open_at_grade_m2": round(open_grade, 1),
                  "open_at_grade_per_student_m2": round(
                      open_grade / prog["capacity"]["total_students"], 2),
                  "roof_area_m2": round(footprint, 1),
                  "total_outdoor_m2": round(open_grade + footprint, 1),
                  "total_outdoor_per_student_m2": round(
                      (open_grade + footprint) / prog["capacity"]["total_students"], 2),
                  "gfa_m2": round(sum(d["gfa_m2"] for d in demand.values()) + pavilion, 1),
                  "spare_ground_m2": round(AREA - used, 1)},
       "compounds": best[1] if best else None,
       "band_order_south_to_north": list(best[2]) if best else None,
       "checks": [{"id": i, "pass": ok, "detail": d} for i, ok, d in checks],
       "feasible": all(ok for _, ok, _ in checks)}
json.dump(sol, open(os.path.join(HERE, "data", "campus_solution.json"), "w"), indent=2)

print(f"ENROLMENT {prog['capacity']['total_students']:,} students, "
      f"{prog['capacity']['total_classrooms']} classrooms, variant '{prog['programme_variant']}'\n")
print(f"{'compound':<15}{'students':>9}{'GFA':>9}{'levels':>8}{'plate':>8}"
      f"{'assembly':>10}{'pitch':>7}{'yard':>7}{'gate':>6}{'territory':>11}")
for s in SCHOOLS:
    d = demand[s]
    print(f"{s:<15}{d['students']:>9,}{d['gfa_m2']:>9,.0f}{'G+'+str(d['levels']-1):>8}"
          f"{d['plate_m2']:>8,.0f}{d['assembly_m2']:>10,.0f}{d['pitch_m2']:>7,}"
          f"{d['yard_m2']:>7,.0f}{d['gate_m2']:>6}{d['territory_m2']:>11,.0f}")
t = sol["totals"]
print(f"\nfootprint {t['footprint_m2']:,.0f} m2 ({t['coverage_pct']}%)   "
      f"open at grade {t['open_at_grade_m2']:,.0f} m2 "
      f"({t['open_at_grade_per_student_m2']} m2/student)   "
      f"total outdoor {t['total_outdoor_m2']:,.0f} m2 "
      f"({t['total_outdoor_per_student_m2']} m2/student)")
print(f"ground demand {t['ground_demand_m2']:,.0f} against {AREA:,.0f}  "
      f"-> {t['spare_ground_m2']:+,.0f} m2\n")
for i, ok, d in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {i}  {d}")
if best:
    print(f"\nbands south to north, joints "
          f"KG {KGJ} m / primary-secondary {PSJ} m:")
    for r in best[1]:
        b = r["bar"]
        print(f"  {r['school']:<14} y {r['band_y0']:>6.2f}-{r['band_y1']:>6.2f} "
              f"({r['band_area_m2']:>6,.0f} m2)   bar x {b['x0']:>6.2f}-{b['x1']:>6.2f} "
              f"y {b['y0']:>6.2f}-{b['y1']:>6.2f}   {r['bar_length_m']:>5.1f} x "
              f"{r['bar_depth_m']:<4.1f}   slack {r['slack_m2']:>6,.0f}")
print(f"\n{'FEASIBLE' if sol['feasible'] else 'INFEASIBLE'} -> data/campus_solution.json")
sys.exit(0 if sol["feasible"] else 1)
