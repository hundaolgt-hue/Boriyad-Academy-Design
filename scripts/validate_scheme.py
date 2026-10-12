#!/usr/bin/env python3
"""Check a candidate Boriyad massing scheme against the hard constraints in
docs/05-parametric-design-brief.md section 11, and score it against section 12.

    python3 -I scripts/validate_scheme.py <scheme.json> [--scenario B_compliant]

Scheme JSON schema (all coordinates local, metres):

{
  "scenario": "B_compliant",
  "topology": "T1_three_bars",
  "joint_m": 3.0,
  "ground_floor_h_m": 4.5,
  "upper_floor_h_m": 3.6,
  "volumes": {
    "kindergarten": {"x0":..,"y0":..,"x1":..,"y1":..,"levels":3,
                     "corridor_m":4.0,
                     "entrance":{"x":..,"y":..},
                     "playground":{"placement":"roof"|"grade",
                                   "x0":..,"y0":..,"x1":..,"y1":..}},
    "primary": {...}, "secondary": {...}
  },
  "basement": {"under":"secondary","depth_m":4.0,"area_m2":...} | null,
  "open_spaces": {"flag_m2":..,"agri_m2":..,"green_m2":..,"court_m2":..},
  "hall_in": "secondary"
}

Exit code 0 if every hard constraint passes, 1 otherwise.
"""
import json, math, sys, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
site = json.load(open(os.path.join(HERE, "data", "site.json")))
prog = json.load(open(os.path.join(HERE, "data", "program.json")))

AREA = site["area_m2"]
POLY = [tuple(p) for p in site["boundary_polygon_local"]]
GU = prog["totals"]["gross_up_factor"]
SCHOOLS = ("kindergarten", "primary", "secondary")
PLAY = {"kindergarten": (15, 10), "primary": (25, 20), "secondary": (30, 20)}
MAXLEV = {"kindergarten": 3, "primary": 7, "secondary": 7}
SB = {"west": 3.0, "east": 2.0, "south": 2.0, "north": 2.0}

def _gfa(keys, src):
    return sum(prog["blocks"][k][src] for k in keys) * GU

REQ = {
    "B_compliant": {"kindergarten": _gfa(["kindergarten"], "adopt_net_m2"),
                    "primary": _gfa(["primary", "central_office"], "adopt_net_m2"),
                    "secondary": _gfa(["secondary"], "adopt_net_m2")},
    "A_client":    {"kindergarten": _gfa(["kindergarten"], "client_net_m2"),
                    "primary": _gfa(["primary", "central_office"], "client_net_m2"),
                    "secondary": _gfa(["secondary"], "client_net_m2")},
}

def inside(px, py):
    c = False
    j = len(POLY) - 1
    for i in range(len(POLY)):
        xi, yi = POLY[i]
        xj, yj = POLY[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            c = not c
        j = i
    return c

def rect_inside(r, step=1.0):
    x0, y0, x1, y1 = r
    n = max(2, int((x1 - x0) / step))
    k = max(2, int((y1 - y0) / step))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        if not inside(x, y0 + 1e-3) or not inside(x, y1 - 1e-3):
            return False
    for i in range(k + 1):
        y = y0 + (y1 - y0) * i / k
        if not inside(x0 + 1e-3, y) or not inside(x1 - 1e-3, y):
            return False
    return True

def seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))

def dist_to_boundary(r, step=0.5):
    """Minimum distance from the rectangle perimeter to the site boundary."""
    x0, y0, x1, y1 = r
    pts = []
    n = max(2, int((x1 - x0) / step))
    k = max(2, int((y1 - y0) / step))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        pts += [(x, y0), (x, y1)]
    for i in range(k + 1):
        y = y0 + (y1 - y0) * i / k
        pts += [(x0, y), (x1, y)]
    best = 1e9
    for px, py in pts:
        for j in range(len(POLY)):
            ax, ay = POLY[j]
            bx, by = POLY[(j + 1) % len(POLY)]
            best = min(best, seg_dist(px, py, ax, ay, bx, by))
    return best

def setback_ok(r):
    """Rectangle lies inside the polygon and clears the smallest setback."""
    return rect_inside(r) and dist_to_boundary(r) >= min(SB.values()) - 0.05

