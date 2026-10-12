# Boriyad Youth Academy — Design Development

New multi-cycle KG / Primary / Secondary campus, Ashewa Meda, Oromia.
69 classrooms, ~2,930 students, 4,618.05 m² (surveyed), G+6.

Governing standard: *Qajeelfama Istaandaardii Manneen Barnootaa Oromiyaa,
Lakk. 04/2016* (Oromia Education Bureau).

## Documents

| File | Phase | What it is |
|---|---|---|
| `docs/01-massing-study.md` | 1 | First massing study. §§1–3 current; §§0, 4–6 superseded. |
| `docs/02-ground-and-survey-review.md` | 1 | Survey geometry and a review of the NATM geotechnical report, with a query sheet |
| `docs/03-massing-study-r2.md` | 1 | Massing after the survey. §§1–3 current; §4 superseded. |
| `docs/04-massing-study-r3.md` | 1 | Massing after the separation requirement — three schools, three gates |
| **`docs/05-parametric-design-brief.md`** | 1 | **Current.** Self-contained brief for an agent building the parametric model in Rhino |
| `docs/massing-study.html` | 1 | Illustrated massing study with site plans drawn from the survey |

## Data (machine-readable)

| File | Contents |
|---|---|
| `data/site.json` | survey coordinates, boundary functions, orientation, climate, ground, services |
| `data/program.json` | reconciled schedule of accommodation, room by room, with article citations |
| `data/seed_layouts.json` | validated seed layouts, 2 topologies × 2 programme scenarios |
| `data/constraints.json` | hard constraints, objectives and parameters |
| `data/scheme_T1_B.json` | worked example scheme, passes 20/20 hard constraints |

## Scripts

```
python3 -I scripts/build_program.py              # rebuild data/program.json
python3 -I scripts/build_site.py                 # rebuild data/site.json
python3 -I scripts/solve_massing.py              # rebuild data/seed_layouts.json
python3 -I scripts/validate_scheme.py <scheme.json>
```

## Live issues

1. **Scenario A (the client programme as issued) will not pass licensing.**
   It is 68% below the guideline-compliant schedule — see brief §6.5. The
   primary toilet provision alone is one WC per 175 students against a required
   one per 25.
2. Which boundary is the Ambo Road, and is there a usable northern frontage?
   Both affect the three gates.
3. Road reservation setbacks are unquantified on every frontage.
4. The NATM boreholes lie 36–84 m south of the surveyed polygon and are for a
   different client. Four new holes to 15 m inside the site are required.
5. Confirm the kindergarten at three levels, and whether enrolment is 2,930
   (this programme) or 3,600 (Design Brief 01).
