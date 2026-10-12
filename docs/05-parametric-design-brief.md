# Boriyad Youth Academy — Parametric Design Brief for a Rhino/Grasshopper Agent

**Version** R1 · 12 October 2026
**Audience** an autonomous agent building a parametric massing and planning
model in Rhino via Rhino MCP.
**Status** issued for model build. Everything in this document is either a
measured fact, a cited regulation, a client instruction, or an explicitly
labelled assumption.

Machine-readable companions, all in `data/`:

| File | Contents |
|---|---|
| `site.json` | survey coordinates, boundary functions, orientation, climate, ground, services |
| `program.json` | the full reconciled schedule of accommodation, room by room |
| `seed_layouts.json` | four validated starting layouts (2 topologies × 2 programme scenarios) |
| `constraints.json` | the hard and soft constraints below, as machine-checkable records |

Build scripts, re-runnable: `scripts/build_program.py`, `scripts/build_site.py`,
`scripts/solve_massing.py`, `scripts/validate_scheme.py`.

---

## 0. How to use this document

1. Read §§2–7 for the invariants. Do not re-derive them.
2. Pick a **programme scenario** (§6) and a **topology** (§8). If not told
   otherwise, build `T1_three_bars` under `B_compliant`.
3. Load the seed layout from `data/seed_layouts.json`, build it (§10), then
   vary the parameters in §9 to search.
4. Score every candidate against §11 and §12, and reject anything that fails a
   hard constraint.
5. Run `scripts/validate_scheme.py <your_scheme.json>` before reporting.

**Units are metres throughout. Angles are degrees. Areas are m².**

---

## 1. Project description

A new purpose-built campus for Boriyad Youth Academy at Ashewa Meda, in the
Oromia Special Zone surrounding Finfinne, on the Ambo Road corridor west of
Addis Ababa. The site is 4,618.05 m². The campus houses **three separately
registered and separately administered schools** on one plot:

| School | Grades | Classrooms | Class size (Art. 11) | Students |
|---|---|---|---|---|
| Kindergarten | Pre-KG, KG, Prep | 18 (6 + 6 + 6) | 30 | 540 |
| Primary | 1–8 | 35 | 50 | 1,750 |
| Secondary | 9–12 | 16 | 40 | 640 |
| **Total** | | **69** | | **2,930** |

Height cap **G+6** (seven levels), imposed by the client. Full-day operation,
no shift system (Art. 12), so the full classroom count must be built.

**The defining characteristic of the project is density.** At 2,930 students on
4,618 m² the site provides 1.58 m² of land per student. International norms
assume 8–12 m²; the densest respectable urban school typologies, in Singapore
and Hong Kong, operate at 3–5 m². This is a vertical school, and the scarce
resource is not floor area but **usable outdoor area**, which the typology
destroys at grade and must manufacture back on roofs and in courts.

### 1.1 The client's governing instruction

> *The three sections must be separated and have different entrances.*

This is a hard constraint, not a preference. Each school is a **structurally
independent volume** with its own street entrance, its own vertical cores, its
own sanitary stacks and its own administration. No internal circulation
connects any two schools. Volumes are separated by movement joints.

---

## 2. Site — survey coordinates

CRS: **UTM Zone 37N, Adindan datum**. Lengths in metres.

### 2.1 Boundary points as surveyed

| Point | Easting | Northing | Local X | Local Y |
|---|---|---|---|---|
| P1 | 464112.500 | 996833.918 | 112.500 | 133.918 |
| P2 | 464109.918 | 996749.453 | 109.918 | 49.453 |
| P3 | 464041.882 | 996761.305 | 41.882 | 61.305 |
| P4 | 464058.980 | 996827.622 | 58.980 | 127.622 |
| P5 | 464066.779 | 996828.861 | 66.779 | 128.861 |

The polygon closes P1 → P2 → P3 → P4 → P5 → P1.

### 2.2 Model origin — set this first

> **Place the Rhino world origin (0, 0, 0) at E 464000.000, N 996700.000, at
> reduced level 0.00 = existing ground level.**
> Model **+X = true East**, **+Y = true North**, **+Z = up**.

Local coordinates are the survey values minus that origin, and every coordinate
in the rest of this document and in `data/*.json` is **local**. Do not rotate
the model. Do not work in survey coordinates — the numbers are large enough to
cost you floating-point precision in Rhino.

### 2.3 Derived geometry

| | |
|---|---|
| Shoelace area | **4,618.05 m²** (Design Brief 01 states 4,621.80; adopt the survey) |
| Perimeter | 275.95 m |
| Extent | 70.62 m east–west × 84.47 m north–south |
| Largest inscribed cardinal rectangle | **51 m E–W × 68 m N–S**, SW corner local (58.9, 58.5) |

### 2.4 Edges

