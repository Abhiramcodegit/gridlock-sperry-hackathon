STATUS: TARGET SPECIFICATION — NOT IMPLEMENTED. As of origin/main 1c31e2e6efc72599317de739f98ec55bcb6f6417, neither the engine nor the UI implements the behavior below. Target dataset: data/official/projects_official.json (PR #8, not on main). Implementing it requires the unassigned integration PR for the engine and a frontend pass by Agent 2. No agent may describe this behavior as live until both merge and acceptance checks C1–C41 pass.

# GridLock Edge Cases

**Path:** `docs/specs/EDGE_CASES.md`
**Status:** Target specification for backend, frontend, and QA agents. Revision 2.2.1
**Scope:** Every ambiguous input or output case and its single required behavior

Companion specs:
- `docs/specs/API_CONTRACT.md` defines fields, enums, error codes, and frontend consumption rules.
- `docs/specs/GEOMETRY_MATH.md` defines every calculation, including shared-endpoint detection and the accuracy record. Its §3–§8 distance model is superseded by pending Revision 2.3; see that file's banner.

Every case below has exactly one required behavior. If a case is not listed here, the agent must stop and escalate. It must not choose a behavior on its own.

### Revision history

| Rev | # | Change |
|---|---|---|
| 2 | R1 | Added shared-endpoint findings, with DESC_2 + GPC_1 as the reference case (§3) |
| 2 | R2 | `endpoint_only` and zero-length segments are valid and never `503`. Four of ten official projects are `endpoint_only` |
| 2 | R3 | `503` is reserved for exactly three reasons (§1.1) |
| 2 | R4 | Empty and invalid endpoint values become unknown endpoints with a data warning instead of failing the load |
| 2 | R5 | Added projection-error boundary behavior (E30) |
| 2.1 | R6 | Payload `coordination_tier_label` is the only tier display text. The UI never derives a label from the `coordination_tier` string value (E35, §3.3, X19) |
| 2.1 | R7 | `shared_endpoint_name` is one concatenated field, never split client-side. Binding shared-endpoint headline and callout copy (§3.3, X20) |
| 2.2 | R8 | Line-one STATUS block: this file describes target engine and UI behavior that is not implemented |
| 2.2 | R9 | Rule wording now describes string-value comparison, not enum mapping. JavaScript has no enums (E35, §3.3, X19, C40) |
| 2.2 | R10 | DESC_2 + GPC_1 `shared_endpoint_name` changed to the verbatim dataset string `Thurmond Sub / THURMOND DAM #5`. The earlier value `Thurmond / Thurmond Dam #5` is withdrawn because the official dataset contradicts it (§3.4) |
| 2.2 | R11 | Target dataset is `data/official/projects_official.json`. It counts as approved only after PR #8 clears audit and merges. The approved-only rule and the 40 km threshold are unchanged |
| 2.2 | R12 | References to an uncommitted copy document replaced with "any other specification" (E35) |
| 2.2 | R13 | The withdrawn Monte Carlo figures (0.014% / 2.4 m; 4.96% / 205 km) must not appear in any UI copy or document. Reproducible figures and their reference models are in `GEOMETRY_MATH.md` §8.3 and §8.5 |
| 2.2.1 | R14 | Copy: shared-endpoint label value changed to `Endpoints published at the same coordinates`; headline changed to `Proximity candidate: endpoints published at the same coordinates` with a separate name line; callout unchanged (§3.2–§3.4, C14, C16). Empty-state headings changed: §8.1 `No cross-utility opportunities found` → `No cross-utility reference candidates found`; §8.2 `No coordination opportunities for <project_id>` → `No reference candidates for <project_id>` (bodies unchanged); new §8.4 approved-result empty state `No approved coordination opportunities yet`. Field names and logic unchanged |
| 2.2.1 | R15 | Coordinate-derived reference candidates are not approved results. They are served only by `GET /reference/opportunities`. Six-pair assertions, empty states (§8.1, §8.2, new §8.4), and C-rows retargeted per `API_CONTRACT.md` R20 |

---

## 1. Master edge-case table

| # | Case | Required behavior |
|---|---|---|
| E1 | Source endpoint value is `none` (trimmed, case-insensitive) | Endpoint is unknown. `known: false`, `location: null`, `label: "none"` |
| E2 | Source endpoint value is empty or whitespace | Endpoint is unknown, exactly as E1. Add warning `empty_endpoint_value_treated_as_unknown`. Not an error |
| E3 | Source endpoint coordinate is non-numeric, `NaN`, infinite, or outside WGS 84 range | Endpoint is unknown, exactly as E1. Add warning `invalid_coordinate_treated_as_unknown`. Not an error |
| E4 | Exactly one endpoint known after E1–E3 | Valid. `geometry_confidence: "endpoint_only"`, `geometry.type: "Point"`. Never `503` |
| E5 | Neither endpoint known after E1–E3 | `503 data_unavailable`, `details.reason = "no_known_endpoint"`, `details.project_id` set. Never invent a location |
| E6 | `endpoint_only` project whose known endpoint is listed second in the source | Normalize: the known endpoint becomes `endpoint_a`, the unknown becomes `endpoint_b` |
| E7 | `endpoint_pair` endpoint order | Preserve source order: the source's first endpoint is `endpoint_a` |
| E8 | Both endpoints known with identical coordinates (zero-length segment) | Valid. `geometry_confidence: "endpoint_pair"`, `is_zero_length_segment: true`, warning `zero_length_segment`. Computed as a single location. Never `503` |
| E9 | Same-utility pair (DESC–DESC or GPC–GPC) | Never evaluated, never returned. See §4 |
| E10 | Self-pair (a project with itself) | Never evaluated, never returned |
| E11 | Pair order | Each cross-utility pair is evaluated once, with DESC first. `opportunity_id = "<DESC_x>__<GPC_y>"` |
| E12 | `closest_distance_km` exactly `40.0` | Not an opportunity. The gate is strict `< 40.0` |
| E13 | `closest_distance_km` below `40.0` but serializes as `40.000` (e.g., `39.9996`) | Qualifies, tier `under_40_km`, displayed as `40.000`. The UI must not re-evaluate it |
| E14 | Distance exactly on a tier boundary (`1.6`, `8.0`) | Belongs to the next-larger tier: `1.6` → `under_8_km`, `8.0` → `under_40_km` |
| E15 | Distance `≤ 0.001` km without a shared endpoint | Tier `touching_crossing`. The backend emits `coordination_tier_label: "Touching / crossing"` |
| E16 | Known DESC endpoint and known GPC endpoint within `0.001` km | Shared-endpoint finding. See §3 |
| E17 | Distance of `0.000` km | Valid output. Never filtered, clamped, hidden, or flagged as an error |
| E18 | Either project `endpoint_only` | `tier_confidence: "reduced"`. Tier is unchanged |
| E19 | Tie in distance ranking | Deterministic three-key sort. See §5 |
| E20 | In-service date missing in the official source | `in_service_date: null`. Any pair using it has `date_gap_days: null` and `date_gap_days_signed: null`. The pair still qualifies on distance |
| E21 | Non-null in-service date that is not a valid strict `YYYY-MM-DD` date (including partial dates) | `503 data_unavailable`, `details.reason = "unparseable_in_service_date"`, with `project_id` and `value` |
| E22 | Very large date gap on a qualifying pair | Pair still qualifies, tier unchanged. See §7 |
| E23 | Pair qualifies on distance with dates in either order | Qualifies. `date_gap_days` is absolute. `date_gap_days_signed` carries direction |
| E24 | Zero opportunities overall | Zero results on either route: `200`, `API_CONTRACT.md` §5.2 envelope, `data: []`. UI shows §8.1 for reference candidates, §8.4 for approved results |
| E25 | Zero opportunities for one project (`DESC_4`, `GPC_4`, `GPC_5`) | `200`, `data: []` from `GET /reference/opportunities?project_id=…`. UI shows §8.2 |
| E26 | `project_id` query value in the wrong case (e.g., `desc_1`) | `400 invalid_project_id`. IDs are case-sensitive |
| E27 | Approved dataset does not contain exactly 10 records with exactly the official `project_id` set (including duplicates) | `503 data_unavailable`, `details.reason = "dataset_project_count_mismatch"`, `expected: 10`, `found: <integer>`. Never serve partial data |
| E28 | Endpoint outside the GA/SC validation box | Computed normally. Warning `outside_ga_sc_extent`. Not an error |
| E29 | Engine output differs from the expected six pairs | Engine or data defect. Do not change constants, tolerances, or formulas. See §10 |
| E30 | Exact distance within the model-error margin of a tier boundary | Classify on the computed full-precision value. No compensation. Model-error figures and their reference models are in `GEOMETRY_MATH.md` §8.3–§8.5 |
| E31 | Center distance at or above 40 km but closest-point distance under 40 km | Qualifies. The gate uses closest-point distance only |
| E32 | Center distance under closest-point distance | Impossible by construction. If the engine produces it, fail the engine test suite |
| E33 | Coordinate with more than 6 decimals in source | Keep full precision internally. Round to 6 only in responses |
| E34 | Outbound network unavailable at runtime | No effect. The backend has no runtime external calls |
| E35 | Any other specification maps `coordination_tier` string values to display text | The payload `coordination_tier_label` wins. The UI renders it as-is and never derives a label from the `coordination_tier` value |
| E36 | `shared_endpoint_name` contains `/` or other separators | Rendered as one unchanged string. Never split, trimmed, reordered, or reformatted client-side |

### 1.1 `503` is reserved for exactly three reasons

| `details.reason` | Trigger |
|---|---|
| `dataset_project_count_mismatch` | Record count ≠ 10, or the `project_id` set ≠ the ten official IDs |
| `unparseable_in_service_date` | A non-null in-service date is not a valid strict `YYYY-MM-DD` date |
| `no_known_endpoint` | A project has neither endpoint known |

Everything else in this file is valid data or a non-503 response. In particular, `endpoint_only` projects, zero-length segments, empty or invalid endpoint values that leave one known endpoint, out-of-box coordinates, and 0 km distances never produce `503`.

---

## 2. `endpoint_only` geometry

Four of the ten official projects are `endpoint_only`: DESC_1, DESC_2, DESC_4, and GPC_2. This is normal data.

### 2.1 How distance is computed

| Pair geometry | Method | `distance_basis` |
|---|---|---|
| `endpoint_only` + `endpoint_pair` | Point-to-segment from the one known endpoint to the other project's segment (`GEOMETRY_MATH.md` §5.2) | `point_to_segment` |
| `endpoint_only` + `endpoint_only` | Distance between the two known endpoints (`GEOMETRY_MATH.md` §5.1) | `point_to_point` |

The missing endpoint contributes nothing. The engine never extends the line, projects a direction, uses a county centroid, or substitutes any other location.

### 2.2 How it is labeled

| Field or UI element | Required value |
|---|---|
| Project `geometry_confidence` | `"endpoint_only"` |
| Project `geometry.type` | `"Point"` |
| Opportunity `pair_geometry_confidence` | `"mixed"` or `"both_endpoint_only"` |
| Opportunity `is_endpoint_only_estimate` | `true` |
| Opportunity `tier_confidence` | `"reduced"` |
| Map marker badge | `Endpoint only — route unknown` |
| Distance note | `Distance measured to the one known endpoint` |
| Tier badge | `Reduced confidence` |

### 2.3 Why the confidence is reduced

A true line through the missing endpoint could pass closer to or farther from the other project than the one known endpoint does. The reported distance is therefore an estimate. The tool still includes or excludes the pair strictly on that estimate, and `tier_confidence: "reduced"` plus the labels above make the limitation visible. Do not widen or narrow the gate for `endpoint_only` pairs.

---

## 3. Shared-endpoint findings

### 3.1 Definition

A shared endpoint exists when a known DESC endpoint and a known GPC endpoint are within `0.001` km of each other (`GEOMETRY_MATH.md` §7). It means both filings name an endpoint that resolves to the same location.

### 3.2 Required output

| Field | Required value |
|---|---|
| `shared_endpoint_detected` | `true` |
| `shared_endpoint_name` | One concatenated string per `GEOMETRY_MATH.md` §7.2, built from dataset labels verbatim |
| `closest_distance_km` | `≤ 0.001`, often `0.000`. Valid output |
| `coordination_tier` | `touching_crossing` |
| `coordination_tier_label` | `Endpoints published at the same coordinates` |
| `tier_confidence` | `reduced` if either project is `endpoint_only`, otherwise `high` |

### 3.3 Required presentation

A shared-endpoint result is a **proximity candidate from coincident published coordinates, not an unqualified crossing**. The copy below is binding. Replace `{shared_endpoint_name}` with the payload value exactly as returned.

| UI element | Required content |
|---|---|
| Headline | `Proximity candidate: endpoints published at the same coordinates` |
| Name line | `{shared_endpoint_name}` |
| Callout body | `Both filings name an endpoint that resolves to the same location, published as {shared_endpoint_name}. GridLock cannot confirm from public sources whether these are one shared site or separate facilities nearby. Both utilities would need to confirm.` |
| Tier text | The payload `coordination_tier_label`, which is `Endpoints published at the same coordinates` |
| Forbidden wording | `Crossing`, `Lines cross`, `Intersection`, `Touching / crossing`, `Touching or crossing` |
| Map | A single marker at the shared location. No connector line |

Label and name rules:
- The UI renders tier text only from `coordination_tier_label`. It never derives a label from the `coordination_tier` string value. The value `touching_crossing` is used for both crossings and shared endpoints, so deriving a label from it would put `Touching or crossing` on this finding.
- The UI never splits `shared_endpoint_name`. There are no per-utility name fields to reconstruct, and the slash form is intended to read as a single published name.

### 3.4 Reference case: DESC_2 + GPC_1

In the official dataset, DESC_2 is `endpoint_only` with its known endpoint labeled `Thurmond Sub`. GPC_1 has two known endpoints (`endpoint_pair`), and its endpoint B is labeled `THURMOND DAM #5`, at the same coordinates. The pair collides at approximately 0 km.

| Field | Required value |
|---|---|
| `closest_distance_km` | `≤ 0.001`, exact value from the golden fixture |
| `coordination_tier` | `touching_crossing` |
| `coordination_tier_label` | `Endpoints published at the same coordinates` |
| `shared_endpoint_detected` | `true` |
| `shared_endpoint_name` | `Thurmond Sub / THURMOND DAM #5` |
| `tier_confidence` | `reduced` (DESC_2 is `endpoint_only`) |
| `distance_basis` | `point_to_segment` |
| `pair_geometry_confidence` | `mixed` |
| `is_endpoint_only_estimate` | `true` |
| `date_gap_days` | `3074` |

Rendered copy for this pair:

| UI element | Rendered text |
|---|---|
| Headline | `Proximity candidate: endpoints published at the same coordinates` |
| Name line | `Thurmond Sub / THURMOND DAM #5` |
| Callout body | `Both filings name an endpoint that resolves to the same location, published as Thurmond Sub / THURMOND DAM #5. GridLock cannot confirm from public sources whether these are one shared site or separate facilities nearby. Both utilities would need to confirm.` |

The mixed casing is preserved deliberately. It reflects two separate filings by two separate utilities. The approximately 0 km result is correct and expected. It must never be treated as a data error, a duplicate project, or a crossing.

---

## 4. Same-utility pairs

**Required behavior:** Exclude every DESC–DESC and GPC–GPC pair. Do not compute distances for them, return them, count them, or log them as opportunities.

**Rationale:**
- GridLock is a cross-utility coordination screening tool. Its purpose is to surface coordination opportunities between two different utilities that do not share an internal planning process.
- A single utility already coordinates its own projects internally. Surfacing same-utility pairs would add noise and dilute the cross-utility signal.
- The expected result set contains only DESC–GPC pairs.

Enforcement:
- The pair generator iterates only over the Cartesian product `DESC_* × GPC_*`, which is 25 pairs for the 10 official projects.
- The inclusion rule string is exactly `"closest_distance_km < 40.0 and utilities differ"`.

---

## 5. Ranking and tiebreak rule

Opportunities are sorted by these keys, in order:

| Priority | Key | Direction | Null handling |
|---|---|---|---|
| 1 | `closest_distance_km`, full `float64` precision | Ascending | Never null |
| 2 | `date_gap_days` (absolute) | Ascending | `null` sorts last |
| 3 | `opportunity_id` | Ascending, byte-wise (ASCII) comparison | Never null |

Rules:
- Two distances are equal for key 1 only when their `float64` values are exactly equal. Do not apply a tolerance to ranking.
- Multiple `touching_crossing` pairs with `d = 0`, including shared-endpoint findings, tie on key 1 and fall through to key 2, then key 3.
- `tier_confidence` and `shared_endpoint_detected` do not affect ranking.
- `rank` is 1-based and assigned after sorting the full unfiltered set.
- Filtering by `project_id` returns the subset with the original `rank` values, in rank order.
- Sorting must be stable and produce the same order on every run.

---

## 6. Date parsing

| Topic | Required behavior |
|---|---|
| Format in approved dataset | Strict ISO 8601 calendar date `YYYY-MM-DD`, zero-padded, e.g. `2027-06-01`, or `null` |
| Other source formats | Converted during the offline data-normalization step and reviewed into the approved dataset. The runtime backend accepts only `YYYY-MM-DD` or `null` |
| Partial official dates (year only, month-year, quarter, season) | Recorded as `null` in the approved dataset with a note in `data/VERIFICATION_LEDGER.md`. If a partial date string reaches the runtime, it is unparseable and triggers `503 unparseable_in_service_date` |
| Time component | None. Dates are pure calendar dates |
| Timezone policy | None applied. Dates are timezone-naive calendar dates. No conversion to UTC or local time, no DST handling |
| Calendar | Proleptic Gregorian |
| Signed gap | `date_gap_days_signed = gpc_in_service_date − desc_in_service_date`, in whole days. Positive means GPC is later |
| Absolute gap | `date_gap_days = abs(date_gap_days_signed)` |
| Which gap is displayed and ranked | Absolute `date_gap_days` |
| Missing date on either side | Both gap fields are `null` |
| Leap years | Standard calendar-date subtraction. No 365-day approximation |
| Derived units | Do not convert the gap to months or years in the API. The UI shows days |

---

## 7. Qualifying distance with a very large date gap

**Case:** DESC_2 + GPC_1 qualifies on closest-point distance and has an absolute date gap of **3074 days**. It is also a shared-endpoint finding (§3.4).

**Required behavior:**

| Item | Required value |
|---|---|
| Included in `GET /reference/opportunities` | Yes. In `GET /opportunities`: only after per-geometry human approval |
| `coordination_tier` | Determined only by `closest_distance_km`: `touching_crossing`. The date gap does not change it |
| `date_gap_days` | `3074` |
| Ranking effect | Date gap is used only as tiebreak key 2 in §5 |
| Filtering effect | None. There is no date-gap threshold |
| UI treatment | Show the gap as `3,074 days apart`, styled like any other gap. No warning color, no "weak" label, no demotion |

**Rationale:** The inclusion gate is geographic. The date gap is a secondary signal for planners, not a filter. Two projects years apart can still share a facility, corridors, access, or permitting knowledge, and the planner decides whether the timing matters.

---

## 8. Zero-opportunity UI states

### 8.1 Global empty state

Shown when unfiltered `GET /reference/opportunities` returns `data: []`.

| Element | Required content |
|---|---|
| Heading | `No cross-utility reference candidates found` |
| Body | `No DESC and Georgia Power project pair is within 40 km (25 mi) at its closest point.` |
| Map | Still renders all projects from `GET /projects`. No connectors |
| Styling | Neutral informational style, not error style |

### 8.2 Per-project empty state

Shown when a project is selected and `GET /reference/opportunities?project_id=<id>` returns `data: []`. With the official dataset this applies to `DESC_4`, `GPC_4`, and `GPC_5`.

| Element | Required content |
|---|---|
| Heading | `No reference candidates for <project_id>` |
| Body | `No project from the other utility is within 40 km (25 mi) of this project at its closest point.` |
| Map | Highlights the selected project. No connectors |
| Project panel | Shows `opportunity_count: 0` from `GET /projects` |
| Styling | Neutral informational style, not error style |

### 8.3 Error state

An error response is never shown as an empty state. On any non-2xx response, the UI shows `error.message` in error styling and does not show either empty state.

### 8.4 Approved-result empty state

Shown when `GET /opportunities` returns `data: []`. This is the current state while no geometry has completed per-geometry human approval.

| Element | Required content |
|---|---|
| Heading | `No approved coordination opportunities yet` |
| Body | `No project pair has completed per-geometry human approval. Coordinate-derived reference candidates are listed separately.` |
| Styling | Neutral informational style, not error style |

---

## 9. Forbidden behaviors

| # | Forbidden behavior |
|---|---|
| X1 | Calling Overpass, Nominatim, or any geocoding, routing, or map-feature service at runtime, from backend or frontend |
| X2 | Inventing, estimating, or substituting coordinates for any unknown endpoint, including centroids, county seats, substation-name lookups, or extrapolated lines |
| X3 | Changing constants, tolerances, Earth radius, projection, thresholds, or formulas to match a reference sheet or the expected pair list |
| X4 | Adding pair-specific or project-specific branches, overrides, or special cases to the engine |
| X5 | Gating, tiering, or ranking on center-to-center distance |
| X6 | Gating on miles, or on any rounded value |
| X7 | Computing distance, tier, tier confidence, shared-endpoint status, date gap, or unit conversion in the frontend |
| X8 | Hard-coding coordinates, distances, tiers, or expected results in frontend or engine code. Expected results may appear only in test assertions and golden fixtures |
| X9 | Returning same-utility or self pairs |
| X10 | Using a date gap to filter pairs or change tiers |
| X11 | Returning `503` for `endpoint_only` projects, zero-length segments, recoverable endpoint values, out-of-box coordinates, or 0 km distances |
| X12 | Serving partial data when one of the three `503` conditions exists |
| X13 | Presenting a shared-endpoint finding as a crossing |
| X14 | Hiding, clamping, or flagging a 0 km distance as an error |
| X15 | Using Python's built-in `round()` for serialized values |
| X16 | Including CEII fields, data, or dependencies |
| X17 | Showing an error state for an empty result, or an empty state for an error |
| X18 | Reusing this engine for continental or multi-region datasets without replacing the projection method |
| X19 | Deriving tier display text on the client from the `coordination_tier` string value, whether by object-literal map, `switch`/`case`, `if`/`else` or ternary comparison, or translation lookup |
| X20 | Splitting, parsing, reordering, or reformatting `shared_endpoint_name` on the client |

---

## 10. When results do not match expectations

If `GET /reference/opportunities` does not return exactly these six pairs:

`DESC_1__GPC_1`, `DESC_2__GPC_1`, `DESC_3__GPC_2`, `DESC_3__GPC_3`, `DESC_5__GPC_2`, `DESC_5__GPC_3`

or if `DESC_4`, `GPC_4`, or `GPC_5` appears in any opportunity, the required process is:

1. Fail the test suite. Do not ship.
2. Check the target dataset against its provenance record for transcription errors, swapped latitude and longitude, or longitude sign errors.
3. Check the engine against the `GEOMETRY_MATH.md` reference vectors.
4. Record the finding in `docs/QA_LOG.md`.
5. Correct only the proven defect, in data or code. Never adjust math to fit the expected list.

---

## Acceptance checks

A QA agent must run all of these. "Fixture" checks use the target dataset. "Synthetic" checks use purpose-built data under `backend/tests/fixtures/synthetic/`. Fixture checks on items (C13, C15, C16) apply to items from `GET /reference/opportunities`.

| # | Check | Data | Pass condition |
|---|---|---|---|
| C1 | Pair universe | fixture | Engine evaluates exactly 25 pairs, all DESC × GPC |
| C2 | No same-utility pairs | synthetic | Two DESC projects 0 km apart produce no opportunity |
| C3 | No self pairs | fixture | No `opportunity_id` has the same project on both sides |
| C4 | Expected set | fixture | The `opportunity_id` set from `GET /reference/opportunities` equals the six in §10 exactly |
| C5 | Zero projects | fixture | `opportunity_count == 0` for all projects (approved-only), and filtered `GET /reference/opportunities` calls for `DESC_4`, `GPC_4`, `GPC_5` return `data: []` |
| C6 | `endpoint_only` count | fixture | Exactly 4 projects are `endpoint_only` (DESC_1, DESC_2, DESC_4, GPC_2), and `/projects` returns `200` |
| C7 | `none` endpoint | synthetic | Endpoint `"None "` becomes `known: false`, `location: null`, `geometry.type == "Point"` |
| C8 | Empty endpoint | synthetic | Endpoint `""` with a known partner endpoint returns `200`, `endpoint_only`, warning `empty_endpoint_value_treated_as_unknown` |
| C9 | Invalid coordinate | synthetic | Endpoint latitude `NaN` with a known partner endpoint returns `200`, `endpoint_only`, warning `invalid_coordinate_treated_as_unknown` |
| C10 | Both endpoints missing | synthetic | Load fails with `503`, `reason == "no_known_endpoint"` |
| C11 | Zero-length segment | synthetic | Identical endpoints return `200`, `is_zero_length_segment == true`, warning `zero_length_segment`, and a correct distance |
| C12 | Endpoint normalization | synthetic | A project with an unknown first endpoint returns the known one as `endpoint_a` |
| C13 | `endpoint_only` labels | fixture | Every opportunity with an `endpoint_only` side has `is_endpoint_only_estimate == true` and `tier_confidence == "reduced"` |
| C14 | Shared endpoint | synthetic | Cross-utility projects sharing one endpoint return `≤ 0.001` km, `touching_crossing`, `shared_endpoint_detected == true`, label `Endpoints published at the same coordinates` |
| C15 | DESC_2 + GPC_1 | fixture | Item matches every row of the §3.4 field table |
| C16 | Shared-endpoint UI copy | fixture | The DESC_2 + GPC_1 card shows exactly the §3.4 rendered headline, name line, and callout body, one map marker, no connector, and none of the §3.3 forbidden wording |
| C17 | Zero distance display | fixture | A `0.000` km distance is shown as `0.000 km` with no error styling |
| C18 | 40 km boundary | synthetic | A pair at full-precision `40.0` km is excluded. A pair at `39.9996` km is included, tier `under_40_km`, serialized `40.000` |
| C19 | Tier boundaries | synthetic | Pairs at `1.6` and `8.0` km get `under_8_km` and `under_40_km` |
| C20 | Tiebreak | synthetic | Three pairs with identical `float64` distances sort by `date_gap_days` ascending, `null` last, then `opportunity_id` ascending |
| C21 | Stable ranking | fixture | Ten repeated calls to `GET /reference/opportunities` return identical order and `rank` values |
| C22 | Filtered ranks | fixture | Filtered `GET /reference/opportunities` responses keep the original `rank` values |
| C23 | Unparseable date | synthetic | `2027-6-1`, `06/01/2027`, and `2027` each fail load with `503`, `reason == "unparseable_in_service_date"` |
| C24 | Missing date | synthetic | A `null` date gives both gap fields `null` and the pair still qualifies |
| C25 | Signed vs absolute | synthetic | DESC `2030-01-01`, GPC `2029-12-31` gives `date_gap_days_signed == -1`, `date_gap_days == 1` |
| C26 | Leap year | synthetic | `2028-02-28` to `2028-03-01` gives a gap of `2` |
| C27 | Large gap | fixture | `DESC_2__GPC_1` is present in `GET /reference/opportunities` with `date_gap_days == 3074` and tier `touching_crossing` |
| C28 | Date gap never filters | synthetic | A pair at 1 km with a 20,000-day gap is included with tier `under_1_6_km` |
| C29 | Center vs closest gate | synthetic | A pair with center distance 60 km and closest distance 5 km is included with tier `under_8_km` |
| C30 | Dataset count | synthetic | A dataset with 9 records, 11 records, or a duplicate `project_id` returns `503`, `reason == "dataset_project_count_mismatch"` on all three routes |
| C31 | `503` scope | synthetic | A dataset containing only `endpoint_only` projects, zero-length segments, recoverable endpoint values, and out-of-box coordinates returns `200` |
| C32 | Case-sensitive IDs | fixture | `?project_id=desc_1` returns `400 invalid_project_id` |
| C33 | Global empty UI | synthetic | A dataset producing no reference candidates shows the exact §8.1 heading and body. An API state with no human-approved geometries shows the exact §8.4 heading and body. Neither uses error styling |
| C34 | Per-project empty UI | fixture | Selecting `GPC_5` shows the exact §8.2 heading and body |
| C35 | Error UI | synthetic | A forced `503` shows `error.message` and neither empty state |
| C36 | No runtime lookups | fixture | With outbound network blocked, backend and frontend work normally. A code search finds no Overpass or Nominatim URLs or clients outside offline data-pipeline scripts |
| C37 | No invented coordinates | fixture | Every response coordinate traces to a known endpoint in the target dataset or a computed closest point on a known geometry |
| C38 | No tuning | fixture | A code search finds no pair IDs, project IDs, or expected distances in engine source outside tests and fixtures |
| C39 | No CEII | fixture | No request, response, fixture, or log contains CEII fields or data |
| C40 | Tier label authority | synthetic | A stubbed payload with `coordination_tier = "touching_crossing"` and `coordination_tier_label = "QA-LABEL-SENTINEL"` renders `QA-LABEL-SENTINEL`, and all three `API_CONTRACT.md` A35 ripgrep searches return zero matches |
| C41 | No name splitting | synthetic | A stubbed `shared_endpoint_name = "A / B / C"` renders unchanged in both the headline and the callout body |