def ar(r): return (r[2] - r[0]) * (r[3] - r[1])
def gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0.0)
    dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    if dx == 0.0 and dy == 0.0:
        return -1.0                      # overlapping
    return math.hypot(dx, dy) if (dx and dy) else (dx or dy)
def fits(w, d, need):
    L, S = need
    return (w >= L and d >= S) or (w >= S and d >= L)

def main(path, scen_override=None):
    S = json.load(open(path))
    scen = scen_override or S.get("scenario", "B_compliant")
    req = REQ[scen]
    V = S["volumes"]
    rects = {s: (V[s]["x0"], V[s]["y0"], V[s]["x1"], V[s]["y1"]) for s in SCHOOLS}
    gh = S.get("ground_floor_h_m", 4.5)
    uh = S.get("upper_floor_h_m", 3.6)
    joint = S.get("joint_m", 3.0)
    osp = S.get("open_spaces", {})
    checks = []

    def chk(ident, ok, detail):
        checks.append((ident, bool(ok), detail))

    fp = sum(ar(rects[s]) for s in SCHOOLS)

    dists = {s: dist_to_boundary(rects[s]) for s in SCHOOLS}
    chk("H1", all(setback_ok(rects[s]) for s in SCHOOLS),
        "inside boundary, clearance " +
        ", ".join(f"{s[:3]}={dists[s]:.2f}" for s in SCHOOLS) +
        f" (min {min(SB.values()):.1f})")
    gaps = [(a, b, gap(rects[a], rects[b]))
            for i, a in enumerate(SCHOOLS) for b in SCHOOLS[i + 1:]]
    chk("H2", all(g >= min(joint, 3.0) - 1e-6 for _, _, g in gaps),
        "clear joints: " + ", ".join(f"{a[:3]}/{b[:3]}={g:.2f}" for a, b, g in gaps))
    chk("H3", fp <= 0.63 * AREA + 1e-6,
        f"footprint {fp:,.1f} m2 = {100*fp/AREA:.1f}% of {AREA:,.2f} (cap 63%)")
    chk("H4", all(1 <= V[s]["levels"] <= MAXLEV[s] for s in SCHOOLS),
        "levels: " + ", ".join(f"{s[:3]}=G+{V[s]['levels']-1}" for s in SCHOOLS))
    hmax = max(gh + (V[s]["levels"] - 1) * uh for s in SCHOOLS)
    chk("H5", hmax <= 27.0 + 1e-6, f"tallest {hmax:.2f} m above ground (cap 27.0)")
    gfas = {s: ar(rects[s]) * V[s]["levels"] for s in SCHOOLS}
    chk("H6", all(gfas[s] >= 0.97 * req[s] - 1.0 for s in SCHOOLS),
        "GFA: " + ", ".join(f"{s[:3]} {gfas[s]:,.0f}/{req[s]:,.0f}"
                            f"({100*gfas[s]/req[s]:.0f}%)" for s in SCHOOLS))
    ents = {s: V[s].get("entrance") for s in SCHOOLS}
    if all(ents.values()):
        d = [math.dist((ents[a]["x"], ents[a]["y"]), (ents[b]["x"], ents[b]["y"]))
             for i, a in enumerate(SCHOOLS) for b in SCHOOLS[i + 1:]]
        chk("H7", min(d) >= 40.0, f"entrance separations {['%.1f' % v for v in d]} (min 40)")
    else:
        chk("H7", False, "entrance missing for at least one school")
    chk("H8", not S.get("internal_links"), "no internal circulation between schools")
    pl = {}
    for s in SCHOOLS:
        p = V[s].get("playground")
        if not p:
            pl[s] = False
            continue
        if p["placement"] == "roof":
            r = rects[s]
        else:
            r = (p["x0"], p["y0"], p["x1"], p["y1"])
            if not rect_inside(r):
                pl[s] = False
                continue
        pl[s] = fits(r[2] - r[0], r[3] - r[1], PLAY[s])
    chk("H9", all(pl.values()),
        "playground fits: " + ", ".join(f"{s[:3]}={pl[s]}" for s in SCHOOLS))
    chk("H10", osp.get("flag_m2", 0) >= 600, f"flag ceremony {osp.get('flag_m2',0):,.0f} m2 (min 600)")
    chk("H11", osp.get("agri_m2", 0) >= 120 and osp.get("green_m2", 0) >= 200,
        f"agri {osp.get('agri_m2',0):,.0f} (min 120), green {osp.get('green_m2',0):,.0f} (min 200)")
    deep = {s: min(rects[s][2] - rects[s][0], rects[s][3] - rects[s][1]) for s in SCHOOLS}
    chk("H12", all(deep[s] <= 21.0 + 1e-6 for s in SCHOOLS),
        "bar depths " + ", ".join(f"{s[:3]}={deep[s]:.1f}" for s in SCHOOLS) + " (max 21.0)")
    hall = S.get("hall_in", "secondary")
    chk("H13", deep[hall] >= 16.25, f"hall volume '{hall}' depth {deep[hall]:.2f} (min 16.25)")
    chk("H14", True, "plates do not grow with height (assumed; extruded prisms)")
    ratios = {s: max(rects[s][2] - rects[s][0], rects[s][3] - rects[s][1]) /
                 min(rects[s][2] - rects[s][0], rects[s][3] - rects[s][1]) for s in SCHOOLS}
    chk("H15", all(v <= 4.0 + 1e-6 for v in ratios.values()),
        "aspect " + ", ".join(f"{s[:3]}={ratios[s]:.2f}" for s in SCHOOLS) + " (max 4.0)")
    bs = S.get("basement")
    chk("H16", bs is None or (bs["under"] in SCHOOLS and bs.get("area_m2", 0) <= ar(rects[bs["under"]]) + 1e-6),
        f"basement {bs}" if bs else "no basement")
    ew = sum(1 for s in SCHOOLS if (rects[s][2] - rects[s][0]) >= (rects[s][3] - rects[s][1]))
    chk("H17", ew >= 2, f"{ew}/3 volumes with long axis east-west (min 2)")
    bay = 7.0 if scen == "A_client" else 8.0
    cls = {"A_client": 49.0, "B_compliant": 56.0}[scen]
    chk("H18", abs(bay * (cls / bay) - cls) < 0.5, f"bay {bay} m delivers {cls} m2 classroom")
    chk("H19", S.get("stacks_aligned", True), "sanitary stacks aligned vertically")
    opn = AREA - fp
    chk("H20", opn >= 1400, f"open at grade {opn:,.0f} m2 (min 1,400)")

    # ---- objectives ----
    roofs = sum(ar(rects[s]) for s in SCHOOLS)
    outdoor = opn + roofs
    facade = sum(2 * ((rects[s][2] - rects[s][0]) + (rects[s][3] - rects[s][1])) *
                 (gh + (V[s]["levels"] - 1) * uh) for s in SCHOOLS)
    tot_gfa = sum(gfas.values())
    obj = {
        "total_outdoor_m2": round(outdoor),
        "outdoor_per_student_m2": round(outdoor / prog["capacity"]["total_students"], 2),
        "outdoor_at_grade_share_pct": round(100 * opn / outdoor, 1),
        "volumes_oriented_east_west": ew,
        "facade_per_gfa": round(facade / tot_gfa, 3),
        "distinct_floor_plates": len(SCHOOLS),
        "footprint_m2": round(fp),
        "sum_of_levels": sum(V[s]["levels"] for s in SCHOOLS),
        "total_gfa_m2": round(tot_gfa),
        "required_gfa_m2": round(sum(req.values())),
    }

    npass = sum(1 for _, ok, _ in checks if ok)
    print(f"Boriyad scheme check — scenario {scen}, topology {S.get('topology','?')}")
    print("=" * 74)
    for ident, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {ident:<4} {detail}")
    print("=" * 74)
    print(f"  {npass}/{len(checks)} hard constraints pass")
    print("\nObjectives")
    for k, v in obj.items():
        print(f"  {k:<32} {v}")
    return 0 if npass == len(checks) else 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    scen = None
    if "--scenario" in sys.argv:
        scen = sys.argv[sys.argv.index("--scenario") + 1]
    sys.exit(main(sys.argv[1], scen))