| Edge | Length | Azimuth | Off nearest cardinal |
|---|---|---|---|
| P1–P2 east | 84.50 | 181.75° | **1.75°** |
| P2–P3 south | 69.06 | 279.88° | 9.88° |
| P3–P4 west | 68.49 | 14.46° | 14.46° |
| P4–P5 north | 7.90 | 80.97° | 9.03° |
| P5–P1 north | 46.00 | 83.69° | **6.31°** |

P5 lies 0.09 m off the line P4–P1 — treat the north boundary as a single edge
with a slight kink.

### 2.5 Boundary as functions — use these for containment tests

```
west  edge P3–P4 :  x = 41.882  + 0.25783  * (y - 61.305)     for  61.305 <= y <= 127.622
east  edge P1–P2 :  x = 109.918 + 0.030569 * (y - 49.453)     for  49.453 <= y <= 133.918
south edge P2–P3 :  y = 49.453  + 0.174196 * (109.918 - x)    for  41.882 <= x <= 109.918
north edge P4–P5 :  y = 127.622 + 0.158867 * (x - 58.980)     for  58.980 <= x <=  66.779
north edge P5–P1 :  y = 128.861 + 0.110606 * (x - 66.779)     for  66.779 <= x <= 112.500
```

A horizontal band between `y0` and `y1` admits an axis-aligned rectangle
spanning `x` from `west(y1)` to `east(y0)` — the west boundary moves east as y
increases, and the east boundary moves east as y increases, so the band's
limits are set at opposite ends. Apply setbacks on top.

### 2.6 The two findings that govern

**The site is cardinally aligned.** The east boundary runs within 1.75° of true
north–south and the north boundary within 6.31° of true east–west. Building
parallel to the boundaries therefore also aligns long elevations north and
south. **Do not rotate the structural grid.** Earlier project documents
(Design Brief 01 §10.2) assume a 45° skew and call for rotation; they were
written before the survey and are wrong on this point.

**The usable depth is 64 m, not 84.5 m.** The north and south boundaries are
diagonal, so the plot wedges at both ends. After a 2 m setback, the south-most
viable bar base sits at y = 62.0 and the north-most bar top at y = 126.0. The
residual ~1,150 m² to the west and south is a wedge — landscape, drop-off,
agricultural plot, not orthogonal building.

### 2.7 Context and setbacks

| Boundary | Context | Setback assumed |
|---|---|---|
| East | **Assumed principal road (Ambo Road corridor) — TO BE CONFIRMED** | 2.0 m |
| South | Secondary road, junction at the south-west | 2.0 m |
| North | Possible frontage — TO BE CONFIRMED | 2.0 m |
| West | Lower-density residential, dense small plots | 3.0 m |

> **Open issue.** The road reservation is not quantified. Treat all four
> setbacks as parameters (§9) and re-run if a reservation is imposed. The
> scheme carries coverage headroom but the court dimension absorbs any move.

---

## 3. Climate, solar and wind

Latitude 8.97° N, longitude 38.78° E, altitude 2,324 m. Köppen *Weina Dega*
(subtropical highland).

| | |
|---|---|
| Mean annual temperature | 15.9 °C |
| Dry season | day 23.3 °C / night 7.3 °C |
| Wet season (kiremt) | 21.0 / 10.0 °C |
| Annual rainfall | 1,089 mm |
| Annual sunshine | 2,439 h |

### 3.1 Solar geometry — drives the massing

- Solar noon altitude **65–85°**. The sun passes directly overhead twice a
  year, about 20 April and 23 August.
- **Late April to late August** the sun tracks north of zenith. This coincides
  with the kiremt rains, when radiation is largely diffuse.
- The remaining **8.5 months** the sun tracks south of zenith, through the
  clear-sky dry season. The southern elevation is therefore the harsher one.
- **East and west are the critical orientations.** Between 07:00–09:00 and
  15:30–18:00 the sun sits at 10–30° altitude and strikes east- and west-facing
  glazing directly. Horizontal shading is useless at these angles.
- Design condition for overheating is **March–April**, the end of the long dry
  season, not mid-year.

**Shading rules to apply in the model**

| Facade | Device | Depth |
|---|---|---|
| North, south | horizontal overhang | 1.2 m |
| East, west | vertical fins or a veranda | 2.5–3.0 m |

**Consequence for massing:** classroom bars should run **true east–west** so
their long elevations face north and south. At this latitude a tall volume on
the *north* side of an open court throws its shadow away from the court for
8.5 months of the year — so the tallest volume belongs at the north.

### 3.2 Wind

| Season | Direction | Character |
|---|---|---|
| October–May (dry) | E to NE | northeast trades, dry and dust-laden |
| June–September (kiremt) | SW | moist monsoon, rain-driving |

Typical speeds 2–4 m/s. The dry-season dust comes from the east, which is also
the assumed road frontage — screen it. Driving rain comes from the south-west,
so any roof-level outdoor space needs a canopy to be usable in the rains.

