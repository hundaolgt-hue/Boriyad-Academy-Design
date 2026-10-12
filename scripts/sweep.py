#!/usr/bin/env python3
"""Prove the model responds to its inputs. Runs the full chain for a set of
scenarios and reports capacity, footprint, open ground and feasibility."""
import json, subprocess, sys, os, copy
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE=json.load(open(os.path.join(HERE,"data","config.json")))
SCEN=[
 ("as issued", {}),
 ("3,600 students", {"enrolment":{"kindergarten":600,"primary":2000,"secondary":1000}}),
 ("2,400 students", {"enrolment":{"kindergarten":450,"primary":1400,"secondary":550}}),
 ("compliant schedule", {"programme_variant":"compliant"}),
 ("compliant + 20x20 secondary pitch", {"programme_variant":"compliant",
                                        "playing_ground_m2":{"kindergarten":150,"primary":500,"secondary":400},
                                        "playing_ground_min_rect_m":{"kindergarten":[15,10],"primary":[25,20],"secondary":[20,20]}}),
 ("design standing rates", {"standing_rate_m2_per_student":{"kindergarten":0.58,"primary":0.58,"secondary":0.73}}),
 ("assembly NOT overlapped", {"overlap_assembly_with_pitch": False}),
 ("open ground >= 1.20 m2/student", {"min_open_at_grade_per_student_m2":1.20}),
 ("central office in primary", {"central_office_with":"primary"}),
 ("no unit consolidation", {"consolidate_registered_units": False}),
]
def deep(a,b):
    out=copy.deepcopy(a)
    for k,v in b.items():
        out[k]=dict(out.get(k,{}),**v) if isinstance(v,dict) and isinstance(out.get(k),dict) else v
    return out
print(f"{'scenario':<36}{'students':>9}{'class':>7}{'GFA':>8}{'foot':>7}{'cov%':>6}"
      f"{'open':>7}{'/stud':>7}{'levels KPS':>12}  result")
tmp=os.path.join(HERE,"data","_sweep_config.json")
for name,delta in SCEN:
    json.dump(deep(BASE,delta),open(tmp,"w"),indent=2)
    subprocess.run([sys.executable,"-I",os.path.join(HERE,"scripts","program_model.py"),tmp],
                   cwd=HERE,capture_output=True)
    r=subprocess.run([sys.executable,"-I",os.path.join(HERE,"scripts","campus_model.py")],
                     cwd=HERE,capture_output=True,text=True)
    sol=json.load(open(os.path.join(HERE,"data","campus_solution.json")))
    t=sol["totals"]; c=sol["capacity"]; d=sol["demand"]
    lv="/".join(f"{d[s]['levels']-1}" for s in ("kindergarten","primary","secondary"))
    bad=[k["id"] for k in sol["checks"] if not k["pass"]]
    print(f"{name:<36}{c['total_students']:>9,}{c['total_classrooms']:>7}{t['gfa_m2']:>8,.0f}"
          f"{t['footprint_m2']:>7,.0f}{t['coverage_pct']:>6.1f}{t['open_at_grade_m2']:>7,.0f}"
          f"{t['open_at_grade_per_student_m2']:>7.2f}{'G+'+lv:>12}  "
          f"{'OK' if sol['feasible'] else 'FAIL '+','.join(bad)}")
os.remove(tmp)
# restore
subprocess.run([sys.executable,"-I",os.path.join(HERE,"scripts","program_model.py")],cwd=HERE,capture_output=True)
subprocess.run([sys.executable,"-I",os.path.join(HERE,"scripts","campus_model.py")],cwd=HERE,capture_output=True)
print("\nbaseline restored")
