# Boriyad Youth Academy — Parametric Model Specification

**For the agent building the Rhino model.**
Version R2 · 12 October 2026 · supersedes `05-parametric-design-brief.md`

Everything is driven from one input file, `data/config.json`. Change the
enrolment, the classroom size, the standing rates, the required open ground at
grade — anything — re-run three scripts, and the whole campus re-solves. No
quantity anywhere is hard-coded to a particular student number.

---

## 0. The chain

```
data/config.json              one input file, every knob
        |
        v
scripts/make_rules.py     ->  data/program_rules.json      room rules, editable
        |
        v
scripts/program_model.py  ->  data/program_resolved.json   schedule for THIS enrolment
        |
        v
scripts/campus_model.py   ->  data/campus_solution.json    geometry + area checks
        |
        v
scripts/validate_campus.py                                 independent geometry check
```

Run order:

```bash
python3 -I scripts/make_rules.py        # only after editing the room rules
python3 -I scripts/program_model.py     # enrolment -> schedule -> GFA
python3 -I scripts/campus_model.py      # GFA + yards -> compounds -> geometry
python3 -I scripts/validate_campus.py   # must exit 0
python3 -I scripts/sweep.py             # shows how the model responds to inputs
```

Standard library only. No dependencies. `campus_model.py` exits non-zero if the
scheme is infeasible, and says which check failed.

**Build the Rhino model from `data/campus_solution.json`, not from this
document.** The numbers quoted here are the current baseline and will move the
moment anyone edits the config.

---

## 1. What is being built

A campus for Boriyad Youth Academy at Ashewa Meda, Oromia, on 4,618.05 m².
**Three separately registered schools, each in its own compound.**

The client's governing instruction, 12 October 2026:

> The three sections must be separated. Students from kindergarten, primary and
> high school cannot intermingle in circulation or on the playground. Staff do
> not intermingle either. Each section has its own flag ceremony area on the
> ground, separately. The sports field can be one big field but separated into
> smaller pitches. Primary and secondary may share structure as long as the
> circulation is separated.

So a **compound** is: one building, one yard, one gate, one drop-off, one set
of cores, stairs, sanitary stacks and staff accommodation. Nothing outdoors is
shared. Primary and secondary may touch structurally; the kindergarten may not.

### 1.1 Current baseline

| | Students | Classrooms | GFA | Levels | Plate | Yard |
|---|---|---|---|---|---|---|
| Kindergarten | 540 | 18 | 2,041 m² | G+2 | 680 m² | 194 m² |
| Primary G1–8 | 1,750 | 35 | 3,886 m² | G+6 | 555 m² | 630 m² |
| Secondary G9–12 | 640 | 16 | 2,458 m² | G+4 | 500 m² | 400 m² |
| Central office | — | — | 298 m² | G+1 | gate pavilion | — |
| **Total** | **2,930** | **69** | **8,684 m²** | | **1,885 m² · 40.8%** | |

Open at grade **2,733 m² · 0.93 m² per student**. Total outdoor including roofs
4,618 m² · 1.58 m² per student. Ground demand 4,110 m² against 4,618 — **508 m²
spare**. All six area checks and all twelve geometric checks pass.

---

## 2. Site

Coordinate reference: **UTM Zone 37N, Adindan datum**, metres.

### 2.1 Model origin — set this first

> Place the Rhino world origin (0, 0, 0) at **E 464 000.000, N 996 700.000**,
> reduced level 0.00 = existing ground.
> **+X = true East, +Y = true North, +Z = up.** Do not rotate the model.

Every coordinate in this document and in `data/*.json` is **local** — survey
value minus that origin. Working in raw survey coordinates costs floating-point
precision in Rhino.

### 2.2 Boundary

| Point | Easting | Northing | Local X | Local Y |
|---|---|---|---|---|
| P1 | 464112.500 | 996833.918 | 112.500 | 133.918 |
| P2 | 464109.918 | 996749.453 | 109.918 | 49.453 |
| P3 | 464041.882 | 996761.305 | 41.882 | 61.305 |
| P4 | 464058.980 | 996827.622 | 58.980 | 127.622 |
| P5 | 464066.779 | 996828.861 | 66.779 | 128.861 |