---

## 4. Ground and structure

Source: NATM Engineering Plc geotechnical report, October 2024.

> **Critical caveat.** All six boreholes lie **36–84 m south of this site
> polygon**, the report is addressed to a different client (Three M JY Trading
> Plc) and names a different locality. It cannot carry foundation design here.
> Treat everything below as indicative regional data. Four new boreholes to
> 15 m inside the polygon are required. See `docs/02-ground-and-survey-review.md`.

### 4.1 Strata

| Layer | Description | Depth |
|---|---|---|
| A | Soft to medium stiff dark grey high-plastic silty CLAY — **black cotton** | 0 to 2.0–3.0 m |
| B | Stiff to very stiff reddish brown high-plastic silty CLAY with sand and gravel | to 3.5–15.0 m |
| C | Weak to moderately weak, highly weathered, closely jointed, fractured vesicular BASALT | below |

Rockhead is highly variable — 3.5 m at BH-5/BH-6 rising from 15.0 m at BH-2 —
and deepens northward. **No groundwater was encountered to 10–15 m.**

### 4.2 Expansive soil — the governing ground condition

Free swell reaches **130%** with a plasticity index of **63** at 1.5–2.0 m, and
**120% / PI 45** at 2.5–3.0 m. Two of twelve samples are in the *very high*
swell class, and one sits at the report's own recommended founding depth of
3.00 m. The active zone is assumed 2.5–4.0 m.

Model consequences:

- Founding level **−3.0 m** minimum below existing ground.
- **Basement slab at −4.0 m** clears the active zone entirely. With no
  groundwater there is no dewatering, no tanking against head and no uplift
  case, so the marginal cost over the required 3.0 m dig is about one metre.
- **Suspended ground-floor slab everywhere there is no basement** — never
  ground-bearing.
- No high-water-demand trees (eucalyptus above all) within 1.5 × mature height
  of any footing. Keep planting in the court, the western wedge or raised
  planters.

### 4.3 Bearing and foundations

| | |
|---|---|
| Allowable bearing, design | **275 kPa** at 3.0 m depth |
| Report's own recommendation | 364 kPa (adopts BH-3, not the weakest hole — do not use) |
| Typical column service load, G+6, 8 × 7 m grid | ~4,700 kN |
| Resulting pad | ~4.15 m square |

A 4.15 m pad on a 7.0 m grid clashes with its neighbour across a 4.0 m corridor
bay. Use combined footings or a strip under the corridor line, or a raft where
the basement occurs.

### 4.4 Seismic

Zone 3, PGA 0.10 g per ES EN 1998-1:2015. A school is **Importance Class III**,
γ<sub>I</sub> = 1.2, so the **design action is 0.12 g**. (The report states
I = 1.0, which is wrong for a school.)

Plan regularity therefore matters. In the model:

- Keep every volume a **plain rectangle in plan**. No re-entrant corners.
- Plan aspect ratio ≤ **4:1**.
- Shear-wall centroid close to the mass centroid in each volume.
- Separate volumes with movement joints of **≥ 3.0 m** (also the daylight slot).
- Plates may shrink with height but never grow — every column runs
  uninterrupted to foundation, no transfer structure.

---

## 5. Regulatory framework

Governing instrument: **Qajeelfama Istaandaardii Manneen Barnootaa Oromiyaa,
Lakk. 04/2016** (Ginbot 2016 E.C.), Oromia Education Bureau, under
Proclamation 242/2014. Article 4 applies it to private schools; Article 21
disapplies any conflicting guideline. It is binding, not advisory.

### 5.1 Provisions the model must satisfy

| Article | Requirement | How the model satisfies it |
|---|---|---|
| 7(1) | Zone for buildings | the three volumes |
| 7(2) | Flag ceremony area | ≥ 600 m² paved, at grade, may share a playing ground in rotation |
| 7(3) | Sports field | the three playing grounds, §6.3 |
| 7(4) | Agricultural plot | ≥ 120 m², may be raised beds on a terrace |
| 7(5) | Greenery | ≥ 200 m², including the *Gaaddisa* shaded reading place of Art. 2(12) |
| 8.1–8.3 | Room-by-room areas | the schedule in §6 |
| 9.1 | Highland colour scheme | KG blue beams and columns, grey roof; primary sky blue; secondary blue beams, grey roof, grey columns |
| 11 | Class sizes 30 / 50 / 40 | fixed; they drive the classroom counts |
| 12 | Full-day operation | no shift relief; all 69 classrooms built |
| 15 | Co-located schools keep their own administration | satisfied by three separate buildings |
| 16.1(1) | No images or writing on compound walls | no signage geometry on walls |
| 17(1) | Five learning corners (*Golee*) per KG classroom | pooled as a shared commons per cluster, §6.2 |

### 5.2 Waivers required — assume granted, but record the dependency

