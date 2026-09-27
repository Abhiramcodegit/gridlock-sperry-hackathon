STATUS: TARGET SPECIFICATION — NOT IMPLEMENTED. As of origin/main 1c31e2e6efc72599317de739f98ec55bcb6f6417, no engine on main implements this math. The official engine in PR #8 (backend/gridlock/official_engine.py, not on main) uses a different distance model; see Blocker 3. Target dataset: data/official/projects_official.json. No agent may describe this specification as implemented until an integration PR merges and acceptance checks G1–G26 pass against the engine it wires in. Sections 3 through 8 are superseded by pending Revision 2.3, which adopts a WGS 84 geodesic reference; see the section banner.

# GridLock Geometry Math

**Path:** `docs/specs/GEOMETRY_MATH.md`
**Status:** Target specification for the distance engine. Revision 2.2.1
**Scope:** Closest-point distance, projection, haversine, closest-point coordinates, center distance, shared-endpoint detection, projection error bound, rounding, unit conversion, and numerical edge cases

Companion specs:
- `docs/specs/API_CONTRACT.md` defines the response fields that carry these values.
- `docs/specs/EDGE_CASES.md` defines behavioral rules for ambiguous cases.

**Standing rule, project-wide:** every accuracy claim must name its reference model. A figure without a stated reference is not a figure.

### Revision history

| Rev | # | Change |
|---|---|---|
| 2 | R1 | Added shared-endpoint detection (§7) and `tier_confidence` derivation (§5.5) |
| 2 | R2 | Zero-length segments are valid and computed as a single location. They never cause `503` (§5.2, §10) |
| 2 | R3 | Invalid coordinates make the endpoint unknown instead of failing the load (§10) |
| 2 | R4 | Added the projection error bound (§8) |
| 2.2 | R5 | Line-one STATUS block and §3–§8 superseded banner. Distance-model ruling (Blocker 3, option a): closest points found in EPSG:32617, distance reported as the WGS 84 geodesic between them. Full rewrite is pending Revision 2.3 |
| 2.2 | R6 | **C-1 withdrawal.** The Monte Carlo figures 0.014% / 2.4 m (within 40 km) and 4.96% / 205 km (continental) are withdrawn project-wide. They came from a shared random stream and do not reproduce from seed 7 in an independent run. §8.3 now carries reproducible figures from `docs/specs/tools/projection_error_mc.py` |
| 2.2 | R7 | **C-3 reclassification.** The §8.3 figures measure projection error internal to the spherical model. They are self-consistency measurements, not accuracy measurements. Accuracy against WGS 84 is recorded separately in §8.5 with the only authorized judge wording |
| 2.2 | R8 | **C-2.** Shared-endpoint wording no longer asserts that the two endpoints are the same facility (§1, §7) |
| 2.2 | R9 | **C-4.** §7.2 example uses the verbatim dataset labels: `Thurmond Sub / THURMOND DAM #5` |
| 2.2.1 | R10 | Copy only: shared-endpoint label value changed to `Endpoints published at the same coordinates`, and positive "shared-facility finding" wording neutralized (§7.3, V11). No geometry, threshold, distance, detection, or matching change. Revision 2.3 remains reserved for the WGS 84 geodesic rewrite |

---

## 1. Constants

Every constant below is fixed. Do not change any of them to make results match a reference sheet.

| Name | Value | Unit | Purpose |
|---|---|---|---|
| `EARTH_RADIUS_KM` | `6371.0088` | km | Mean Earth radius (IUGG mean radius R₁), used by haversine and the local projection. Superseded by pending Revision 2.3 |
| `KM_PER_MILE` | `1.609344` | km/mi | Exact international statute mile |
| `INCLUSION_THRESHOLD_KM` | `40.0` | km | Pair is an opportunity only if `closest_distance_km < 40.0` |
| `TIER_TOUCH_KM` | `0.001` | km | Distances at or below 1 meter are `touching_crossing` |
| `SHARED_ENDPOINT_KM` | `0.001` | km | Two known endpoints this close resolve to the same location |
| `TIER_1_KM` | `1.6` | km | Upper bound, exclusive, for `under_1_6_km` |
| `TIER_2_KM` | `8.0` | km | Upper bound, exclusive, for `under_8_km` |
| `TIER_3_KM` | `40.0` | km | Upper bound, exclusive, for `under_40_km` |
| `EPS_LEN2_KM2` | `1e-12` | km² | Squared projected length below which a segment is treated as a single location |
| `EPS_ORIENT_KM2` | `1e-12` | km² | Tolerance for orientation (cross-product) tests |
| `GA_SC_LAT_MIN`, `GA_SC_LAT_MAX` | `30.3`, `35.3` | degrees | GA/SC validation box latitude range |
| `GA_SC_LON_MIN`, `GA_SC_LON_MAX` | `-85.7`, `-78.5` | degrees | GA/SC validation box longitude range |
| `DISTANCE_DECIMALS` | `3` | — | Response rounding for all distance fields |
| `COORD_DECIMALS` | `6` | — | Response rounding for all latitude and longitude fields |

