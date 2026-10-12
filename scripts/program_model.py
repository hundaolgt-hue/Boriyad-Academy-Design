#!/usr/bin/env python3
"""Resolve data/program_rules.json into a schedule of accommodation for any
enrolment, then into gross floor area per school.

    python3 -I scripts/program_model.py [config.json]

With no argument it uses data/config.json. Writes data/program_resolved.json.

The whole chain is:

    enrolment -> classrooms -> teaching area
              -> registered units -> ancillary area
              -> net area -> gross floor area

Nothing downstream is hard-coded to a particular student number.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHOOLS = ("kindergarten", "primary", "secondary")

DEFAULT_CONFIG = {
    "enrolment": {"kindergarten": 540, "primary": 1750, "secondary": 640},
    "programme_variant": "client",          # "client" | "compliant"
    "class_size_override": {},              # e.g. {"primary": 45}
    "classroom_area_override": {},          # e.g. {"primary": 56}
    "consolidate_registered_units": True,   # Art. 15 position
    "gross_up_factor": None,                # None = use the rule set's 1.40
    "central_office_with": "gate_pavilion", # "gate_pavilion" | "primary" | ...
}

def load_config(path=None):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    p = path or os.path.join(HERE, "data", "config.json")
    if os.path.exists(p):
        user = json.load(open(p))
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg

def count_for(rule, ctx):
    """Resolve a count rule to an integer quantity."""
    n = rule.get("n", 1)
    per = rule["per"]
    if per == "school":
        return n
    if per == "classroom":
        return n * ctx["classrooms"]
    if per == "classrooms":
        return n * math.ceil(ctx["classrooms"] / rule["each"])
    if per == "students":
        return n * math.ceil(ctx["students"] / rule["each"])
    if per == "unit":
        u = 1 if ctx["consolidate"] and rule.get("_consolidates", True) else ctx["units"]
        return n * u
    if per == "pits":
        return n * ctx["sanitary_blocks"]
    raise ValueError("unknown count rule: " + per)

def resolve(cfg, rules=None):
    rules = rules or json.load(open(os.path.join(HERE, "data", "program_rules.json")))
    variant = cfg["programme_variant"]
    gu = cfg.get("gross_up_factor") or rules["gross_up_factor"]
    san = rules["sanitary"]
    out = {"config": cfg, "programme_variant": variant, "gross_up_factor": gu,
           "blocks": {}, "capacity": {}}

    for s in SCHOOLS:
        students = cfg["enrolment"][s]
        csize = cfg["class_size_override"].get(s, rules["class_size"][s])
        classrooms = math.ceil(students / csize) if students else 0
        units = math.ceil(students / rules["registered_unit_size"][s]) if students else 0
        pits = math.ceil(students / san["students_per_pit"]) if students else 0
        blocks = math.ceil(pits / san["pits_per_block"]) if pits else 0
        ctx = {"students": students, "classrooms": classrooms, "units": units,
               "sanitary_blocks": blocks, "consolidate": cfg["consolidate_registered_units"]}
        rows, net = [], 0.0
        for r in rules["blocks"][s]:
            rule = dict(r["count"])
            rule["_consolidates"] = r.get("consolidates", True)
            area = r["area_m2"][variant]
            if r["key"] in cfg["classroom_area_override"] or \
               (r["key"] == "classroom" and s in cfg["classroom_area_override"]):
                area = cfg["classroom_area_override"].get(s, area)
            qty = count_for(rule, ctx) if area else 0
            tot = area * qty
            net += tot
            rows.append({"key": r["key"], "label": r["label"], "article": r["article"],
                         "unit_area_m2": area, "count": qty, "total_m2": round(tot, 2),
                         "rule": r["count"], "note": r.get("note", "")})
        out["blocks"][s] = {"rooms": rows, "net_m2": round(net, 2),
                            "gfa_m2": round(net * gu, 1)}
        out["capacity"][s] = {"students": students, "class_size": csize,
                              "classrooms": classrooms, "registered_units": units,
                              "sanitary_pits": pits, "sanitary_blocks": blocks,
                              "m2_per_student_in_class": round(
                                  (cfg["classroom_area_override"].get(s)
                                   or rules["blocks"][s][0]["area_m2"][variant]) / csize, 2)}

    # central office — a group function, not a school
    ctx = {"students": sum(cfg["enrolment"].values()), "classrooms": 0, "units": 1,
           "sanitary_blocks": 1, "consolidate": True}
    rows, net = [], 0.0
    for r in rules["blocks"]["central_office"]:
        rule = dict(r["count"]); rule["_consolidates"] = True
        area = r["area_m2"][variant]
        qty = count_for(rule, ctx) if area else 0
        net += area * qty
        rows.append({"key": r["key"], "label": r["label"], "article": r["article"],
                     "unit_area_m2": area, "count": qty, "total_m2": round(area * qty, 2)})
    out["blocks"]["central_office"] = {"rooms": rows, "net_m2": round(net, 2),
                                       "gfa_m2": round(net * gu, 1),
                                       "located_with": cfg["central_office_with"]}

    tot_students = sum(cfg["enrolment"].values())
    tot_classes = sum(out["capacity"][s]["classrooms"] for s in SCHOOLS)
    out["capacity"]["total_students"] = tot_students
    out["capacity"]["total_classrooms"] = tot_classes
    out["totals"] = {
        "net_m2": round(sum(out["blocks"][b]["net_m2"] for b in out["blocks"]), 1),
        "gfa_m2": round(sum(out["blocks"][b]["gfa_m2"] for b in out["blocks"]), 1),
        "net_per_student_m2": round(
            sum(out["blocks"][b]["net_m2"] for b in out["blocks"]) / tot_students, 2),
        "gfa_per_student_m2": round(
            sum(out["blocks"][b]["gfa_m2"] for b in out["blocks"]) / tot_students, 2),
    }
    # the school each compound must build: its own GFA plus any central office
    out["compound_gfa_m2"] = {s: out["blocks"][s]["gfa_m2"] for s in SCHOOLS}
    co = cfg["central_office_with"]
    if co in SCHOOLS:
        out["compound_gfa_m2"][co] += out["blocks"]["central_office"]["gfa_m2"]
        out["central_office_standalone_m2"] = 0.0
    else:
        out["central_office_standalone_m2"] = out["blocks"]["central_office"]["gfa_m2"]
    return out

if __name__ == "__main__":
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
    r = resolve(cfg)
    json.dump(r, open(os.path.join(HERE, "data", "program_resolved.json"), "w"), indent=2)
    print(f"variant: {r['programme_variant']}   gross-up {r['gross_up_factor']}   "
          f"consolidate units: {cfg['consolidate_registered_units']}\n")
    print(f"{'school':<16}{'students':>9}{'classes':>9}{'units':>7}{'pits':>6}"
          f"{'net m2':>10}{'GFA m2':>10}")
    for s in SCHOOLS:
        c = r["capacity"][s]; b = r["blocks"][s]
        print(f"{s:<16}{c['students']:>9,}{c['classrooms']:>9}{c['registered_units']:>7}"
              f"{c['sanitary_pits']:>6}{b['net_m2']:>10,.0f}{b['gfa_m2']:>10,.0f}")
    co = r["blocks"]["central_office"]
    print(f"{'central office':<16}{'-':>9}{'-':>9}{'-':>7}{'-':>6}"
          f"{co['net_m2']:>10,.0f}{co['gfa_m2']:>10,.0f}   with: {co['located_with']}")
    t = r["totals"]
    print(f"{'TOTAL':<16}{r['capacity']['total_students']:>9,}"
          f"{r['capacity']['total_classrooms']:>9}{'':>7}{'':>6}"
          f"{t['net_m2']:>10,.0f}{t['gfa_m2']:>10,.0f}")
    print(f"\nper student: {t['net_per_student_m2']} m2 net, {t['gfa_per_student_m2']} m2 gross")
    print("classroom density: " + ", ".join(
        f"{s[:3]} {r['capacity'][s]['m2_per_student_in_class']}" for s in SCHOOLS) + " m2/student")
