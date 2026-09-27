# GridLock — Methodology

> How GridLock decides that two cross-utility projects are a coordination
> opportunity. The decision is deterministic geometry and calendar math — no
> LLM makes the call. Thresholds and tiers are parameters set by the challenge,
> not values GridLock tuned.

Last updated: 2026-09-27

---

## Inclusion threshold: 40 km (the enforced gate)

Two planned projects are screened as a candidate coordination pair only if their
geometries come within **40 km** of each other. Under 40 km → flag for review;
farther → ignore.

- The **enforced gate is 40 km = 40 000 m ≈ 24.855 mi.** The challenge docx/xlsx
  phrase the cutoff as **25 mi (≈ 40.234 km)**; GridLock implements the 40 km
  form. The two are **not identical** — they differ by ~0.23 km at the boundary,
  so a pair between 40.000 km and 40.234 km would pass a 25-mi rule but is
  rejected by the 40 km gate. All GridLock results use the 40 km gate.
- The rationale is operational: 40 km is roughly how far a crew drives from a
  morning staging yard. Inside that radius, two utilities can plausibly share
  crews, cranes, and contractors.
- In the implementation this is the constant `CANDIDATE_RADIUS_M = 40000.0` in
  [`backend/gridlock/config.py`](../backend/gridlock/config.py), enforced by the
  candidate filter (`ST_DWithin(..., 40000)` in PostGIS mode, or the
  `tier()` cutoff in file mode; the offline reference engine gates on
  `distance_m < 40_000.0`). It is a fixed parameter, not a per-request guess.

---

## Primary ranking: closest-point geometry distance

The **primary signal is distance**, and pairs are ranked closest-first — closer
means a higher-value coordination opportunity. Distance is measured as the
**minimum distance between the full geometries** of the two projects (their
closest points), never center-to-center.

The engine computes this by projecting both geometries into UTM 17N
(`EPSG:32617`, the most accurate projection for the SC/GA border region), taking
the nearest points between them, and reporting the separation. A pair whose
endpoint coordinates coincide computes to distance zero (crossing tier).

> Distances are closest-point, computed from published endpoint coordinates.
> Against a WGS 84 geodesic reference, model error within 40 km is under 0.35%
> (about 120 m at most). No tier assignment or qualifying pair changes under any
> of the models we tested.

---

## Secondary signal: in-service date gap in days

**Timeline overlap is a secondary signal, used alongside distance, not instead
of it.** GridLock measures the gap between the two projects' in-service dates in
**days**. A small gap means the two builds land in the same window and crews /
laydown / permits could genuinely be shared; a large gap (years apart) weakens
the case even when the projects are physically close.

Two important honesty rules:

- If either project's construction window is unknown, the timeline overlap is
  reported as **unknown / NULL** — never silently treated as overlapping.
- The date gap is reported **separately** from the distance so a reviewer can
  see both signals independently rather than a single blended number hiding a
  30-year schedule gap.

In the official answer key, for example, the two Thurmond-corridor overlaps have
day gaps of **3074 days** — physically close but ~8 years apart — which is
exactly the kind of nuance the separate timeline signal surfaces.

---

## The 4-tier coordination model

For a flagged pair, the closest-point distance maps to one of four coordination
tiers. Each tier describes what the two utilities can realistically share, and —
importantly for a screening tool — what is *shareable* at that tier:

| Tier | Distance | What can be shared / coordinated |
|---|---|---|
| **Crossing / touching** | intersects or 0 m | **Must coordinate:** outage timing, crossing structures. The endpoint coordinates coincide; whether the facilities physically meet cannot be confirmed from the published data, so the pair is flagged for coordination review. |
| **Shared land** | < 1.6 km | Share the land itself: right-of-way, access roads, permits. |
| **Shared logistics** | < 8 km | Share site logistics: laydown yards, deliveries. |
| **Shared crews** | < 40 km | Share crews and equipment mobilized from a common staging area. |

These four tiers and their cutoffs live in `TIERS` in
[`backend/gridlock/config.py`](../backend/gridlock/config.py). What is
"shareable" narrows as distance grows: at the crossing tier the utilities can
share physical structures and must align outages; by the 40 km tier the shared
value is mostly crews and equipment rather than land or permits. The tier label
is a coordination *hint* for a human planner, not an instruction to build.

---

## Center-to-center vs closest-point — why the upgrade matters

The official `Projects_Overlaps.xlsx` computes overlaps **center-to-center**:
each project is collapsed to the midpoint of its endpoints, and the distance is
the haversine between those two midpoints. GridLock's implementation instead
uses **closest-point distance between the full geometries**.

Closest-point is more faithful to reality:

- A transmission project is a corridor, not a point. Center-to-center throws
  away the extent of the line. A 60 km line whose midpoint is 30 km from another
  utility's substation can still pass **within a few km** of that substation —
  center-to-center hides that; closest-point catches it.
- Coordination happens where the works physically come near each other, which is
  a function of the closest approach, not of the midpoints.
- Where a project has only one located endpoint, its center collapses onto that
  single point, so center-to-center and closest-point converge for that project
  — but for two-endpoint projects, closest-point is strictly the more honest
  measure of how near the two builds actually get.

Both measures apply the 40 km flag threshold, so they agree on *whether* to
screen a pair in most cases; closest-point mainly changes the *ranking* and the
tier, pulling genuinely adjacent corridors up where they belong. On the official
dataset the two metrics produce the same six qualifying pairs; only the reported
distances differ.

---

## Why most project pairs correctly produce no overlap

With 5 DESC and 5 GPC projects there are **25 possible cross-utility pairs**. The
reference engine flags **6**; the other **19 pairs** correctly produce no
overlap, and that is the expected, healthy outcome:

- Utilities plan across large service territories. Most planned projects are
  simply far apart. Three projects appear in **no** overlapping pair at all —
  GPC_4 (Mitchell–North Tifton, southwest Georgia), GPC_5 (Jesup–Ludowici,
  southeast Georgia), and DESC_4 (Queensboro–Ft Johnson, Charleston) — because
  they sit in regions with no nearby cross-utility work.
- The 40 km filter exists precisely to reject far-apart pairs. A tool that
  "found" opportunities everywhere would be wrong; the value is in isolating the
  few genuine adjacencies from the many non-adjacencies.
- The challenge states this outright: **expect most of the dataset to not
  overlap, and finding the few real matches is the entire point.**

The overlaps that do survive cluster into two geographic corridors — the
Augusta/Thurmond area and the Savannah/Okatie area — which is the signature of a
correct screen: opportunities concentrate where two utilities genuinely build
near each other, and everything else is silent.

---

Related: [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) · [`COST_ESTIMATE.md`](COST_ESTIMATE.md)
· [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) · [`../README.md`](../README.md)