Closed P1 → P2 → P3 → P4 → P5 → P1. Shoelace area **4,618.05 m²** (Design Brief
01 states 4,621.80; adopt the survey). Extent 70.62 m E–W × 84.47 m N–S.

### 2.3 Boundary as functions — use these, not the polygon, for fitting

```
west  P3–P4 :  x = 41.882  + 0.25783  * (y - 61.305)     61.305 <= y <= 127.622
east  P1–P2 :  x = 109.918 + 0.030569 * (y - 49.453)     49.453 <= y <= 133.918
south P2–P3 :  y = 49.453  + 0.174196 * (109.918 - x)    41.882 <= x <= 109.918
north P4–P5 :  y = 127.622 + 0.158867 * (x - 58.980)     58.980 <= x <=  66.779
north P5–P1 :  y = 128.861 + 0.110606 * (x - 66.779)     66.779 <= x <= 112.500
```

Site width between the east and west edges, exact for 61.305 ≤ y ≤ 127.622:

```
width(y)      = 82.330 - 0.22726 * y
area(a .. b)  = 82.330 * (b - a) - 0.11363 * (b^2 - a^2)
```

A horizontal band from `y0` to `y1` admits an axis-aligned rectangle from
`west(y1)` to `east(y0)` — both boundaries move east as y increases, so the
band's limits are set at opposite ends.

### 2.4 Two facts that govern everything

**The site is cardinally aligned.** East boundary 1.75° off true north–south,
north boundary 6.31° off true east–west. Building parallel to the boundaries
*is* building east–west, so every classroom faces north or south for free.
Design Brief 01 §10.2 assumes a 45° skew and calls for rotation; it predates
the survey and is wrong.

**The buildable strip is 63.8 m deep, not 84.5.** The north and south edges run
diagonally, so the corners are unusable once setbacks apply. The model computes
this at run time:

```
Y_BOT = 62.055     lowest y a 17 m band can start
Y_TOP = 125.872    highest y a 17 m band can reach
```

Those move if the setbacks change. The residual ~580 m² in the north and south
wedges is real ground — gates, drop-offs, landscape — but not orthogonal
building.

### 2.5 Context

| Boundary | Context | Setback |
|---|---|---|
| East | **assumed principal road, Ambo Road corridor — UNCONFIRMED** | 2.0 m |
| South | secondary road, junction at the south-west | 2.0 m |
| North | possible frontage — **UNCONFIRMED** | 2.0 m |
| West | lower-density residential | 3.0 m |

The road reservation is not quantified. Setbacks are parameters; re-run if one
is imposed.

---

## 3. Climate and solar

Latitude 8.97° N, longitude 38.78° E, altitude 2,324 m. Köppen *Weina Dega*.
Mean annual 15.9 °C; dry season 23.3 / 7.3 °C; wet season 21.0 / 10.0 °C;
rainfall 1,089 mm; sunshine 2,439 h.

- Solar noon altitude **65–85°**; the sun passes overhead about 20 April and
  23 August.
- **Late April to late August** the sun is north of zenith, during the kiremt
  rains when radiation is largely diffuse. The other **8.5 months** it is south
  of zenith under clear skies, so the south elevation is the harsher one.
- **East and west are the critical orientations.** Between 07:00–09:00 and
  15:30–18:00 the sun sits at 10–30° altitude. Horizontal shading is useless at
  those angles.
- Overheating design condition is **March–April**, not mid-year.

| Facade | Device | Depth |
|---|---|---|
| North, south | horizontal overhang | 1.2 m |
| East, west | vertical fins or veranda | 2.5–3.0 m |

**Massing consequence:** bars run true east–west. A tall volume on the *north*
side of an open yard throws its shadow away from that yard for 8.5 months, so
height belongs at the north of whatever it overlooks.

Wind: October–May east to north-east, dry and dust-laden — the assumed road
side, so screen it. June–September south-west, rain-driving, so any roof-level
outdoor space needs a canopy to be usable in the rains. Speeds 2–4 m/s.