All intermediate math uses IEEE 754 double precision (`float64`). Rounding happens only at serialization (§9).

---

## 2. Geometry model

| `geometry_confidence` | Model | Symbols used below |
|---|---|---|
| `endpoint_pair` | Straight segment from endpoint A to endpoint B. If A and B are identical, a zero-length segment computed as the single location A | Segment `AB` |
| `endpoint_only` | Single point at the one known endpoint | Point `P` |

**Segment definition.** A segment is the set of points whose latitude and longitude vary linearly from A to B:

\[
\varphi(t) = \varphi_A + t(\varphi_B - \varphi_A),\qquad \lambda(t) = \lambda_A + t(\lambda_B - \lambda_A),\qquad t \in [0, 1]
\]

It is not a great-circle arc. Because the projection in §4 is affine in latitude and longitude, this segment is exactly the straight segment in the projected plane for every choice of reference latitude.

Coordinates are `(φ, λ)` = `(lat, lon)` in degrees at input and output, and in radians inside formulas.

Both geometry types are valid, normal data. In the official dataset, 4 of the 10 projects are `endpoint_only`: `DESC_1`, `DESC_2`, `DESC_4`, and `GPC_2`.

---

> ## ⚠ Banner: §3–§8 superseded by pending Revision 2.3
>
> **Distance-model ruling (Blocker 3, option a):** closest points are found in EPSG:32617 (UTM 17N) with the existing shapely method in PR #8, and each reported distance is the **WGS 84 geodesic** (`pyproj.Geod`, ellipsoid `WGS84`) between those two closest points. The geodesic step belongs to the integration PR. PR #8 stays frozen.
>
> **Superseded in §3–§8 (non-authoritative until Revision 2.3):** the haversine metric (§3), the local equirectangular projection (§4), the spherical distance values produced in §5 and §6, and the spherical error bound (§8.1–§8.4). Test vectors V1–V12 (§11) and checks G1–G6, G12, G16–G18, and G22 inherit this status for their numeric values.
>
> **Still binding until Revision 2.3 says otherwise:** case dispatch (§5.4), clamping and candidate ordering logic (§5.2–§5.3), tier function and tier confidence (§5.5), center definition as midpoint (§6.1), closest-point versus center-to-center rules (§6.2–§6.3), shared-endpoint detection order, threshold, and naming (§7), the GA/SC validation box (§8.2), the WGS 84 accuracy record (§8.5), rounding and conversion (§9), and edge-case behavior (§10).
>
> For the official dataset, the model choice changes no qualifying pair and no tier (§8.5).

## 3. Haversine distance

Distance between two points `(φ₁, λ₁)` and `(φ₂, λ₂)`, with all angles in radians:

\[
a = \sin^2\!\left(\frac{\varphi_2 - \varphi_1}{2}\right) + \cos\varphi_1 \cos\varphi_2 \sin^2\!\left(\frac{\lambda_2 - \lambda_1}{2}\right)
\]

\[
a \leftarrow \min(1,\ \max(0,\ a))
\]

\[
c = 2 \cdot \operatorname{atan2}\!\left(\sqrt{a},\ \sqrt{1 - a}\right)
\]

\[
d_{km} = R \cdot c,\qquad R = 6371.0088\ \text{km}
\]

Required implementation details:

- Clamp `a` to `[0, 1]` before the square roots. Floating-point error can push `a` slightly outside that range.
- Use `atan2`, not `asin`, for numerical stability.
- Haversine is the **only** function that produces a reported distance under this revision's spherical model. Projected-plane lengths are used only to find the parameter `t` and to test intersection. They are never reported.

---

## 4. Local projection for segment math

Point-to-segment projection and segment intersection need a flat plane. Use a local equirectangular projection.

### 4.1 Reference latitude

For each distance computation, `φ₀` is the arithmetic mean latitude, in radians, of **every input position in that computation**:

| Case | Positions averaged |
|---|---|
| Point-to-segment | `P`, `A`, `B` (3 positions) |
| Segment-to-segment | `A₁`, `B₁`, `A₂`, `B₂` (4 positions) |

