#!/usr/bin/env python3
"""Independent geometric check of data/campus_solution.json.

campus_model.py asserts the area budget; this verifies the geometry it emitted
and the rules that only a drawing can confirm. Run it on the solver's output,
and again on anything the Rhino agent builds, exported to the same schema.

    python3 -I scripts/validate_campus.py [campus_solution.json]

Exit 0 if every check passes.
"""
import json, math, os, sys, itertools

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
site = json.load(open(os.path.join(HERE, "data", "site.json")))
POLY = [tuple(p) for p in site["boundary_polygon_local"]]
AREA = site["area_m2"]
SCHOOLS = ("kindergarten", "primary", "secondary")

def inside(px, py):
    c, j = False, len(POLY) - 1
    for i in range(len(POLY)):
        xi, yi = POLY[i]; xj, yj = POLY[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            c = not c
        j = i
    return c

def rect_inside(r, step=1.0):
    x0, y0, x1, y1 = r
    n, k = max(2, int((x1 - x0) / step)), max(2, int((y1 - y0) / step))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        if not inside(x, y0 + 1e-3) or not inside(x, y1 - 1e-3): return False
    for i in range(k + 1):
        y = y0 + (y1 - y0) * i / k
        if not inside(x0 + 1e-3, y) or not inside(x1 - 1e-3, y): return False
    return True

def seg_d(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))

def clearance(r, step=0.5):
    x0, y0, x1, y1 = r
    pts = []
    n, k = max(2, int((x1 - x0) / step)), max(2, int((y1 - y0) / step))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n; pts += [(x, y0), (x, y1)]
    for i in range(k + 1):
        y = y0 + (y1 - y0) * i / k; pts += [(x0, y), (x1, y)]
    return min(min(seg_d(px, py, POLY[j][0], POLY[j][1],
                         POLY[(j + 1) % len(POLY)][0], POLY[(j + 1) % len(POLY)][1])
                   for j in range(len(POLY))) for px, py in pts)

def gap(a, b):
    """Clear separation between two axis-aligned rectangles. Zero means they
       touch, which is what a shared-structure joint of 0.0 m means; a negative
       value is a genuine overlap."""
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    if ox > 0 and oy > 0:
        return -min(ox, oy)
    sx, sy = max(-ox, 0.0), max(-oy, 0.0)
    return math.hypot(sx, sy) if (sx and sy) else (sx or sy)

def band_area(a, b):
    """Site area between two y values — the same model the solver uses, so the
       tapered sliver west of a building counts toward its yard."""
    a, b = max(a, 61.305), min(b, 127.622)
    return 0.0 if b <= a else 82.330 * (b - a) - 0.11363 * (b * b - a * a)

def fits(w, d, need):
    L, S = need
    return (w >= L and d >= S) or (w >= S and d >= L)