| Article | Requirement | Position |
|---|---|---|
| 6(1) | KG compound 1,000 m² urban | Full compliance across all three cycles needs >6 ha. Waiver essential; the vertical typology is the mitigation. |
| 6(2) | Primary compound 3 ha urban | as above |
| 6(3) | Secondary compound 3 ha urban | as above |

Article 22 empowers the Bureau to waive, and Article 13 contemplates schools
operating above standard. Article 11(4) sets *minimum* enrolments to open a new
school, not caps. Because the three schools now occupy three separate buildings
with separate administrations, **Art. 15 is satisfied without argument** and the
regulatory ask narrows to Art. 6 alone.

---

## 6. Space programme

Two scenarios. **Both must be buildable from the same parametric model** —
scenario is a parameter.

### 6.1 Scenario A — the client programme as issued

From `school_space_program.docx`. This is the client's operational wish-list.

### 6.2 Scenario B — reconciled against the guideline

Rule applied: where both sources specify the same facility, adopt the larger.
Where the guideline mandates a facility the client omitted, add it. Client-only
rooms are kept. Room-by-room detail with article citations is in
`data/program.json`.

| Block | Scenario A net | Scenario B net | Delta |
|---|---|---|---|
| Kindergarten | 1,364 m² | 1,943 m² | +579 |
| Primary (G1–8) | 2,665 m² | 4,136 m² | +1,471 |
| Central office | 213 m² | 213 m² | — |
| Secondary | 1,548 m² | 3,444 m² | +1,896 |
| **Net total** | **5,790 m²** | **9,735 m²** | **+3,945 (+68%)** |
| **GFA at 1.40** | **8,106 m²** | **13,630 m²** | **+5,524** |

> **This 68% gap is the single most important commercial fact in the project.**
> Scenario A will not pass licensing. The principal shortfalls are set out in
> §6.5.

**Gross-up factor 1.40.** Net-to-gross covers horizontal circulation (~14%),
vertical circulation (~5.5%), structure and walls (~6.5%) and services (~3%).
Note the net figures already include sanitary, storage, kitchen and guard
accommodation because Arts. 8.1–8.3 schedule these individually, so published
benchmarks as low as 1.25 are not comparable.

### 6.3 Classroom modules and the structural grid

| | Scenario A | Scenario B (guideline) | Article |
|---|---|---|---|
| KG classroom | 49 m² (7 × 7) | **63 m²** (7 × 9) | 8.1(1) |
| Primary classroom | 49 m² (7 × 7) | **56 m²** (7 × 8) | 8.2(1) |
| Secondary classroom | 49 m² (7 × 7) | **56 m²** (7 × 8) | 8.3(1) |

**Adopt an 8.0 m structural bay under Scenario B**, 7.0 m under Scenario A.

| Room | Resolution on an 8.0 m bay | Delivered |
|---|---|---|
| Primary / secondary classroom | 8.0 × 7.0 | **56.00 m²** exactly |
| KG classroom | 8.0 × 7.875 | **63.00 m²** exactly |

The kindergarten facade is pushed out 0.875 m relative to the floors above. The
KG band is the widest part of a mass that only ever diminishes upward, so that
bulge is structurally free. The guideline regulates area; the 7 × 9 in the
parenthesis is descriptive.

Transverse frame: **7.0 | corridor | 7.0**. Corridor 3.0 m minimum, 4.0–6.0 m
where the bar depth allows — a wide corridor is the only informal learning space
available at this density.

### 6.4 Largest rooms — these set the minimum bar depth

| Room | Article | Size | Deepest dimension |
|---|---|---|---|
| Multipurpose hall, secondary | 8.3(9) | 16.25 × 26.20 | **16.25** |
| Library, secondary | 8.3(10) | 16 × 17 | 16.00 |
| Library, primary | 8.2(4) | 12 × 15 | 12.00 |
| Science laboratory, secondary | 8.3(8) | 22 × 9 | 9.00 |
| Workshop, secondary | 8.3(14) | 24 × 8 | 8.00 |
| Dining hall | 8.2(16), 8.3(21) | 8 × 15 | 8.00 |

Nothing exceeds 16.25 m. **A bar depth of 17–21 m accommodates the entire
schedule.** Place the hall, libraries and workshop at ground level, where long
spans are achievable without transfer structure above and where community access
out of hours is straightforward.

### 6.5 Where Scenario A fails the guideline — the compliance register

The largest gaps, for the client conversation. Full detail in `program.json`.