For segment-to-segment, all four point-to-segment sub-computations in §5.3 reuse this same 4-position `φ₀`.

### 4.2 Forward projection

\[
x = R \cdot \lambda \cdot \cos\varphi_0,\qquad y = R \cdot \varphi
\]

### 4.3 Inverse projection

\[
\varphi = \frac{y}{R},\qquad \lambda = \frac{x}{R \cdot \cos\varphi_0}
\]

Convert back to degrees for output.

---

## 5. Closest-point distance

Closest-point distance is the minimum distance between **any** point of one project's geometry and **any** point of the other project's geometry. It is the only distance used for the inclusion gate, tier assignment, and ranking.

### 5.1 Point-to-point

Used when both projects are `endpoint_only`. `distance_basis = "point_to_point"`.

\[
d = \text{haversine}(P_1, P_2)
\]

| Output | Value |
|---|---|
| `closest_point_desc` | The DESC point |
| `closest_point_gpc` | The GPC point |

### 5.2 Point-to-segment

Used when one project is `endpoint_only` (point `P`) and the other is `endpoint_pair` (segment `AB`). `distance_basis = "point_to_segment"`.

Steps:

1. Compute `φ₀` from `P`, `A`, `B` (§4.1).
2. Project `P`, `A`, `B` to plane coordinates `p`, `a`, `b` (§4.2).
3. Compute the segment vector and its squared length:

\[
\vec{v} = b - a,\qquad L^2 = \vec{v}\cdot\vec{v}
\]

4. If `L² < EPS_LEN2_KM2`, the segment is zero-length. Set `q = a` and skip to step 7. This is a valid case and is never an error.
5. Compute the projection parameter:

\[
t = \frac{(p - a)\cdot\vec{v}}{L^2}
\]

6. Clamp it to the segment:

\[
t \leftarrow \min(1,\ \max(0,\ t)),\qquad q = a + t\,\vec{v}
\]

7. Inverse-project `q` to `Q = (φ_Q, λ_Q)` (§4.3).
8. Compute the reported distance with haversine:

\[
d = \text{haversine}(P, Q)
\]

Clamping meaning:

| `t` before clamping | Closest point on segment |
|---|---|
| `t < 0` | Endpoint `A` |
| `0 ≤ t ≤ 1` | Interior foot of the perpendicular |
| `t > 1` | Endpoint `B` |

Outputs:

| Output | Value |
|---|---|
| Closest point on the point project | `P` |
| Closest point on the segment project | `Q` |

### 5.3 Segment-to-segment

Used when both projects are `endpoint_pair`. `distance_basis = "segment_to_segment"`. Segment 1 is always the DESC segment `A₁B₁`. Segment 2 is always the GPC segment `A₂B₂`.

**Zero-length pre-check.** Compute `φ₀` from all four endpoints and project them. If either segment has `L² < EPS_LEN2_KM2`:
- If only one segment is zero-length, compute §5.2 steps 3–8 from that single location to the other segment, using the shared 4-position `φ₀`.
- If both are zero-length, compute haversine between `A₁` and `A₂`.
- Keep `distance_basis = "segment_to_segment"`.
- Skip steps 3–6 below.

Steps for two non-degenerate segments:

1. Compute `φ₀` from all four endpoints (§4.1).
2. Project all four endpoints to `a₁`, `b₁`, `a₂`, `b₂`.
3. **Intersection test.** Define the orientation function:

\[
\operatorname{orient}(u, v, w) = (v_x - u_x)(w_y - u_y) - (v_y - u_y)(w_x - u_x)
\]

Treat any `|orient| ≤ EPS_ORIENT_KM2` as `0` (collinear).

\[
o_1 = \operatorname{orient}(a_1, b_1, a_2),\quad
o_2 = \operatorname{orient}(a_1, b_1, b_2),\quad
o_3 = \operatorname{orient}(a_2, b_2, a_1),\quad
o_4 = \operatorname{orient}(a_2, b_2, b_1)
\]

The segments intersect if either of these holds:
- **Proper crossing:** `sign(o₁) ≠ sign(o₂)` and `sign(o₃) ≠ sign(o₄)`, with all four nonzero.
- **Touching or collinear contact:** any `oᵢ = 0` and the corresponding endpoint lies within the other segment's bounding box, expanded by `1e-9` km on each side.

Because the projection is affine in latitude and longitude, this intersection test gives the same answer for any `φ₀`.

4. **If the segments intersect:**
   - `d = 0`.
   - For a proper crossing, compute the intersection point in the plane:

