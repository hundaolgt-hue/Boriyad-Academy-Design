#!/usr/bin/env python3
"""Standing area per student by age for the Art. 7(2) flag ceremony, and the
resulting at-grade site budget for three separated compounds.

Method: lateral pitch = p95 shoulder breadth + lateral gap
        rank pitch    = p95 body depth     + rank gap
        net area      = lateral x rank
        gross area    = net x circulation factor + fixed frontage
The circulation factor covers aisles between class blocks and staff positions;
the fixed frontage is the flag mast, podium and staff line.
"""
COHORT = [
    # label, age, students, shoulder_p95, depth_p95, lat_gap, rank_gap, gross_f, fixed
    ("Kindergarten (Pre-KG/KG/Prep)", "4-6",   540, 0.28, 0.17, 0.22, 0.53, 1.50, 30),
    ("Primary lower, G1-4",           "7-10",  875, 0.32, 0.19, 0.23, 0.51, 1.30, 0),
    ("Primary upper, G5-8",           "11-14", 875, 0.38, 0.22, 0.22, 0.53, 1.30, 60),
    ("Secondary, G9-12",              "15-18", 640, 0.46, 0.26, 0.19, 0.54, 1.25, 50),
]
DENSE = 0.62   # multiplier for the "as actually practised" packed formation

print("STANDING AREA PER STUDENT — flag ceremony formation\n")
print(f"{'cohort':<32}{'age':>7}{'lat':>7}{'rank':>7}{'net':>8}{'design':>9}{'dense':>8}")
print(f"{'':<32}{'':>7}{'m':>7}{'m':>7}{'m2/st':>8}{'m2/st':>9}{'m2/st':>8}")
tot = {}
for lbl, age, n, sh, dp, lg, rg, gf, fx in COHORT:
    lat, rank = sh + lg, dp + rg
    net = lat * rank
    gross = (net * gf * n + fx) / n
    print(f"{lbl:<32}{age:>7}{lat:>7.2f}{rank:>7.2f}{net:>8.3f}{gross:>9.2f}{gross*DENSE:>8.2f}")
    key = "primary" if "Primary" in lbl else ("kindergarten" if "Kinder" in lbl else "secondary")
    a = tot.setdefault(key, [0, 0.0, 0.0])
    a[0] += n; a[1] += net * gf * n + fx; a[2] += (net * gf * n + fx) * DENSE

print("\n\nASSEMBLY AREA REQUIRED, per school, at grade\n")
print(f"{'school':<16}{'students':>10}{'design m2':>12}{'m2/st':>8}{'dense m2':>11}{'m2/st':>8}")
for k in ("kindergarten", "primary", "secondary"):
    n, d, dn = tot[k]
    print(f"{k:<16}{n:>10,}{d:>12,.0f}{d/n:>8.2f}{dn:>11,.0f}{dn/n:>8.2f}")
D = sum(v[1] for v in tot.values()); N = sum(v[2] for v in tot.values())
print(f"{'TOTAL':<16}{sum(v[0] for v in tot.values()):>10,}{D:>12,.0f}{'':>8}{N:>11,.0f}")

PITCH = {"kindergarten": 150, "primary": 500, "secondary": 600}   # client's own figures
print("\n\nAT-GRADE DEMAND — can the flag area and the hard pitch be the same surface?\n")
for mode, combine in (("SHARED surface (assembly = pitch, used at different times)", True),
                      ("SEPARATE surfaces", False)):
    print(f"  {mode}")
    for rate, lbl in ((1.0, "design"), (DENSE, "dense")):
        t = 0
        parts = []
        for k in ("kindergarten", "primary", "secondary"):
            a = tot[k][1] * rate
            v = max(a, PITCH[k]) if combine else a + PITCH[k]
            parts.append(f"{k[:3].upper()} {v:,.0f}")
            t += v
        print(f"     {lbl:<7} {'  '.join(parts):<40} total {t:>6,.0f} m2")
    print()

print("SITE BUDGET AT GRADE\n")
SITE = 4618.05
OTHER = {"three gates and drop-offs": 300, "agricultural plot, Art. 7(4)": 120,
         "greenery and Gaaddisa, Art. 7(5)": 200, "perimeter and fire access": 250}
print(f"  fixed other demands: {sum(OTHER.values())} m2  (" +
      ", ".join(f"{k} {v}" for k, v in OTHER.items()) + ")\n")
print(f"{'footprint scenario':<42}{'open grade':>12}{'spare after shared+other':>26}")
for lbl, fp in (("client programme, current seed", 1842),
                ("reconciled programme, current seed", 2465),
                ("reconciled, pushed to 40% coverage", 1847)):
    opn = SITE - fp
    for rate, rl in ((1.0, "design"), (DENSE, "dense")):
        need = sum(max(tot[k][1] * rate, PITCH[k]) for k in PITCH) + sum(OTHER.values())
        print(f"{lbl + ' [' + rl + ']':<42}{opn:>12,.0f}{opn - need:>26,.0f}")