| Item | Client | Guideline | Shortfall |
|---|---|---|---|
| **Primary student toilets** | 20 m² total | 1 pit per 25 students → 70 pits ≈ 180 m² | **−160 m²** — one WC per 175 students as drawn. Will fail licensing and is a welfare issue. |
| Secondary multipurpose hall | absent | 425.75 m², Art. 8.3(9) | −426 |
| Secondary science laboratories | 3 × 56 | 3 × 198 (22 × 9), Art. 8.3(8) | −426 |
| Secondary workshop | absent | 192 m² (24 × 8), Art. 8.3(14) | −192 |
| Primary SEN support centre + inclusive class | absent | 2 × 72 + 56, Arts. 8.2(18)(19) | −200 |
| Classroom areas, all cycles | 49 m² | 56 / 63 m² | −609 |
| Primary libraries | 2 × 100 | 2 × 180, Art. 8.2(4) | −160 |
| Secondary library | 120 | 272, Art. 8.3(10) | −152 |
| Secondary toilets | 10 m² | 26 pits ≈ 65 m² | −55 |
| Girls' hygiene rooms | absent | Arts. 8.2(14), 8.3(19) | −79 |
| Various omitted mandatory rooms | absent | day care, exam printing, records, teaching-material production, food stores, guard rooms | −400 |

Two transcription errors in the client document, corrected in `program.json`:
secondary cleaners' room reads "3m × 3m = 90 m²" (taken as 9 m²); KG and
primary toilet counts are given as areas, not fixtures.

### 6.6 Outdoor requirements

| Item | Source | Required | Clear rectangle |
|---|---|---|---|
| KG playground | client | 150 m² | 15 × 10 |
| Primary playing ground | client | 500 m² | 25 × 20 |
| Secondary playing ground | client | 600 m² | 30 × 20 |
| Flag ceremony area | Art. 7(2) | ≥ 600 m² | may share a playing ground in rotation |
| Agricultural plot | Art. 7(4) | ≥ 120 m² | raised beds acceptable |
| Greenery / *Gaaddisa* | Art. 7(5), 2(12) | ≥ 200 m² | shaded, under trees, at distance from footings |

> **Note.** The client's secondary ground is **30 × 20 m**, not a FIBA court
> (which needs 32 × 19 with run-off). The 30 × 20 requirement is what governs.
> A full FIBA rectangle is an upgrade to test, not a constraint.

Because the three schools are separated, **each school's playing ground must be
reachable without entering another school** — either at grade within its own
demise, or on its own roof.

### 6.7 Services, to be accommodated in the model

| | |
|---|---|
| Water demand | ~30 m³/day; 2 days' storage = 80 m³ bulk tank + 25 m³ roof service tank |
| Wastewater | 25–40 m³/day. Arts. 8.2(13)/8.3(17) specify pits, which cannot stack: **waterborne sanitation**, ~144 WCs |
| Treatment | on-site packaged plant (baffled reactor + planted gravel filter). **No soakaway is possible in this clay.** Treated effluent irrigates the agricultural plot |
| Rainwater harvesting | ~2,100 m³/year from ~2,500 m² of roof — about a third of annual demand |
| Basement | **one basement only, not the whole footprint** (client instruction). ~800–950 m² under one volume, slab at −4.0 m, vehicle ramp from a service forecourt |

Sanitary stacks must align vertically through every level of their volume.

---

## 7. Deliverables expected from the model

1. Closed Brep solids for each school volume, one per level, on named layers.
2. Floor plates as planar surfaces with the structural grid drawn.
3. Roof surfaces with the playing-ground rectangles inscribed.
4. Open-space surfaces: court, playing grounds, flag ceremony area,
   agricultural plot, greenery, drop-offs.
5. Entrance markers — one point and direction vector per school.
6. Basement extent as a solid at −4.0 to 0.0.
7. A JSON report matching the schema that `scripts/validate_scheme.py` reads.
8. Shadow studies at 21 March, 21 June, 21 September and 21 December, at
   09:00, 12:00 and 15:00 local solar time.

---

## 8. Massing topologies

Two topologies survive the constraints. Seeds for both are in
`data/seed_layouts.json`, already validated against §11.

### T1 — Three Bars

Three parallel bars running true east–west, separated by movement joints, each
school's playing ground on its own roof.

- Every classroom in every school faces north or south. Best possible solar.
- Each school owns its own roof outright.
- Maximum formwork repetition; three plain rectangles; ideal seismic
  configuration.
- **No open court at grade.** Three bars of 17–21 m plus two joints consume the
  whole 64 m of usable depth.
- **Feasible under both scenarios.**

### T2 — Court

Two east–west bars plus one north–south volume on the east road edge, enclosing
an open court at grade on three sides, open west.

- A real court at grade: sports, flag ceremony and agriculture in one room,
  overlooked from every classroom, at zero structural cost.
- The north–south volume's classrooms face east and west — the poor
  orientations. Assign it to the school with the fewest classrooms and the most
  orientation-indifferent specialist rooms.
- The tallest volume sits north of the court, which at 9° N throws its shadow
  away from the court.
- **Feasible only under Scenario A.** Under Scenario B the east volume cannot
  reach the required GFA within G+6: its footprint ceiling is ~550 m², giving
  3,850 m² at seven levels against a 4,821 m² requirement.