\[
s = \frac{\operatorname{orient}(a_2, b_2, a_1)}{\operatorname{orient}(a_2, b_2, a_1) - \operatorname{orient}(a_2, b_2, b_1)},\qquad x = a_1 + s\,(b_1 - a_1)
\]

   - For touching or collinear contact, the intersection point is the first endpoint, in the order `a₁, b₁, a₂, b₂`, that satisfies the contact condition.
   - Inverse-project the intersection point. Both `closest_point_desc` and `closest_point_gpc` equal it.

5. **If the segments do not intersect**, the minimum distance between two non-intersecting segments is reached at an endpoint of one of them. Evaluate these four point-to-segment candidates in this exact order, each using §5.2 steps 3–8 with the shared 4-position `φ₀`:

| Order | Point | Segment | `closest_point_desc` | `closest_point_gpc` |
|---|---|---|---|---|
| 1 | `A₁` (DESC) | `A₂B₂` (GPC) | `A₁` | foot on GPC segment |
| 2 | `B₁` (DESC) | `A₂B₂` (GPC) | `B₁` | foot on GPC segment |
| 3 | `A₂` (GPC) | `A₁B₁` (DESC) | foot on DESC segment | `A₂` |
| 4 | `B₂` (GPC) | `A₁B₁` (DESC) | foot on DESC segment | `B₂` |

6. Select the candidate with the smallest `d`. If two candidates tie within `1e-9` km, select the one that comes first in the table order.

### 5.4 Case dispatch

| DESC geometry | GPC geometry | Method | `distance_basis` |
|---|---|---|---|
| `endpoint_only` | `endpoint_only` | §5.1 | `point_to_point` |
| `endpoint_only` | `endpoint_pair` | §5.2 with DESC as `P`, GPC as `AB` | `point_to_segment` |
| `endpoint_pair` | `endpoint_only` | §5.2 with GPC as `P`, DESC as `AB` | `point_to_segment` |
| `endpoint_pair` | `endpoint_pair` | §5.3 | `segment_to_segment` |

### 5.5 Tier and tier confidence

| Output | Rule |
|---|---|
| `coordination_tier` | From full-precision `d`: intersect or `d <= 0.001` → `touching_crossing`; `< 1.6` → `under_1_6_km`; `< 8.0` → `under_8_km`; `< 40.0` → `under_40_km` |
| `tier_confidence` | `reduced` if either project is `endpoint_only`, otherwise `high` |

`tier_confidence` never changes `coordination_tier`.

---

## 6. Center-to-center distance

### 6.1 Project center

| Geometry | `center` |
|---|---|
| `endpoint_pair` | `lat = (lat_A + lat_B) / 2`, `lon = (lon_A + lon_B) / 2`. For a zero-length segment this is the single location |
| `endpoint_only` | The single known point |

\[
\text{center\_distance\_km} = \text{haversine}(\text{center}_{DESC}, \text{center}_{GPC})
\]

Center distance is **informational only**. It is never used for the gate, the tier, or the ranking.

### 6.2 Why center-to-center differs from closest-point

Center-to-center measures between two midpoints. Closest-point measures between the nearest parts of the two geometries. For two long lines whose nearest ends approach each other while their midpoints sit far apart, the center distance can be many times the closest-point distance. It can even exceed the 40 km gate while the lines are close enough to qualify.

Each center lies on its own geometry, because the segment midpoint at `t = 0.5` is exactly the arithmetic mean of the endpoints under the §2 segment definition. So closest-point distance is always less than or equal to center-to-center distance.

### 6.3 Concrete illustration: DESC_3 + GPC_2

**DESC_3 + GPC_2** is the required reference pair for this difference:

| Measure | What it describes for DESC_3 + GPC_2 | Used for |
|---|---|---|
| `center_distance_km` | Distance between the center of DESC_3 and the center of GPC_2 | Display only, as the secondary `Center-to-center` value |
| `closest_distance_km` | Distance between the nearest points of the two geometries, shown on the map by `closest_connector` | Gate, tier, ranking |

Required behavior:
- The engine must report both values for this pair.
- `center_distance_km` must be strictly greater than `closest_distance_km` for this pair.
- The pair qualifies and is tiered **only** on `closest_distance_km`.
- An engine that gated or tiered on center distance would misclassify pairs like this one. That is exactly the error this rule prevents.

The numbers for DESC_3 + GPC_2 are recorded in the golden fixture `backend/tests/fixtures/golden/opportunity_DESC_3__GPC_2.json`, which Agent 1 generates from the target dataset. This spec does not populate them.

---

## 7. Shared-endpoint detection

A shared endpoint means both filings name an endpoint that resolves to the same location. GridLock cannot confirm from public sources whether that is one shared site or separate facilities nearby. It is a distinct finding from a geometric crossing.