---

## 4. Ground, structure, seismic

Source: NATM Engineering Plc, October 2024.

> **Caveat.** All six boreholes lie **36–84 m south of this polygon**, the
> report is addressed to a different client and names a different locality. It
> cannot carry foundation design. Treat as indicative regional data; four new
> holes to 15 m inside the site are required. See `02-ground-and-survey-review.md`.

| Layer | Description | Depth |
|---|---|---|
| A | soft to medium stiff dark grey high-plastic silty CLAY — **black cotton** | 0 to 2.0–3.0 m |
| B | stiff to very stiff reddish brown high-plastic silty CLAY with sand and gravel | to 3.5–15.0 m |
| C | weak to moderately weak, highly weathered, fractured vesicular BASALT | below |

Rockhead varies 3.5–15.0 m and deepens northward. **No groundwater to 15 m.**

**Expansive soil is the governing ground condition.** Free swell reaches 130%
with PI 63 at 1.5–2.0 m, and 120% / PI 45 at 2.5–3.0 m — at the report's own
recommended founding depth. Active zone assumed 2.5–4.0 m.

- Found at **−3.0 m** minimum.
- **Basement slab at −4.0 m** clears the active zone, removes the expansive
  material and gives a suspended ground floor by definition. With no
  groundwater there is no dewatering, tanking or uplift case, so the marginal
  cost over the required 3.0 m dig is about one metre.
- **Suspended ground slab everywhere there is no basement.**
- No high-water-demand trees, eucalyptus above all, within 1.5 × mature height
  of any footing. Planting goes in the yards and the wedges.

| | |
|---|---|
| Allowable bearing, design | **275 kPa** at 3.0 m |
| Report's recommendation | 364 kPa — adopts BH-3, not the weakest hole. Do not use |
| Seismic | Zone 3, PGA 0.10 g, Importance Class III, γ<sub>I</sub> = 1.2 → **design 0.12 g** |

The report states I = 1.0, which is wrong for a school.

**Plan regularity matters at 0.12 g.** Keep every volume a plain rectangle, no
re-entrant corners, aspect ratio ≤ 4:1, shear-wall centroid on the mass
centroid. Plates may shrink with height but never grow — every column runs to
foundation, no transfer structure. Primary and secondary may share structure;
the kindergarten is separated by a movement joint.

---

## 5. Regulatory framework

**Qajeelfama Istaandaardii Manneen Barnootaa Oromiyaa, Lakk. 04/2016**, Oromia
Education Bureau. Article 4 applies it to private schools; Article 21
disapplies conflicting guidelines. Binding, not advisory.

| Article | Requirement | How the model satisfies it |
|---|---|---|
| 7(1) | buildings zone | the three compounds |
| 7(2) | flag ceremony area | each compound's yard, at grade, separately |
| 7(3) | sports field | the three pitches, one field divided |
| 7(4) | agricultural plot | ≥ 120 m², may be raised beds on a roof |
| 7(5) | greenery | ≥ 200 m², including the *Gaaddisa* of Art. 2(12) |
| 8.1–8.3 | room areas | `data/program_rules.json`, every room cited |
| 9.1 | highland colour scheme | KG blue beams and columns, grey roof; primary sky blue; secondary blue beams, grey roof, grey columns |
| 11 | class sizes 30 / 50 / 40 | parameters that drive the classroom count |
| 12 | full-day operation | no shift relief |
| 15 | co-located schools keep their own administration | **satisfied outright by three separate buildings** |
| 16.1(1) | no writing on compound walls | no signage geometry on walls |
| 17(1) | five *Golee* corners per KG classroom | pooled as a commons per cluster |

**Waivers assumed granted:** Art. 6(1)–(3) compound areas (1,000 m² KG, 3 ha
primary, 3 ha secondary urban). Full compliance would need over 6 ha. Art. 22
empowers the Bureau to waive. Because the three schools now occupy three
separate buildings, **Art. 15 is satisfied without argument** and the ask
narrows to Art. 6 alone.

---

## 6. How enrolment drives everything

This is the part that makes the model parametric. Every quantity derives from
`enrolment`; nothing is fixed to 2,930 students.