### 8.1 Seed layouts (local coordinates, metres)

Volumes are listed south to north.

**`T1_three_bars__B_compliant`** — recommended under the compliant schedule
footprint 2,465 m² (53.4%), GFA 13,631 m², open at grade 2,153 m², joints 3.0 m

| Volume | x₀ | y₀ | x₁ | y₁ | L × D | Footprint | Levels | GFA |
|---|---|---|---|---|---|---|---|---|
| Kindergarten | 54.96 | 62.00 | 108.30 | 79.00 | 53.3 × 17.0 | 906.8 | G+2 | 2,720 |
| Secondary | 74.47 | 82.00 | 108.91 | 102.00 | 34.4 × 20.0 | 688.8 | G+6 | 4,822 |
| Primary | 68.20 | 105.00 | 109.62 | 126.00 | 41.4 × 21.0 | 869.8 | G+6 | 6,089 |

**`T1_three_bars__A_client`** — recommended under the client programme as issued
footprint 1,842 m² (39.9%), GFA 8,459 m², open at grade 2,776 m², joints 3.0 m

| Volume | x₀ | y₀ | x₁ | y₁ | L × D | Footprint | Levels | GFA |
|---|---|---|---|---|---|---|---|---|
| Kindergarten | 70.86 | 62.00 | 108.30 | 79.00 | 37.4 × 17.0 | 636.5 | G+2 | 1,909 |
| Primary | 80.13 | 82.00 | 108.91 | 102.00 | 28.8 × 20.0 | 575.6 | G+6 | 4,029 |
| Secondary | 79.62 | 105.00 | 109.62 | 126.00 | 30.0 × 21.0 | 630.0 | G+3 | 2,520 |

**`T2_court__A_client`**
footprint 1,644 m² (35.6%), GFA 8,531 m², open at grade 2,974 m², joints 3.0 m, court 780 m²

| Volume | x₀ | y₀ | x₁ | y₁ | L × D | Footprint | Levels | GFA |
|---|---|---|---|---|---|---|---|---|
| Kindergarten | 70.86 | 62.00 | 108.30 | 79.00 | 37.4 × 17.0 | 636.5 | G+2 | 1,909 |
| Secondary | 90.91 | 82.00 | 108.91 | 106.00 | 18.0 × 24.0 | 432.0 | G+5 | 2,592 |
| Primary | 75.88 | 109.00 | 109.74 | 126.00 | 33.9 × 17.0 | 575.6 | G+6 | 4,029 |
| Court | 56.41 | 82.00 | 88.91 | 106.00 | 32.5 × 24.0 | 780 | — | — |

`T2_court__B_compliant` is **infeasible** and is recorded as such in
`seed_layouts.json`.

Worked schemes for the two T1 seeds, with gates, basement and open spaces filled in,
are `data/scheme_T1_B.json` and `data/scheme_T1_A.json`. Both pass 20/20 hard
constraints — run `python3 -I scripts/validate_scheme.py data/scheme_T1_A.json`.

### 8.2 Programme-to-volume assignment rules

- **Kindergarten always takes the southernmost volume**, at the quietest corner
  furthest from the assumed east road, with direct ground access and its own
  walled garden. Maximum **3 levels** — the youngest at ground, a terrace on
  every floor, an external ramp and two direct stairs to grade.
- **Primary is the largest school** (35 classrooms) and needs the largest
  volume × most levels. Give it an east–west bar.
- **Secondary has the fewest classrooms (16) and the most
  orientation-indifferent specialist rooms** — three 22 × 9 laboratories, a
  24 × 8 workshop, a 425.75 m² hall, a 272 m² library. If one volume must run
  north–south, it is this one, with its classrooms facing the court behind a
  3 m veranda with vertical fins and the specialist rooms on the road side as
  an acoustic buffer.
- The central office (213 m²) sits with the primary school.

> **Frontage trap in T1.** Three bars stacked south to north leave the middle
> bar landlocked — its only possible gate is on the east. Place the middle
> school's entrance there, and take the other two gates to the south-west and
> the north, or H7 (gates ≥ 40 m apart) cannot be met. If there is no usable
> northern frontage, T1 needs the north bar's gate on the east as well, and the
> two east gates will sit about 39 m apart — marginally short. Confirm the
> northern frontage.

### 8.3 Entrances

Three gates, one per school, each from the perimeter, **≥ 40 m apart** measured
along the boundary, and no two on the same boundary segment where avoidable.
Each gate has its own forecourt and drop-off. The basement service ramp shares
a gate with the secondary or primary school, never the kindergarten.

---

## 9. Parameters

