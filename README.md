# Boriyad Youth Academy — Design Development

New multi-cycle KG / Primary / Secondary campus, Ashewa Meda, Oromia.
Three separately registered schools in three separate compounds on 4,618.05 m².

Governing standard: *Qajeelfama Istaandaardii Manneen Barnootaa Oromiyaa,
Lakk. 04/2016* (Oromia Education Bureau).

## Current deliverable

**`docs/06-rhino-parametric-model.md`** — the specification for the agent
building the Rhino model. Self-contained and fully parametric: change the
enrolment, classroom sizes, standing rates, required open ground or any other
input in `data/config.json`, re-run three scripts, and the whole campus
re-solves.

```
python3 -I scripts/make_rules.py        # only after editing the room rules
python3 -I scripts/program_model.py     # enrolment -> schedule -> GFA
python3 -I scripts/campus_model.py      # GFA + yards -> compounds -> geometry
python3 -I scripts/validate_campus.py   # must exit 0
python3 -I scripts/sweep.py             # shows how the model responds to inputs
```

Baseline: 2,930 students, 69 classrooms, 8,684 m² GFA, footprint 1,885 m²
(40.8%), open at grade 2,733 m² (0.93 m²/student). 6/6 area checks, 12/12
geometric checks.

## Documents

| File | What it is |
|---|---|
| `docs/06-rhino-parametric-model.md` | **Current.** Parametric model specification |
| `docs/05-parametric-design-brief.md` | Superseded by 06 |
| `docs/04-massing-study-r3.md` | How the massing reached three separate schools |
| `docs/03-massing-study-r2.md` | Massing after the survey. §§1–3 current |
| `docs/02-ground-and-survey-review.md` | Survey arithmetic and the NATM report review, with a query sheet |
| `docs/01-massing-study.md` | First massing study. §§1–3 current |
| `docs/massing-study.html` | Illustrated massing study |
| `docs/three-compounds.html` | Illustrated compound planning — yards, plan, budget |

## Data

| File | Contents |
|---|---|
| `data/config.json` | **the single input file** |
| `data/program_rules.json` | room rules with scaling, every room cited to its article |
| `data/site.json` | survey coordinates, boundary functions, orientation, climate, ground |
| `data/program_resolved.json` | the schedule for the current enrolment |
| `data/campus_solution.json` | geometry the Rhino model is built from |

## Decisions outstanding

1. **Which programme.** The guideline-compliant schedule cannot coexist with
   three separated compounds on this site. Blocking.
2. **Which boundary is the Ambo Road**, and is there a usable northern frontage.
3. **Where the central office goes**, given that staff do not intermingle.
4. Road reservation setbacks, unquantified on every frontage.
5. Four boreholes to 15 m inside the site polygon — the NATM report is for
   another parcel.