```
classrooms[s]       = ceil(enrolment[s] / class_size[s])
registered_units[s] = ceil(enrolment[s] / registered_unit_size[s])      Art. 11
sanitary_pits[s]    = ceil(enrolment[s] / students_per_pit)             Art. 8.2(13)
sanitary_blocks[s]  = ceil(pits / pits_per_block)

net_area[s]         = SUM over rooms of  unit_area * count(rule)
gfa[s]              = net_area[s] * gross_up_factor

levels[s], plate[s] = argmin plate  subject to  plate >= gfa/levels,
                                                plate >= min_plate[s],
                                                levels <= max_levels[s]

assembly[s]         = enrolment[s] * standing_rate[s]
yard[s]             = max(assembly, pitch)      if overlap_assembly_with_pitch
                    = assembly + pitch          otherwise

band_demand[s]      = plate[s] + yard[s] + yard * yard_circulation_factor
open_at_grade       = site_area - total_footprint
```

### 6.1 Room count rules

Each room in `data/program_rules.json` carries a count rule:

| Rule | Meaning |
|---|---|
| `{"per":"school"}` | one per school, whatever its size |
| `{"per":"classroom"}` | one per classroom |
| `{"per":"classrooms","each":6}` | one per 6 classrooms, rounded up |
| `{"per":"students","each":875}` | one per 875 students, rounded up |
| `{"per":"unit"}` | one per registered unit; collapses to one when `consolidate_registered_units` is true, unless the room sets `"consolidates": false` |
| `{"per":"pits"}` | one per sanitary block |

`"n"` multiplies any of them. **This is where the Art. 15 negotiating position
lives:** directors' offices set `"consolidates": false`, so they duplicate per
registered unit while everything else consolidates. Turning consolidation off
costs 1,196 m² of GFA and makes the scheme infeasible — the model shows it.

**Sanitary provision is computed, never taken from the client document.** The
client programme allows 20 m² of toilets for 1,750 primary students, one WC per
175 against the one-per-25 that Art. 8.2(13) requires. The model applies the
article. That is why the resolved client-variant schedule (6,203 m² net) is
larger than the client document as written (5,790 m²).

### 6.2 The two programme variants

`programme_variant` picks which area column each room uses.

| | `client` | `compliant` |
|---|---|---|
| KG classroom | 49 m² (7 × 7) | 63 m² (7 × 9), Art. 8.1(1) |
| Primary classroom | 49 m² (7 × 7) | 56 m² (7 × 8), Art. 8.2(1) |
| Secondary classroom | 49 m² (7 × 7) | 56 m² (7 × 8), Art. 8.3(1) |
| Secondary hall | absent | 425.75 m², Art. 8.3(9) |
| Secondary workshop | absent | 192 m², Art. 8.3(14) |
| Secondary laboratories | 3 × 56 | 3 × 198, Art. 8.3(8) |
| Primary SEN centre, inclusive class | absent | 2 × 72 + 56, Arts. 8.2(18)(19) |
| **Resolved net at 2,930 students** | **6,203 m²** | **9,424 m²** |
| **GFA** | **8,684 m²** | **13,194 m²** |

Classroom density at the client sizes: KG 1.63, primary **0.98**, secondary 1.23
m² per student. Primary below one square metre per child is the tightest figure
in the programme and the first thing an inspector will notice.

**The compliant variant does not fit three separate compounds on this site.** It
fails C1, C3 and C6. That is the project's blocking decision, not a modelling
artefact.

### 6.3 Structural grid

| Variant | Bay | Classroom | Delivered |
|---|---|---|---|
| `client` | 7.0 m | 7.0 × 7.0 | 49.00 m² |
| `compliant` | 8.0 m | 8.0 × 7.0 | 56.00 m² |
| `compliant` KG | 8.0 m | 8.0 × 7.875 | 63.00 m² |

The kindergarten facade pushes out 0.875 m relative to the floors above. Since
the KG band is the widest part of a mass that only diminishes upward, that
bulge is structurally free. The guideline regulates area; the 7 × 9 in the
parenthesis is descriptive.