| # | Parameter | Type | Range | Default |
|---|---|---|---|---|
| 1 | `scenario` | enum | `A_client`, `B_compliant` | `B_compliant` |
| 2 | `topology` | enum | `T1_three_bars`, `T2_court` | `T1_three_bars` |
| 3 | `bay_m` | float | 7.0 (A) or 8.0 (B) | by scenario |
| 4 | `bar_depth_m[school]` | float | 17.0 – 21.0, step 0.5 | 18 / 20 / 20 |
| 5 | `corridor_m[school]` | float | 3.0 – 6.0 | bar_depth − 14.0 |
| 6 | `levels[school]` | int | 1 – 7; KG ≤ 3 | from seed |
| 7 | `bar_y0[school]` | float | 62.0 – 126.0 | from seed |
| 8 | `bar_length_m[school]` | float | 24.0 – band width | from seed |
| 9 | `joint_m` | float | 3.0 – 6.0 | 3.0 |
| 10 | `setback_m[edge]` | float | 2.0 – 8.0 | N 2, E 2, S 2, W 3 |
| 11 | `ground_floor_h_m` | float | 4.0 – 5.0 | 4.5 |
| 12 | `upper_floor_h_m` | float | 3.3 – 3.9 | 3.6 |
| 13 | `basement_under` | enum | `kindergarten`, `primary`, `secondary`, `none` | `secondary` |
| 14 | `basement_depth_m` | float | 3.6 – 4.5 | 4.0 |
| 15 | `playground_placement[school]` | enum | `grade`, `roof` | by topology |
| 16 | `overhang_ns_m` | float | 0.9 – 1.8 | 1.2 |
| 17 | `fin_depth_ew_m` | float | 2.0 – 3.5 | 3.0 |
| 18 | `bar_azimuth_deg` | float | 83.0 – 97.0 | 90.0 |

Parameter 18 exists so the agent can test a small rotation. **The expected
result is that 90.0 wins** — the site is already cardinal. Report the delta
rather than assuming it.

Maximum building height check: `ground_floor_h + 6 × upper_floor_h` must not
exceed 27.0 m above ground, and the parapet and any ball-catch enclosure sit
above that.

---

## 10. Rhino construction sequence

1. Set units to metres, absolute tolerance 0.001, angle tolerance 0.1°.
2. Create layers: `00_SITE`, `01_BOUNDARY`, `02_SETBACK`, `10_KG`, `11_KG_ROOF`,
   `20_PRIMARY`, `21_PRIMARY_ROOF`, `30_SECONDARY`, `31_SECONDARY_ROOF`,
   `40_COURT`, `41_PLAYGROUNDS`, `42_FLAG`, `43_AGRI`, `44_GREEN`,
   `50_BASEMENT`, `60_GRID`, `70_ENTRANCES`, `80_SHADOW`, `90_ANALYSIS`.
3. Draw the boundary polyline from the five local coordinates in §2.1 and close
   it. Confirm the area reads 4,618.05 ± 0.5 m².
4. Offset inward by the per-edge setbacks to produce the buildable region.
5. For each school, build the base rectangle from `(x0, y0)` to `(x1, y1)`.
6. Extrude level by level: ground 0 → `ground_floor_h`, then each upper level by
   `upper_floor_h`. Keep each level a separate Brep so plates can differ.
7. Cap each volume with a roof surface; inscribe the playing-ground rectangle
   where `playground_placement == roof`.
8. Draw the structural grid on each plate: lines at `bay_m` along the bar, and
   transverse lines at `7.0 | corridor | 7.0`.
9. Build the basement solid from −`basement_depth_m` to 0.0 under the nominated
   volume only.
10. Build open-space surfaces by boolean difference: site minus footprints,
    then subdivide into court, playing grounds, flag ceremony, agricultural
    plot, greenery and drop-offs.
11. Place entrance points and direction vectors, one per school.
12. Run shadow studies at the dates and times in §7.
13. Export the JSON report and run the validator.

Keep every step scripted and re-runnable from the parameter set. Do not hand-place
geometry.

---

## 11. Hard constraints — a scheme failing any of these is rejected

| # | Constraint | Check |
|---|---|---|
| H1 | Every volume lies inside the boundary polygon minus its setbacks | sample the rectangle perimeter at 1 m and test point-in-polygon |
| H2 | Volumes are mutually disjoint with a clear joint ≥ `joint_m` ≥ 3.0 m | rectangle separation in x or y |
| H3 | Total footprint ≤ **63%** of 4,618.05 m² = **2,909.4 m²** | sum of footprints |
| H4 | Levels ≤ 7 (G+6) for every volume; kindergarten ≤ 3 | per volume |
| H5 | Height above ground ≤ 27.0 m excluding parapet | computed |
| H6 | GFA per school ≥ 97% of its scenario requirement | per school |
| H7 | Each school has exactly one entrance; entrances ≥ 40 m apart | pairwise distance |
| H8 | No internal circulation connects two schools | topological |
| H9 | Each school's playing ground fits as a clear rectangle inside its own demise, at grade or on its own roof | rectangle fit, both orientations |
| H10 | Flag ceremony area ≥ 600 m² at grade, paved, reachable by all three schools | area and adjacency |
| H11 | Agricultural plot ≥ 120 m²; greenery ≥ 200 m² | area |
| H12 | No point on a classroom floor is more than 9.0 m from a facade | bar depth ≤ 21.0 with a central corridor, or ≤ 9.0 m single-loaded |
| H13 | Bar depth ≥ 16.25 m in whichever volume carries the multipurpose hall | per volume |
| H14 | Plates never grow with height; no transfer structure | level-by-level containment |
| H15 | Plan aspect ratio of each volume ≤ 4:1 | per volume |
| H16 | Basement under at most one volume, footprint ≤ that volume's | per model |
| H17 | At least two of three volumes have their long axis within 7° of true east–west | per model |
| H18 | Classroom module delivers the scenario's required area exactly, ±0.5 m² | grid arithmetic |
| H19 | Sanitary stacks align vertically through all levels of their volume | per volume |
| H20 | Open ground at grade ≥ 1,400 m², excluding roofs | site minus footprints |