### 7.1 Algorithm

1. List the DESC project's known endpoints in order: `endpoint_a`, then `endpoint_b` if known.
2. List the GPC project's known endpoints in the same order.
3. Compare every DESC known endpoint with every GPC known endpoint, in this nested order: DESC `a` × GPC `a`, DESC `a` × GPC `b`, DESC `b` × GPC `a`, DESC `b` × GPC `b`. Skip any comparison involving an unknown endpoint.
4. The first comparison where the distance is `≤ SHARED_ENDPOINT_KM` (0.001 km) is the match.
5. If a match exists, set `shared_endpoint_detected = true`. Otherwise set it to `false` and `shared_endpoint_name = null`.

### 7.2 `shared_endpoint_name`

| Condition | Value |
|---|---|
| Matched labels are equal after trimming whitespace and case-folding | The DESC endpoint label, trimmed |
| Matched labels differ | `"<DESC endpoint label> / <GPC endpoint label>"`, each trimmed, otherwise verbatim |

No case normalization is applied to the output. Labels are copied from the dataset as published.

Example from the official dataset: DESC_2's known endpoint is labeled `Thurmond Sub`, and GPC_1's endpoint B is labeled `THURMOND DAM #5`, at identical coordinates. The labels differ after case-folding, so `shared_endpoint_name = "Thurmond Sub / THURMOND DAM #5"`. The mixed casing is preserved because it reflects two separate filings by two separate utilities.

### 7.3 Relationship to distance and tier

- Shared-endpoint detection does not replace the §5 closest-point computation. The engine still runs §5 and reports its `d` and closest points.
- A shared endpoint forces `d ≤ 0.001` km, so the tier is always `touching_crossing`.
- When `shared_endpoint_detected` is `true`, `coordination_tier_label` is `Endpoints published at the same coordinates`, not `Touching / crossing`.
- An approximately 0 km result is **valid output**. The API presents it as a proximity candidate from coincident published coordinates, not as an unqualified line crossing.
- When either project is `endpoint_only`, `tier_confidence` is `reduced` regardless of the shared endpoint.

---

## 8. Projection error and accuracy

§8.1–§8.4 describe the spherical model and are superseded by pending Revision 2.3 (see banner). §8.2 and §8.5 remain binding.

### 8.1 Where error can and cannot arise (spherical model)

| Part of the computation | Projection error |
|---|---|
| Segment definition | None. The segment is defined in latitude and longitude (§2) |
| Intersection test (§5.3 step 3) | None. The projection is affine in latitude and longitude, so intersection results do not depend on `φ₀` |
| Reported distance for a given closest point | None within the model. It is always haversine |
| Choice of the closest point `Q` on a segment (§5.2 step 5) | **Yes.** The planar perpendicular uses the east-west scale `cos φ₀` everywhere, while the true local scale is `cos φ` |

### 8.2 GA/SC validation box

| Bound | Value |
|---|---|
| Latitude | 30.3° to 35.3° N |
| Longitude | −85.7° to −78.5° |

This box contains Georgia and South Carolina. Endpoints outside it are still computed. They receive the `outside_ga_sc_extent` data warning, because the figures below do not apply to them.

### 8.3 Projection error internal to the spherical model

**Classification: projection error internal to the spherical model. Reference model: the spec's own sphere (haversine, R = 6371.0088 km). This is a self-consistency measurement, not an accuracy measurement. These are sample statistics, not proven bounds.**

Method: standalone script `docs/specs/tools/projection_error_mc.py`, seed 7 per population (each population has its own independent generator), numpy 1.26.4. Reference minimum from dense sampling of the §2 segment at 20,001 or 40,001 points.

| Population | Samples | Max relative error | 99th percentile | Max absolute error |
|---|---|---|---|---|
| Random point and segment anywhere in the GA/SC box, `d ≥ 0.5` km | 3,000 | 0.0577% | 0.0266% | 379.1 m (on distances of hundreds of km) |
| GA/SC box, `0.5 ≤ d < 40` km | 1,500 | 0.0104% | 0.0056% | 3.4 m |
| Continental US (lat 25° to 49° N, lon −125° to −67°) | 2,000 | 4.3658% | 1.2802% | 160.5 km |

Withdrawn figures (C-1): 0.014% / 2.4 m within 40 km and 4.96% / 205 km continental. Do not quote them anywhere.

### 8.4 Interpretation (spherical model only)