def main(path):
    sol = json.load(open(path))
    cfg = sol["inputs"]
    if not sol.get("compounds"):
        print("No compound geometry in the solution — nothing to check."); return 1
    comp = {c["school"]: c for c in sol["compounds"]}
    rects = {s: (comp[s]["bar"]["x0"], comp[s]["bar"]["y0"],
                 comp[s]["bar"]["x1"], comp[s]["bar"]["y1"]) for s in SCHOOLS}
    checks = []
    def chk(i, ok, d): checks.append((i, bool(ok), d))

    minsb = min(cfg["setback_m"].values())
    cl = {s: clearance(rects[s]) for s in SCHOOLS}
    chk("G1", all(rect_inside(rects[s]) for s in SCHOOLS) and
              all(cl[s] >= minsb - 0.05 for s in SCHOOLS),
        "buildings inside the boundary, clearance " +
        ", ".join(f"{s[:3]}={cl[s]:.2f}" for s in SCHOOLS) + f" (min {minsb})")

    kgj = cfg["separation"]["kg_joint_m"]
    psj = cfg["separation"]["shared_structure_joint_m"] \
          if cfg["separation"]["primary_secondary_may_share_structure"] else kgj
    gaps, gok = [], True
    for a, b in itertools.combinations(SCHOOLS, 2):
        g = gap(rects[a], rects[b])
        need = kgj if "kindergarten" in (a, b) else psj
        gaps.append(f"{a[:3]}/{b[:3]}={g:.2f}(min {need})")
        if g < need - 0.05: gok = False
    chk("G2", gok, "joints: " + ", ".join(gaps))

    bands = sorted((comp[s]["band_y0"], comp[s]["band_y1"], s) for s in SCHOOLS)
    bok = all(bands[i][1] <= bands[i + 1][0] + 1e-6 for i in range(2))
    chk("G3", bok, "compound bands do not overlap: " +
        " | ".join(f"{s} {a:.1f}-{b:.1f}" for a, b, s in bands))

    yok, yd = True, []
    for s in SCHOOLS:
        c = comp[s]
        w = c["bar"]["x0"] - c["yard_west_limit_x"] - 3.0      # clean strip beside the building
        d = c["band_y1"] - c["band_y0"]
        a = band_area(c["band_y0"], c["band_y1"]) - sol["demand"][s]["plate_m2"]
        need = sol["demand"][s]["yard_m2"] + sol["demand"][s]["yard_circulation_m2"]
        pr = cfg["playing_ground_min_rect_m"][s]
        rect_ok = fits(w, d, pr) if cfg.get("enforce_playing_ground_rect", True) else True
        ok = a >= need - 0.5 and rect_ok
        yd.append(f"{s[:3]} area {a:.0f} (need {need:.0f}), strip {w:.1f}x{d:.1f} "
                  f"vs {pr[0]}x{pr[1]} {'ok' if ok else 'NO'}")
        if not ok: yok = False
    chk("G4", yok, "yards: " + " | ".join(yd))

    fp = sum((r[2] - r[0]) * (r[3] - r[1]) for r in rects.values())
    chk("G5", abs(fp - sum(sol["demand"][s]["plate_m2"] for s in SCHOOLS)) < 25,
        f"drawn footprint {fp:,.0f} m2 against scheduled "
        f"{sum(sol['demand'][s]['plate_m2'] for s in SCHOOLS):,.0f}")
    chk("G6", fp <= cfg["max_site_coverage"] * AREA,
        f"coverage {100*fp/AREA:.1f}% (cap {100*cfg['max_site_coverage']:.0f}%)")
    opn = AREA - fp
    need_open = max(cfg.get("min_open_at_grade_m2", 0),
                    cfg.get("min_open_at_grade_per_student_m2", 0) *
                    sol["capacity"]["total_students"])
    chk("G7", opn >= need_open - 0.5,
        f"open at grade {opn:,.0f} m2 >= {need_open:,.0f} required")
    dep = {s: min(rects[s][2] - rects[s][0], rects[s][3] - rects[s][1]) for s in SCHOOLS}
    chk("G8", all(v <= cfg["max_bar_depth_m"] + 1e-6 for v in dep.values()),
        "bar depths " + ", ".join(f"{s[:3]}={dep[s]:.1f}" for s in SCHOOLS) +
        f" (max {cfg['max_bar_depth_m']})")
    lng = {s: max(rects[s][2] - rects[s][0], rects[s][3] - rects[s][1]) for s in SCHOOLS}
    chk("G9", all(lng[s] >= cfg["min_bar_length_m"] - 1e-6 for s in SCHOOLS),
        "bar lengths " + ", ".join(f"{s[:3]}={lng[s]:.1f}" for s in SCHOOLS) +
        f" (min {cfg['min_bar_length_m']})")
    chk("G10", all(lng[s] / dep[s] <= 4.0 + 1e-6 for s in SCHOOLS),
        "aspect " + ", ".join(f"{s[:3]}={lng[s]/dep[s]:.2f}" for s in SCHOOLS) + " (max 4.0)")
    ew = sum(1 for s in SCHOOLS if (rects[s][2] - rects[s][0]) >= (rects[s][3] - rects[s][1]))
    chk("G11", ew == 3, f"{ew}/3 buildings with their long axis east-west")
    h = cfg["ground_floor_h_m"] + (max(sol["demand"][s]["levels"] for s in SCHOOLS) - 1) \
        * cfg["upper_floor_h_m"]
    chk("G12", h <= cfg["max_height_m"] + 1e-6, f"tallest {h:.2f} m (cap {cfg['max_height_m']})")

    npass = sum(1 for _, ok, _ in checks if ok)
    print(f"Boriyad campus geometry — {sol['capacity']['total_students']:,} students, "
          f"variant '{cfg['programme_variant']}'")
    print("=" * 78)
    for i, ok, d in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {i:<4} {d}")
    print("=" * 78)
    print(f"  {npass}/{len(checks)} geometric checks pass")
    return 0 if npass == len(checks) else 1

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "data", "campus_solution.json")
    sys.exit(main(p))