Transverse frame **7.0 | corridor | 7.0**. Corridor 3.0 m minimum, wider where
the bar depth allows — at this density circulation is the only informal
learning space available.

### 6.4 Largest rooms set the minimum bar depth

| Room | Article | Size | Depth needed |
|---|---|---|---|
| Multipurpose hall | 8.3(9) | 16.25 × 26.20 | **16.25** |
| Secondary library | 8.3(10) | 16 × 17 | 16.00 |
| Primary library | 8.2(4) | 12 × 15 | 12.00 |
| Science laboratory | 8.3(8) | 22 × 9 | 9.00 |
| Workshop | 8.3(14) | 24 × 8 | 8.00 |

Nothing exceeds 16.25 m, so bars of 17–21 m take the whole schedule. Put the
hall, libraries and workshop at ground level where long spans need no transfer
above and community access out of hours is straightforward.

---

## 7. Assembly and yards

All three schools assemble **simultaneously**, so all three yards must exist at
once. No time-sharing.

Standing allowance is built from 95th-percentile shoulder breadth and body
depth plus the gap each age needs to hold a rank, grossed up for aisles
between class blocks, staff positions and the flag-mast frontage.

| Cohort | Age | Shoulder | Lateral pitch | Rank pitch | Design | **Dense · adopted** |
|---|---|---|---|---|---|---|
| Kindergarten | 4–6 | 0.28 | 0.50 | 0.70 | 0.58 | **0.36** |
| Primary G1–4 | 7–10 | 0.32 | 0.55 | 0.70 | 0.50 | **0.31** |
| Primary G5–8 | 11–14 | 0.38 | 0.60 | 0.75 | 0.65 | **0.41** |
| Secondary | 15–18 | 0.46 | 0.65 | 0.80 | 0.73 | **0.45** |

Kindergarten carries a 1.50 gross factor against 1.25–1.30 for the older
cohorts: four-year-olds do not hold ranks, teachers stand among them, and any
child must be reachable quickly. So the smallest bodies do not give the
smallest allowance per head.

`standing_rate_m2_per_student` in the config takes one figure per school; the
primary value is the blended 0.36. Switching to design rates makes the scheme
infeasible — the model shows it.

**Overlapping the assembly onto the pitch is what makes this work.** Three
separate assembly areas plus three separate pitches needs 2,359 m² at dense
rates. Overlapped — the same paved surface at different times — it needs
1,424 m². That one decision releases 935 m². Setting
`overlap_assembly_with_pitch: false` makes the scheme infeasible.

| | Students | Assembly | Pitch | **Yard** | Governed by |
|---|---|---|---|---|---|
| Kindergarten | 540 | 194 | 150 | **194** | assembly |
| Primary | 1,750 | 630 | 500 | **630** | assembly |
| Secondary | 640 | 288 | 400 | **400** | playing ground |

### 7.1 The playing-ground rectangle is a hard geometric constraint

Each yard must hold its playing ground as a **clear rectangle** beside its own
building. This is what broke the client's stated figures:

> The client's secondary ground is **30 × 20 m**. That needs 30 m of clear yard
> width. Only the south band is wide enough — and the primary school needs the
> south band for its own larger yard. **20 × 20 m is the largest that fits.**

Secondary needs only 288 m² to assemble, so nothing is lost at the flag
ceremony. Set `playing_ground_m2.secondary` back to 600 and
`playing_ground_min_rect_m.secondary` to `[30, 20]` to reproduce the conflict —
the model fails C6 and tells you.

`enforce_playing_ground_rect: false` relaxes the rectangle to an area test only.

**Yard area** is the band minus the building, including the tapered sliver to
the west. **The rectangle** must sit in the clean strip beside the building,
with a 3 m path along the facade. These are different tests and both apply.

---

## 8. Compound rules

1. **Three compounds, stacked as horizontal bands** across the site, south to
   north. Each holds one school's building, yard and gate.
2. **Buildings sit east**, along the assumed road. **Yards run west** behind
   them, away from traffic noise and dust.