| Scale | Status | Reason |
|---|---|---|
| GA/SC extent | Internally consistent | Measured maximum 0.0577% against the model's own sphere |
| Within 40 km | Internally consistent | Measured maximum 0.0104%. At the 40 km gate that is about 4.2 m, at 8 km about 0.8 m, and at 1.6 km about 0.17 m |
| Continental scale | **Invalid** | Errors exceed 4% (measured maximum 4.37%). Do not use this engine for multi-region or continental datasets |

Tier boundaries are not adjusted for projection error. A pair is classified on its computed value.

### 8.5 Accuracy against WGS 84 (binding)

**Reference model: WGS 84 ellipsoid geodesic via `pyproj.Geod(ellps="WGS84")`. These are sample statistics, not proven bounds.**

Method: population `wgs84_model_error` in `docs/specs/tools/projection_error_mc.py`, seed 7, 4,000 random point pairs 0.5–40 km apart inside the GA/SC box, pyproj 3.7.1, numpy 1.26.4.

| Model | Error vs WGS 84 geodesic | Max absolute error |
|---|---|---|
| Spherical model (haversine, R = 6371.0088 km) | −0.2232% to +0.3060% | 115.7 m |
| UTM 17N planar distance (EPSG:32617), the PR #8 method | −0.0400% to +0.2252% | 85.7 m |
| UTM 17N, SC/GA border subregion (lat 32°–34° N, lon −82.5° to −80.5°) | −0.0400% to −0.0115% | — |

Two non-fixture official pairs, nine decimals, closest-point distance in km:

| Pair | UTM 17N planar (PR #8 method) | Spherical model | WGS 84 geodesic between spherical-model closest points |
|---|---|---|---|
| DESC_1 + GPC_1 | 11.082604858 | 11.063667012 | 11.085586625 |
| DESC_5 + GPC_3 | 14.224941192 | 14.202485708 | — |

**Materiality.** The six qualifying official pairs have PR #8 closest-point distances of 0.000, 4.816, 5.466, 11.083, 13.574, and 14.225 km (published in PR #8's `docs/OFFICIAL_DATASET_ENGINE.md`). The 0.000 km pair has identical coordinates and is 0 under every model. For the other five, the nearest tier boundary is at least 27.8% away (11.083 km versus the 8.0 km boundary), about 80 times the largest measured model error. No model tested changes any qualifying pair or tier.

**The only authorized judge wording:**

> "Distances are closest-point, computed from published endpoint coordinates. Against a WGS 84 geodesic reference, model error within 40 km is under 0.35% (about 120 m at most). No tier assignment or qualifying pair changes under any of the models we tested."

Never quote the error figure without the final sentence. The earlier sentence "Within 40 km, measured error is under 0.02% and under 5 m" is withdrawn. It described §8.3 self-consistency, not accuracy.

---

## 9. Rounding and unit conversion

| Step | Rule |
|---|---|
| Calculation | Full `float64` precision throughout |
| Gate and tier | Evaluated on the full-precision km value |
| Ranking | Sorted on the full-precision km value |
| km → mi | `mi_full = km_full / 1.609344`, computed from the full-precision km value |
| Serialization of distances | Convert the full-precision value to `Decimal(repr(value))`, then quantize to `0.001` with `ROUND_HALF_UP` |
| Serialization of coordinates | Same method, quantized to `0.000001` with `ROUND_HALF_UP` |
| Forbidden | Converting a rounded km value to miles. Rounding before gating or tiering. Using Python's built-in `round()` for serialization |

Conversion reference:

| km | mi (from 1.609344) |
|---|---|
| 1.609344 | 1.000 |
| 1.6 | 0.994 |
| 8.0 | 4.971 |
| 40.0 | 24.855 |

The "1 mi", "5 mi", and "25 mi" tier labels are rounded public labels. Gating always uses the km constants in §1.

---

## 10. Numerical edge cases

| Case | Required behavior |
|---|---|
| Identical points (point-to-point) | `d = 0`, tier `touching_crossing`. Both closest points equal the shared point. Shared-endpoint detection applies |
| Point exactly on a segment | §5.2 gives `d = 0` up to floating-point noise, because the planar foot of a point on the segment is the point itself. Tier `touching_crossing` |
| Zero-length segment in source (`A = B`) | **Valid.** Project keeps `geometry_confidence = endpoint_pair`, `is_zero_length_segment = true`, warning `zero_length_segment`. Computed as the single location `A` (§5.2 step 4, §5.3 pre-check). Never `503` |
| Near-zero projected length (`L² < EPS_LEN2_KM2`) | Treated as the single location `a` |
| Shared endpoint | `d ≤ 0.001`, tier `touching_crossing`, `shared_endpoint_detected = true` (§7) |
| Parallel non-overlapping segments | Intersection test fails. §5.3 step 5 finds the endpoint-based minimum |
| Collinear overlapping segments | Intersection test passes via collinear contact. `d = 0`, tier `touching_crossing` |
| T-junction (endpoint touches the other segment's interior) | Collinear contact at one `oᵢ = 0`. `d = 0`, tier `touching_crossing` |
| Haversine `a` slightly outside `[0, 1]` | Clamp before `sqrt` |
| Candidate ties in §5.3 step 6 | First candidate in table order wins |
| Distance within floating-point noise of a tier boundary | Compare the raw `float64` value with the strict inequalities in §1. No tolerance except `TIER_TOUCH_KM` |
| Endpoint coordinate non-numeric, `NaN`, infinite, or outside WGS 84 range | The endpoint is treated as unknown, with warning `invalid_coordinate_treated_as_unknown`. If that leaves no known endpoint, the load fails with `503`, `reason = "no_known_endpoint"` |
| Endpoint outside the GA/SC validation box | Computed normally, with warning `outside_ga_sc_extent` |
| Antimeridian crossing | **Out of scope.** Cannot occur inside the GA/SC validation box. The engine contains no antimeridian handling |
| Poles | **Out of scope.** Cannot occur inside the GA/SC validation box. The engine contains no polar handling |

---

## 11. Reference test vectors

These vectors use synthetic coordinates chosen for math verification only. They are not project locations. Coordinates are `(lat, lon)` in degrees. Expected values use the spherical model (`EARTH_RADIUS_KM = 6371.0088`); numeric values are superseded by pending Revision 2.3, while the expected flags, closest-point identities, and candidate choices remain binding.

| # | Case | Inputs | Expected `d` (km, 6 dp) | Expected `d` (mi, 6 dp) | Expected closest points and flags |
|---|---|---|---|---|---|
| V1 | Point-to-point, 1° longitude at equator | `(0, 0)`, `(0, 1)` | `111.195080` | `69.093420` | The two inputs |
| V2 | Point-to-point, 1° latitude | `(0, 0)`, `(1, 0)` | `111.195080` | `69.093420` | The two inputs |
| V3 | Point-to-segment, interior foot | `P = (0.5, 0.5)`, `A = (0, 0)`, `B = (0, 1)` | `55.597540` | `34.546710` | `P`, `Q = (0, 0.5)` |
| V4 | Point-to-segment, clamped to `B` (`t > 1`) | `P = (0, 2)`, `A = (0, 0)`, `B = (0, 1)` | `111.195080` | `69.093420` | `P`, `Q = B = (0, 1)` |
| V5 | Point-to-point, 0.1° longitude at 33° N | `(33.0, -81.0)`, `(33.0, -80.9)` | `9.325604` | `5.794662` | The two inputs |
| V6 | Point-to-point, 0.1° latitude | `(33.0, -81.0)`, `(33.1, -81.0)` | `11.119508` | `6.909342` | The two inputs |
| V7 | Segment-to-segment, proper crossing | DESC `(-0.5, 0) → (0.5, 0)`, GPC `(0, -0.5) → (0, 0.5)` | `0.000000` | `0.000000` | Both `(0, 0)`; tier `touching_crossing`; `shared_endpoint_detected = false` |
| V8 | Segment-to-segment, endpoint candidate wins | DESC `(0, 0) → (0, 1)`, GPC `(0.1, 0.5) → (0.2, 0.5)` | `11.119508` | `6.909342` | DESC `(0, 0.5)`, GPC `(0.1, 0.5)`; candidate 3 |
| V9 | Identical points | `(33.0, -81.0)`, `(33.0, -81.0)` | `0.000000` | `0.000000` | Both `(33.0, -81.0)`; tier `touching_crossing`; `shared_endpoint_detected = true` |
| V10 | Zero-length segment to point | DESC segment `(0, 0) → (0, 0)`, GPC point `(0, 1)` | `111.195080` | `69.093420` | DESC `(0, 0)`, GPC `(0, 1)`; `distance_basis = point_to_segment`; no error |
| V11 | Shared endpoint, point to segment end | DESC point `(33.0, -81.0)` labeled `Alpha`; GPC segment `(33.1, -81.0) → (33.0, -81.0)`, endpoint B labeled `Alpha Dam` | `0.000000` | `0.000000` | `shared_endpoint_detected = true`, `shared_endpoint_name = "Alpha / Alpha Dam"`, tier `touching_crossing`, label `Endpoints published at the same coordinates`, `tier_confidence = reduced` |
| V12 | Shared endpoint, equal labels | DESC point `(33.0, -81.0)` labeled `Beta`; GPC point `(33.0, -81.0)` labeled ` beta ` | `0.000000` | `0.000000` | `shared_endpoint_name = "Beta"` |

Tier boundary vectors, applied directly to the tier function with full-precision inputs (binding):

| Input `d` (km) | Expected tier |
|---|---|
| `0.0` | `touching_crossing` |
| `0.001` | `touching_crossing` |
| `0.0010001` | `under_1_6_km` |
| `1.5999999` | `under_1_6_km` |
| `1.6` | `under_8_km` |
| `7.9999999` | `under_8_km` |
| `8.0` | `under_40_km` |
| `39.9999999` | `under_40_km` |
| `40.0` | Not an opportunity |

---

## Acceptance checks

A QA agent must run all of these as unit tests against the engine module, with no network access. Numeric thresholds in checks marked † inherit the §3–§8 superseded status and will be restated in Revision 2.3.

| # | Check | Pass condition |
|---|---|---|
| G1 † | Constants | All §1 constants equal the stated values |
| G2 † | Haversine vectors | V1, V2, V5, V6, V9 match within `1e-6` km |
| G3 † | Point-to-segment interior | V3 matches within `1e-6` km and the closest point equals `(0, 0.5)` within `1e-9` degrees |
| G4 † | Clamping | V4 returns `Q = B` with `t` clamped to `1`. The mirrored case `P = (0, -1)` returns `Q = A` |
| G5 † | Crossing | V7 returns `d == 0`, both closest points `(0, 0)`, tier `touching_crossing`, no shared endpoint |
| G6 † | Endpoint candidate | V8 returns `11.119508` km, selects candidate 3, and returns the stated closest points |
| G7 | Zero-length segment | V10 computes with no exception, no `503`, and `is_zero_length_segment = true` on the project |
| G8 | Shared endpoint | V9, V11, V12 return the stated `shared_endpoint_detected`, `shared_endpoint_name`, tier, label, and `tier_confidence` |
| G9 | Shared endpoint order | When two matches exist, the first match in §7.1 nested order sets the name |
| G10 | Tier boundaries | Every row of the tier boundary table returns the expected tier |
| G11 | Tier confidence | `tier_confidence` is `reduced` for every pair with an `endpoint_only` side and `high` otherwise |
| G12 † | Distance consistency | For every real opportunity, the model distance between the unrounded closest points equals unrounded `closest_distance_km` within `1e-9` km |
| G13 | Center ≥ closest | For every real opportunity, `center_distance_km_full >= closest_distance_km_full − 1e-9` |
| G14 | DESC_3 + GPC_2 | `center_distance_km > closest_distance_km`, gate and tier use `closest_distance_km`, values equal `opportunity_DESC_3__GPC_2.json` |
| G15 | DESC_2 + GPC_1 | `closest_distance_km <= 0.001`, `shared_endpoint_detected = true`, `shared_endpoint_name = "Thurmond Sub / THURMOND DAM #5"`, `tier_confidence = reduced` |
| G16 † | Projection bound, GA/SC | `python3 docs/specs/tools/projection_error_mc.py` under the pinned environment reproduces §8.3 exactly, and `ga_sc_all.max_rel_pct < 0.5` |
| G17 † | Projection bound, 40 km | Same run: `ga_sc_within_40km.max_rel_pct < 0.5` and `max_abs_m < 10` |
| G18 † | Intersection independence | V7 and a collinear-contact case give identical intersection results with `φ₀` forced to 0°, 33°, and 60° |
| G19 | Mile conversion | `closest_distance_mi` equals `HALF_UP(km_full / 1.609344, 3)`, never `HALF_UP(HALF_UP(km_full, 3) / 1.609344, 3)` |
| G20 | Rounding mode | A value of `2.0005` km serializes as `2.001` |
| G21 | Dispatch | All four rows of §5.4 route to the stated method and `distance_basis` |
| G22 † | Shared φ₀ | Segment-to-segment sub-computations use the 4-position mean latitude |
| G23 | Invalid coordinate | An endpoint with `NaN` becomes unknown with warning `invalid_coordinate_treated_as_unknown`. If both endpoints are invalid, load fails with `no_known_endpoint` |
| G24 | Extent warning | An endpoint at `(40.0, -75.0)` computes normally and carries warning `outside_ga_sc_extent` |
| G25 | Determinism | Running the engine twice on the target dataset produces identical full-precision outputs |
| G26 | Reference-sheet independence | No constant, tolerance, or formula branch references a reference sheet, a pair ID, or an expected result |