---

## 12. Objectives — rank candidates that pass §11

Maximise, in descending priority:

1. **Total usable outdoor area** (grade + roofs + court), target ≥ 4,600 m²,
   which is 1.57 m² per student and recovers the whole site area once over.
2. **Fraction of classrooms with a north or south aspect.** Target 100% under
   T1; ≥ 60% under T2.
3. **Outdoor area at grade** as a share of the total — grade beats roof for
   young children and for the flag ceremony.
4. **Court sun hours** on 21 June and 21 December, 09:00–15:00, where a court
   exists.

Minimise:

5. **Facade area per m² of GFA** — the main envelope cost driver.
6. **Number of distinct floor plates** — formwork repetition is the largest
   single cost lever in Ethiopian reinforced-concrete construction.
7. **Total footprint**, which preserves open ground.
8. **Sum of levels across the three volumes** — cost per m² rises materially
   above G+5 with lifts, second escape stairs and pumped water storage.

Report all eight for every candidate.

### 12.1 The tie-break that matters — do not get this wrong

When a school's required floor area can be housed by several
(levels × footprint) combinations, **choose the one with the smallest
footprint**, not the one with the fewest storeys. On this site open ground is
the binding scarcity, and every square metre of plate is a square metre of
playground forgone.

The first version of `solve_massing.py` returned the first level count that
fitted — that is, it minimised storeys — and the result was that cutting the
programme by 41% shrank the footprint by only 9%. The kindergarten plate
actually *grew*. Sizing to minimum footprint instead frees 641 m² of open
ground under the client programme and 260 m² under the compliant one, at no
cost in GFA.

Storeys are not free, so two floors are set under the search:

| Floor | Value | Why |
|---|---|---|
| `MINPLATE` for primary and secondary | 500 m² | below this a plate carries too few classrooms to justify a core, stair and lift |
| Playing ground on the volume's own roof | KG 150, primary 500, **secondary 600 m²** | the roof must still hold the rectangle |

**Under topology T1 the second floor binds before the first.** Scenario A needs
only 310 m² of plate for the secondary school at G+6, but its 30 × 20 m playing
ground forces 600 m². Past that point the playgrounds set the footprint, not the
schedule — which is why T1 does not shrink in proportion to the programme.
Moving a playing ground to grade, where the site allows it, is the lever that
breaks the floor.

### 12.2 Kindergarten levels — a judgement, not an optimisation

Minimising footprint pushes the kindergarten to three levels in every scenario.
Holding it to two, which is better for four- to six-year-olds, costs **318 m² of
open ground** under the client programme. Present both; do not let the optimiser
decide it silently.

---

## 13. Open issues — flag these in the report, do not silently assume

1. **Which boundary is the Ambo Road**, and is there a usable northern
   frontage? It fixes the three gates, the drop-offs and which faces take
   acoustic and dust screening. The model assumes the east.
2. **Road reservation setbacks** are unquantified on every frontage.
3. **The geotechnical report does not cover this site.** Four boreholes to 15 m
   inside the polygon, reporting swell pressure and active-zone depth.
4. **Scenario A will not pass licensing.** §6.5. The client must decide whether
   to build to the compliant schedule or to seek dispensations beyond Art. 6.
5. **Kindergarten at three levels** departs from the project's own Principle 1
   (KG no higher than Level 1). No regulation is breached. Under Scenario B the
   kindergarten cannot be held to two levels without losing the court or
   breaching coverage.
6. **Art. 8.2(6)** — departmental rooms read as 96 m² *combined*, not each
   (*bal'inni waliigalaa isaanii*). Confirm with the Bureau; it swings 288 m².
7. Enrolment implied by this programme is **2,930**, not the 3,600 in Design
   Brief 01. Confirm which figure governs the business case.

---

*Rapha Engineering and Consulting for Boriyad Youth Academy. Issued for
parametric model build.*