3. **Nothing outdoors is shared.** Fence lines run east–west between compounds.
   The three yards read as one field divided into pitches; gates between them
   open only for whole-campus events.
4. **One gate per school**, each with its own forecourt and drop-off, placed in
   the perimeter wedges rather than inside the band.
5. **Separation joints:** kindergarten 3.0 m to its neighbour; primary and
   secondary 0.0 m, since they may share structure. Circulation, cores,
   sanitary stacks and staff accommodation stay entirely separate regardless.
6. **Band allocation is forced by the taper, not chosen.** The site is 68 m
   wide at the south and 53 m at the north. The hungriest compound takes the
   widest band. At the current baseline that is primary south, secondary
   middle, kindergarten north. It flips if the road hierarchy says the youngest
   must sit furthest from traffic — still an open question.
7. **Minimum plate** 500 m² for primary and secondary, so no school becomes a
   point block where the stair and lift eat the floor. Sized on area alone the
   secondary would come out 15 m long over seven storeys.
8. **Sizing minimises footprint, not storeys.** Open ground is scarcer than
   storeys here. Getting this backwards made a 41% cut in floor area shrink the
   footprint by only 9%.
9. **Kindergarten no higher than G+2**, and lowest-and-nearest-to-ground in its
   own compound, with an external ramp and two direct stairs to grade.
10. **Central office** is a group function serving all three schools. With
    staff separated it cannot sit inside any one compound without that school
    hosting the other two, so the default is a **gate pavilion** at the main
    entrance — which also gives visitor reception for all three without anyone
    entering a school. `central_office_with` can place it in a compound
    instead, which is 107 m² more land-efficient.

---

## 9. The input file

`data/config.json`. Everything below is live — change it and re-run.

### 9.1 Capacity

| Key | Type | Baseline | Effect |
|---|---|---|---|
| `enrolment` | int per school | 540 / 1750 / 640 | **drives everything** |
| `class_size_override` | int per school | {} | defaults to Art. 11: 30 / 50 / 40 |
| `classroom_area_override` | m² per school | {} | overrides the variant's classroom area |
| `programme_variant` | enum | `client` | `client` \| `compliant` |
| `consolidate_registered_units` | bool | true | the Art. 15 position |
| `gross_up_factor` | float | null → 1.40 | net to gross |
| `central_office_with` | enum | `gate_pavilion` | or a school name |

### 9.2 Outdoor

| Key | Type | Baseline | Effect |
|---|---|---|---|
| `standing_rate_m2_per_student` | m² per school | 0.36 / 0.36 / 0.45 | dense rates; design rates are 0.58 / 0.58 / 0.73 |
| `playing_ground_m2` | m² per school | 150 / 500 / 400 | |
| `playing_ground_min_rect_m` | [L, S] per school | [15,10] / [25,20] / [20,20] | hard geometric constraint |
| `enforce_playing_ground_rect` | bool | true | false relaxes to an area test |
| `overlap_assembly_with_pitch` | bool | true | **false makes the scheme infeasible** |
| `simultaneous_assembly` | bool | true | all three yards coexist |
| `yard_circulation_factor` | float | 0.15 | paths and fence margins |
| `min_open_at_grade_m2` | m² | 0 | absolute floor |
| `min_open_at_grade_per_student_m2` | m² | 0.90 | **per-student floor — the binding one** |

### 9.3 Building and site

| Key | Type | Baseline |
|---|---|---|
| `max_site_coverage` | fraction | 0.63 |
| `max_levels` | int per school | 3 / 7 / 7 |
| `min_plate_m2` | m² per school | 0 / 500 / 500 |
| `max_bar_depth_m` | m | 21.0 |
| `min_bar_length_m` | m | 24.0 |
| `ground_floor_h_m` / `upper_floor_h_m` | m | 4.5 / 3.6 |
| `max_height_m` | m | 27.0 |
| `setback_m` | m per edge | N 2, E 2, S 2, W 3 |
| `gate_and_dropoff_m2` | m² per school | 220 / 200 / 180 |
| `gate_pavilion_m2` | m² | 300 |
| `perimeter_and_fire_m2` | m² | 250 |
| `bar_azimuth_deg` | degrees | 90.0 |
| `basement_under` / `basement_depth_m` | — | auto / 4.0 |

`separation`: `kg_joint_m` 3.0, `primary_secondary_may_share_structure` true,
`shared_structure_joint_m` 0.0, and three booleans recording that circulation,
playground and staff are all separated.

`bar_azimuth_deg` exists so you can test a rotation. **90.0 is expected to
win** — the site is already cardinal. Report the delta rather than assuming it.

---

## 10. Constraints

### 10.1 Area and programme — checked by `campus_model.py`

| | Check |
|---|---|
| **C1** | total ground demand ≤ site area |
| **C2** | footprint ≤ `max_site_coverage` × site |
| **C3** | open at grade ≥ `min_open_at_grade*` |
| **C4** | levels within `max_levels` per school |
| **C5** | height ≤ `max_height_m` excluding parapet |
| **C6** | three stacked compounds fit the boundary |

### 10.2 Geometry — checked by `validate_campus.py`

| | Check |
|---|---|
| **G1** | buildings inside the boundary and clear of the setbacks |
| **G2** | joints respected — 3.0 m to the kindergarten, 0.0 m between primary and secondary |
| **G3** | compound bands do not overlap |
| **G4** | yard area sufficient AND the playing-ground rectangle fits beside the building |
| **G5** | drawn footprint matches the scheduled plates |
| **G6** | coverage within the cap |
| **G7** | open at grade meets the requirement |
| **G8** | bar depth ≤ `max_bar_depth_m` — the daylight rule, no desk more than 9 m from a window |
| **G9** | bar length ≥ `min_bar_length_m` |
| **G10** | plan aspect ratio ≤ 4:1 — seismic regularity |
| **G11** | all three buildings with their long axis east–west |
| **G12** | height within the cap |

A scheme that does not pass all eighteen is not a candidate.

### 10.3 Rules the scripts cannot check — your responsibility in Rhino

- No internal circulation connects two schools.
- Sanitary stacks align vertically through every level of their own volume.
- Plates never grow with height; every column runs to foundation.
- Each school's gate reaches its own yard without crossing another compound.
- Shear-wall centroid near the mass centroid in each volume.
- Agricultural plot ≥ 120 m² and greenery ≥ 200 m², on roofs or in the wedges.

---

## 11. Objectives — rank candidates that pass §10

Maximise, in order: **outdoor area at grade per student**; fraction of
classrooms facing north or south, target 100%; total outdoor area; yard sun
hours on 21 June and 21 December, 09:00–15:00.

Minimise: footprint; facade area per m² of GFA; distinct floor plates; sum of
levels across the three volumes — cost per m² rises materially above G+5 with
lifts, second escape stairs and pumped water storage.

Report all eight for every candidate.

---

## 12. Rhino construction sequence

1. Units metres, absolute tolerance 0.001, angle tolerance 0.1°.
2. Layers: `00_SITE`, `01_BOUNDARY`, `02_SETBACK`, `10_KG`, `11_KG_YARD`,
   `12_KG_ROOF`, `20_PRIMARY`, `21_PRIMARY_YARD`, `22_PRIMARY_ROOF`,
   `30_SECONDARY`, `31_SECONDARY_YARD`, `32_SECONDARY_ROOF`, `40_PITCHES`,
   `41_ASSEMBLY`, `42_AGRI`, `43_GREEN`, `50_BASEMENT`, `60_GRID`,
   `70_GATES`, `71_PAVILION`, `80_SHADOW`, `90_ANALYSIS`.
3. Draw the boundary from the five local coordinates and close it. Confirm the
   area reads 4,618.05 ± 0.5 m².
4. Offset inward by the per-edge setbacks.
5. Read `data/campus_solution.json`. For each compound, build the band
   rectangle, then the building rectangle from `bar`, then the yard from `yard`.
6. Extrude level by level: ground 0 → `ground_floor_h_m`, then each upper level
   by `upper_floor_h_m`. Keep each level a separate Brep.
7. Cap each volume with a roof surface. Agricultural plot and greenery go here.
8. Draw the structural grid on each plate: `bay_m` along the bar, transverse
   `7.0 | corridor | 7.0`.
9. Inscribe each playing-ground rectangle in its yard and mark the assembly
   area and flag mast.
10. Basement solid from −`basement_depth_m` to 0.0 under the nominated volume.
11. Gates and drop-offs in the wedges; gate pavilion at the main entrance.
12. Fence lines along the compound boundaries.
13. Shadow studies 21 March, 21 June, 21 September, 21 December at 09:00, 12:00
    and 15:00 local solar time.
14. Export to the solution schema and run `validate_campus.py`.

Keep every step scripted from the parameter set. Do not hand-place geometry.

---

## 13. How the model responds — verification sweep

`python3 -I scripts/sweep.py` reproduces this. Every failure is real.

| Scenario | Students | GFA | Footprint | Open/student | Levels K/P/S | Result |
|---|---|---|---|---|---|---|
| **As issued** | 2,930 | 8,684 | 1,885 · 40.8% | 0.93 | G+2/6/4 | **OK** |
| 3,600 students | 3,600 | 10,141 | 2,032 · 44.0% | 0.72 | G+2/6/6 | fails C3, C6 |
| 2,400 students | 2,400 | 7,745 | 1,752 · 37.9% | 1.19 | G+2/6/4 | OK |
| Compliant schedule | 2,930 | 13,194 | 2,516 · 54.5% | 0.72 | G+2/6/6 | fails C1, C3, C6 |
| Compliant + 20×20 pitch | 2,930 | 13,194 | 2,516 · 54.5% | 0.72 | G+2/6/6 | fails C1, C3, C6 |
| Design standing rates | 2,930 | 8,684 | 1,885 | 0.93 | G+2/6/4 | fails C1, C6 |
| Assembly not overlapped | 2,930 | 8,684 | 1,885 | 0.93 | G+2/6/4 | fails C1, C6 |
| Open ground ≥ 1.20 m²/student | 2,930 | 8,684 | 1,885 | 0.93 | G+2/6/4 | fails C3 |
| Central office in primary | 2,930 | 8,684 | 1,778 · 38.5% | 0.97 | G+2/6/4 | **OK, better** |
| No unit consolidation | 2,930 | 9,880 | 2,180 · 47.2% | 0.83 | G+2/6/4 | fails C3, C6 |

Read it as the project's decision map:

- **3,600 students no longer fits** three separated compounds at 0.90 m² of
  open ground per student. Earlier advice that it fitted was given before the
  separation rules and the open-ground floor existed. Reaching 3,600 now means
  accepting ~0.72 m²/student at grade, or finding land.
- **The compliant schedule fails on every count**, and cutting the secondary
  pitch no longer rescues it once the open-ground floor applies.
- **Overlapping assembly with the pitch, and the dense standing rates, are both
  load-bearing.** Lose either and the scheme fails.
- **Putting the central office inside a compound is more land-efficient** than a
  gate pavilion, by 107 m². The reason not to is the staff-separation rule.

---

## 14. Open issues — flag these, do not silently assume

1. **Which boundary is the Ambo Road**, and is there a usable northern
   frontage? It fixes the three gates, the drop-offs and which faces take
   acoustic and dust screening. The model assumes the east.
2. **Road reservation setbacks** are unquantified on every frontage.
3. **The geotechnical report does not cover this site.** Four holes to 15 m
   inside the polygon, reporting swell pressure and active-zone depth.
4. **Which programme.** The compliant schedule cannot coexist with three
   separated compounds here. This is the blocking commercial decision.
5. **Enrolment.** 2,930 from this programme against 3,600 in Design Brief 01,
   on which the business case was built.
6. **Where the central office goes**, given staff separation.
7. **Primary classroom density** at 0.98 m² per student under the client
   variant — below one square metre per child.
8. **Art. 8.2(6)** — departmental rooms read as 96 m² *combined*, not each
   (*bal'inni waliigalaa isaanii*). Confirm with the Bureau; it swings 288 m².

---

*Rapha Engineering and Consulting for Boriyad Youth Academy. Issued for
parametric model build.*
