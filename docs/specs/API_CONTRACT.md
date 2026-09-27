STATUS: TARGET CONTRACT — NOT IMPLEMENTED. As of origin/main 1c31e2e6efc72599317de739f98ec55bcb6f6417 (verified by P3 and P2), GET /opportunities returns an empty array from the conservative pipeline and emits none of the Revision 2.2 fields. Target dataset: data/official/projects_official.json (PR #8, not on main). Implementing this contract requires an integration PR, currently unassigned, that wires the official engine into backend/gridlock/api.py and implements every field, error, and rule below. No agent may describe this contract as live until that PR merges and acceptance checks A1–A38 pass.

# GridLock API Contract

**Path:** `docs/specs/API_CONTRACT.md`
**Status:** Target specification for backend and frontend agents. Revision 2.2
**Scope:** `GET /projects`, `GET /opportunities`, error responses, frontend consumption rules

Companion specs:
- `docs/specs/GEOMETRY_MATH.md` defines every distance, closest-point, shared-endpoint, and projection calculation. Its §3–§8 distance model is superseded by pending Revision 2.3 (WGS 84 geodesic reference); see that file's banner.
- `docs/specs/EDGE_CASES.md` defines required behavior for ambiguous cases.

If this file conflicts with a companion on that companion's topic, the companion controls. Geometry questions go to `GEOMETRY_MATH.md`. Behavioral edge cases go to `EDGE_CASES.md`.

**Tier label authority:** `coordination_tier_label` in this contract is the only source of tier display text. It overrides any mapping from `coordination_tier` string values to display text in any other specification.

### Revision history

| Rev | # | Change |
|---|---|---|
| 2 | R1 | Added `shared_endpoint_detected`, `shared_endpoint_name`, and `tier_confidence` to `Opportunity` |
| 2 | R2 | Added the `Shared endpoint facility` tier label for shared-endpoint findings |
| 2 | R3 | `endpoint_only` and zero-length segments are valid data and never cause `503` |
| 2 | R4 | `503 data_unavailable` is reserved for exactly three reasons |
| 2 | R5 | Added `is_zero_length_segment` and `data_warnings` to `Project` |
| 2 | R6 | Worked example updated for the DESC_2 + GPC_1 shared-endpoint finding. `«golden»` markers remain for fixture-bound numbers |
| 2.1 | R7 | Payload `coordination_tier_label` is authoritative. The UI must never derive a tier label from the `coordination_tier` string value (F21) |
| 2.1 | R8 | `shared_endpoint_name` is one concatenated field and is never split client-side. Binding shared-endpoint headline and callout copy (F12) |
| 2.2 | R9 | Line-one STATUS block: this contract describes target behavior that is not implemented |
| 2.2 | R10 | "String enum" defined as a JSON Schema closed set of strings. JavaScript has no enums; all rules now describe string-value comparison (§2, F21, A35, A37) |
| 2.2 | R11 | A35 replaced with three exact ripgrep searches for `.js`/`.jsx`/`.mjs`/`.cjs` |
| 2.2 | R12 | `shared_endpoint_name` for DESC_2 + GPC_1 changed to the verbatim dataset string `Thurmond Sub / THURMOND DAM #5`. The earlier value `Thurmond / Thurmond Dam #5` is withdrawn because the official dataset contradicts it |
| 2.2 | R13 | Target dataset changed to `data/official/projects_official.json`. `dataset_version` format updated. The approved-only rule and the 40 km threshold are unchanged (§4.4) |
| 2.2 | R14 | References to an uncommitted copy document replaced with "any other specification" |
| 2.2 | R15 | Added Appendix A, engine-to-contract mapping gaps (informational) |
| 2.2 | R16 | The Monte Carlo figures cited in earlier session handoffs (0.014% / 2.4 m; 4.96% / 205 km) are withdrawn project-wide as non-reproducible. Reproducible figures and their reference models are in `GEOMETRY_MATH.md` §8. This contract states no accuracy figures |

---

## 1. General rules

| Rule | Required behavior |
|---|---|
| Transport | HTTP/1.1 JSON over the backend base URL |
| Content type | `application/json; charset=utf-8` on every response, including errors |
| Methods | `GET` only. Any other method on these routes returns `405` |
| Authentication | None for the hackathon build |
| Field naming | `snake_case` everywhere |
| Coordinate order in scalar fields | `lat` and `lon` as separate named fields |
| Coordinate order in GeoJSON | `[lon, lat]` per RFC 7946 |
| Coordinate reference system | WGS 84 (EPSG:4326), decimal degrees |
| Coordinate precision in responses | 6 decimal places |
| Distance precision in responses | 3 decimal places |
| Rounding mode | `ROUND_HALF_UP` on the full-precision value (see `GEOMETRY_MATH.md` §9) |
| Dates | ISO 8601 calendar date `YYYY-MM-DD`, no time, no timezone |
| Distance units | Always two separate fields: `*_km` and `*_mi` |
| Unknown query parameters | Rejected with `400 invalid_query_parameter` |
| Response determinism | Identical input data must produce byte-identical JSON bodies, excluding `meta.generated_at` |
| External calls | None at runtime. No Overpass, no Nominatim, no geocoding, no tile-derived geometry |
| CEII | No CEII fields, values, or dependencies anywhere in the API |

---

## 2. Enumerations

In this contract, "string enum" is the JSON Schema term for a closed set of allowed JSON string values. It is not a language-level enum. The frontend is JavaScript (`.js`/`.jsx`), which has no enums.

### 2.1 `utility`

| Value | Meaning |
|---|---|
| `DESC` | Dominion Energy South Carolina |
| `GPC` | Georgia Power Company |

No other values are valid.

### 2.2 `project_id`

Exactly these ten values are valid:

| `project_id` | `utility` |
|---|---|
| `DESC_1` | `DESC` |
| `DESC_2` | `DESC` |
| `DESC_3` | `DESC` |
| `DESC_4` | `DESC` |
| `DESC_5` | `DESC` |
| `GPC_1` | `GPC` |
| `GPC_2` | `GPC` |
| `GPC_3` | `GPC` |
| `GPC_4` | `GPC` |
| `GPC_5` | `GPC` |

### 2.3 `geometry_confidence`

| Value | Meaning | Geometry type |
|---|---|---|
| `endpoint_pair` | Both endpoints are known. The project is modeled as a straight segment between them. A segment whose two endpoints are identical is a valid zero-length segment | GeoJSON `LineString` with exactly 2 positions (identical for zero-length) |
| `endpoint_only` | Exactly one endpoint is known. The other is missing in the source data | GeoJSON `Point` |

No other values are valid. `endpoint_pair` does **not** mean the true routed path is known. It means the model uses a straight line between the two known endpoints.

Both values are valid, normal data. Neither causes an error. In the official dataset, **4 of the 10 projects are `endpoint_only`**: `DESC_1`, `DESC_2`, `DESC_4`, and `GPC_2`. The official dataset spells the other value `two_endpoints`; the API emits `endpoint_pair` (see Appendix A).

### 2.4 `coordination_tier`

Tier is assigned from the full-precision `closest_distance_km`, never from a rounded value.

| Value | Condition on full-precision `closest_distance_km` (`d`) | Backend-emitted `coordination_tier_label` |
|---|---|---|
| `touching_crossing` | Geometries intersect, or `d <= 0.001` | `Touching / crossing`, or `Shared endpoint facility` when `shared_endpoint_detected` is `true` |
| `under_1_6_km` | `0.001 < d < 1.6` | `Under 1.6 km (1 mi)` |
| `under_8_km` | `1.6 <= d < 8.0` | `Under 8 km (5 mi)` |
| `under_40_km` | `8.0 <= d < 40.0` | `Under 40 km (25 mi)` |

A pair with `d >= 40.0` is **not an opportunity** and never appears in `GET /opportunities`.

A distance of `0.000` km, or any value within the touching tolerance, is **valid output**. It is not an error and must not be filtered, clamped, or flagged as suspicious.

The label column describes what the **backend** emits. The frontend never uses this table to build labels. The same `coordination_tier` string value, `touching_crossing`, is emitted with two different labels, so the label cannot be derived from the value. See F21.

### 2.5 `tier_confidence`

| Value | Condition |
|---|---|
| `high` | Both projects are `endpoint_pair` |
| `reduced` | At least one project is `endpoint_only` |

`tier_confidence` is always `reduced` when either project is `endpoint_only`. No other input changes it. It never changes `coordination_tier`.

### 2.6 `distance_basis`

| Value | Case |
|---|---|
| `point_to_point` | Both projects are `endpoint_only` |
| `point_to_segment` | One project is `endpoint_only`, the other is `endpoint_pair` |
| `segment_to_segment` | Both projects are `endpoint_pair` |

Zero-length segments keep the `distance_basis` of their `geometry_confidence`. The math handles the degenerate case (see `GEOMETRY_MATH.md` §5.2).

### 2.7 `pair_geometry_confidence`

| Value | Condition |
|---|---|
| `both_endpoint_pair` | Both projects are `endpoint_pair` |
| `mixed` | Exactly one project is `endpoint_only` |
| `both_endpoint_only` | Both projects are `endpoint_only` |

### 2.8 `data_warnings` values

| Value | Meaning |
|---|---|
| `empty_endpoint_value_treated_as_unknown` | A source endpoint was empty or whitespace and was treated as missing |
| `invalid_coordinate_treated_as_unknown` | A source endpoint had a non-numeric, `NaN`, infinite, or out-of-range coordinate and was treated as missing |
| `zero_length_segment` | Both endpoints are known and identical. The project is computed as a single location |
| `outside_ga_sc_extent` | A known endpoint lies outside the GA/SC validation box in `GEOMETRY_MATH.md` §8.2. Error figures for the GA/SC extent do not apply to pairs using it |

Warnings are informational. None of them causes an error response.

---

## 3. Shared object types

### 3.1 `LatLon`

| Field | Type | Units | Nullable | Example |
|---|---|---|---|---|
| `lat` | number | decimal degrees, WGS 84, range −90 to 90 | No | `33.123456` |
| `lon` | number | decimal degrees, WGS 84, range −180 to 180 | No | `-81.654321` |

### 3.2 `Endpoint`

| Field | Type | Units | Nullable | Example |
|---|---|---|---|---|
| `label` | string | — | No | `"Substation name from source"` |
| `known` | boolean | — | No | `true` |
| `location` | `LatLon` | — | Yes. `null` exactly when `known` is `false` | `{"lat": 33.123456, "lon": -81.654321}` |

When the source endpoint is missing (`none`, empty, or an invalid coordinate), the backend returns `label: "none"`, `known: false`, and `location: null`. It never replaces a missing endpoint with a centroid, county seat, geocode, or guess.

### 3.3 GeoJSON geometry

| Field | Type | Nullable | Rule |
|---|---|---|---|
| `type` | string enum `"LineString"` or `"Point"` | No | `LineString` if and only if `geometry_confidence = endpoint_pair`. `Point` if and only if `geometry_confidence = endpoint_only` |
| `coordinates` | array | No | `LineString`: `[[lon, lat], [lon, lat]]`, exactly 2 positions, identical for a zero-length segment. `Point`: `[lon, lat]` |

---

## 4. `GET /projects`

### 4.1 Request

| Item | Value |
|---|---|
| Method | `GET` |
| Path | `/projects` |
| Query parameters | None. Any query parameter returns `400 invalid_query_parameter` |
| Request body | None |

### 4.2 Success response: `200 OK`

| Field | Type | Nullable | Example |
|---|---|---|---|
| `data` | array of `Project` | No | See §4.3 |
| `meta` | `ProjectsMeta` | No | See §4.4 |

### 4.3 `Project`

| Field | Type | Units | Nullable | Example |
|---|---|---|---|---|
| `project_id` | string enum (§2.2) | — | No | `"DESC_2"` |
| `utility` | string enum (§2.1) | — | No | `"DESC"` |
| `utility_name` | string | — | No | `"Dominion Energy South Carolina"` |
| `project_name` | string | — | No | `"Name as published in the official project list"` |
| `in_service_date` | string `YYYY-MM-DD` | calendar date | Yes. `null` only if the official source gives no date | `"2027-06-01"` |
| `geometry_confidence` | string enum (§2.3) | — | No | `"endpoint_only"` |
| `is_zero_length_segment` | boolean | — | No. Always `false` for `endpoint_only` | `false` |
| `endpoint_a` | `Endpoint` | — | No | See §3.2 |
| `endpoint_b` | `Endpoint` | — | No | See §3.2 |
| `geometry` | GeoJSON geometry (§3.3) | degrees | No | `{"type": "Point", "coordinates": [-81.654321, 33.123456]}` |
| `center` | `LatLon` | degrees | No | `{"lat": 33.123456, "lon": -81.654321}` |
| `opportunity_count` | integer ≥ 0 | count | No | `1` |
| `data_warnings` | array of string enum (§2.8) | — | No. Empty array when none | `[]` |

Rules:
- For `endpoint_only`, `endpoint_a` is always the known endpoint and `endpoint_b` is always the missing endpoint (`known: false`).
- `center` is defined in `GEOMETRY_MATH.md` §6.1.
- `opportunity_count` must equal the number of items in `GET /opportunities` that include this project.
- `DESC_4`, `GPC_4`, and `GPC_5` must return `opportunity_count: 0`.
- Example values in this table show format only. They are not project data.

### 4.4 `ProjectsMeta`

| Field | Type | Units | Nullable | Example |
|---|---|---|---|---|
| `count` | integer | count | No | `10` |
| `endpoint_only_count` | integer | count | No | `4` |
| `dataset_version` | string, format `projects_official.json@<40-character git blob SHA>` | — | No | `"projects_official.json@0000000000000000000000000000000000000000"` |
| `generated_at` | string, ISO 8601 UTC timestamp | — | No | `"2026-09-27T05:33:00Z"` |

`count` must equal `10`. `endpoint_only_count` must equal `4` for the official dataset. The `dataset_version` example shows format only; the SHA is the git blob SHA of the served dataset file.

**Target dataset and the approved-only rule.** The target dataset is `data/official/projects_official.json`, added by PR #8. It counts as the approved dataset **only after PR #8 clears independent audit and merges**. Until then, no environment may serve it as approved. This path change does not relax the approved-only rule and does not change the 40 km threshold. `data/approved/projects_approved.geojson` belongs to the conservative pipeline and is not the target of this contract.

### 4.5 Ordering

`data` is ordered with all `DESC` projects by numeric suffix ascending, then all `GPC` projects by numeric suffix ascending:

`DESC_1, DESC_2, DESC_3, DESC_4, DESC_5, GPC_1, GPC_2, GPC_3, GPC_4, GPC_5`

---

## 5. `GET /opportunities`

### 5.1 Request

| Item | Value |
|---|---|
| Method | `GET` |
| Path | `/opportunities` |
| Request body | None |

Query parameters:

| Name | Type | Required | Rule |
|---|---|---|---|
| `project_id` | string enum (§2.2) | No | Returns only opportunities that include this project. Returned items keep their global `rank` values |

Any other query parameter returns `400 invalid_query_parameter`. An invalid `project_id` value returns `400 invalid_project_id`.

### 5.2 Success response: `200 OK`

| Field | Type | Nullable | Example |
|---|---|---|---|
| `data` | array of `Opportunity` | No. Empty array when there are none | See §5.3 |
| `meta` | `OpportunitiesMeta` | No | See §5.4 |

### 5.3 `Opportunity`

| Field | Type | Units | Nullable | Example |
|---|---|---|---|---|
| `opportunity_id` | string, format `<DESC project_id>__<GPC project_id>` | — | No | `"DESC_3__GPC_2"` |
| `rank` | integer ≥ 1 | position | No | `2` |
| `desc_project_id` | string enum, `DESC_*` only | — | No | `"DESC_3"` |
| `gpc_project_id` | string enum, `GPC_*` only | — | No | `"GPC_2"` |
| `closest_distance_km` | number, 3 decimals | kilometers | No | `4.217` |
| `closest_distance_mi` | number, 3 decimals | statute miles | No | `2.620` |
| `center_distance_km` | number, 3 decimals | kilometers | No | `9.842` |
| `center_distance_mi` | number, 3 decimals | statute miles | No | `6.116` |
| `coordination_tier` | string enum (§2.4) | — | No | `"under_8_km"` |
| `coordination_tier_label` | string, exact backend-emitted label from §2.4. The only tier display text | — | No | `"Under 8 km (5 mi)"` |
| `tier_confidence` | string enum (§2.5) | — | No | `"high"` |
| `shared_endpoint_detected` | boolean | — | No | `false` |
| `shared_endpoint_name` | string, a single concatenated value | — | Yes. `null` exactly when `shared_endpoint_detected` is `false` | `null` |
| `distance_basis` | string enum (§2.6) | — | No | `"segment_to_segment"` |
| `pair_geometry_confidence` | string enum (§2.7) | — | No | `"both_endpoint_pair"` |
| `desc_geometry_confidence` | string enum (§2.3) | — | No | `"endpoint_pair"` |
| `gpc_geometry_confidence` | string enum (§2.3) | — | No | `"endpoint_pair"` |
| `closest_point_desc` | `LatLon` | degrees | No | `{"lat": 33.201234, "lon": -81.912345}` |
| `closest_point_gpc` | `LatLon` | degrees | No | `{"lat": 33.221987, "lon": -81.955432}` |
| `closest_connector` | GeoJSON `LineString` | degrees | No | `{"type": "LineString", "coordinates": [[-81.912345, 33.201234], [-81.955432, 33.221987]]}` |
| `desc_in_service_date` | string `YYYY-MM-DD` | calendar date | Yes | `"2027-06-01"` |
| `gpc_in_service_date` | string `YYYY-MM-DD` | calendar date | Yes | `"2035-10-15"` |
| `date_gap_days` | integer ≥ 0 | days, absolute | Yes. `null` if either date is `null` | `3058` |
| `date_gap_days_signed` | integer | days, `gpc_in_service_date − desc_in_service_date` | Yes. `null` if either date is `null` | `3058` |
| `is_endpoint_only_estimate` | boolean | — | No | `false` |

Rules:
- `closest_connector.coordinates` is always `[[closest_point_desc.lon, closest_point_desc.lat], [closest_point_gpc.lon, closest_point_gpc.lat]]`, in that order.
- When the tier is `touching_crossing` because the geometries intersect or share an endpoint, `closest_point_desc` and `closest_point_gpc` may be identical, and `closest_connector` then has two identical positions.
- `is_endpoint_only_estimate` is `true` exactly when `pair_geometry_confidence` is `mixed` or `both_endpoint_only`.
- `tier_confidence` is `reduced` exactly when `is_endpoint_only_estimate` is `true`.
- `shared_endpoint_detected` and `shared_endpoint_name` follow `GEOMETRY_MATH.md` §7.
- `shared_endpoint_name` is one concatenated string built from dataset labels verbatim, for example `"Thurmond Sub / THURMOND DAM #5"`. The API has no separate per-utility name fields for it, and clients must never split it. The backend applies no case normalization.
- When `shared_endpoint_detected` is `true`, `coordination_tier` is `touching_crossing` and `coordination_tier_label` is exactly `Shared endpoint facility`.
- `closest_distance_mi` is converted from the full-precision km value and then rounded. It is never converted from the rounded km value.
- Example values in this table show format only. They are not project data.

### 5.4 `OpportunitiesMeta`

| Field | Type | Units | Nullable | Example |
|---|---|---|---|---|
| `count` | integer ≥ 0 | count, after filtering | No | `6` |
| `total_count` | integer ≥ 0 | count, before `project_id` filtering | No | `6` |
| `inclusion_threshold_km` | number | kilometers | No | `40.0` |
| `inclusion_threshold_mi_display` | integer | statute miles, display label only | No | `25` |
| `inclusion_rule` | string, exact constant | — | No | `"closest_distance_km < 40.0 and utilities differ"` |
| `ranking_rule` | string, exact constant | — | No | `"closest_distance_km asc, date_gap_days asc nulls last, opportunity_id asc"` |
| `filter_project_id` | string enum (§2.2) | — | Yes. `null` when no filter is used | `null` |
| `dataset_version` | string, format `projects_official.json@<40-character git blob SHA>`, same rules as §4.4 | — | No | `"projects_official.json@0000000000000000000000000000000000000000"` |
| `generated_at` | string, ISO 8601 UTC timestamp | — | No | `"2026-09-27T05:33:00Z"` |

`inclusion_threshold_mi_display` is the rounded public label "25 miles". The actual gate is always `inclusion_threshold_km = 40.0` (24.855 mi). The backend never gates on miles.

### 5.5 Ordering

`data` is sorted by the rule in `EDGE_CASES.md` §5:

1. `closest_distance_km` ascending, full precision
2. `date_gap_days` ascending, `null` last
3. `opportunity_id` ascending, byte-wise string comparison

`rank` is 1-based and assigned after sorting the full unfiltered set. Filtering by `project_id` does not renumber ranks.

### 5.6 Expected result set

With the official 10-project dataset, the unfiltered response must contain exactly these six `opportunity_id` values, in the order §5.5 produces:

| `opportunity_id` |
|---|
| `DESC_1__GPC_1` |
| `DESC_2__GPC_1` |
| `DESC_3__GPC_2` |
| `DESC_3__GPC_3` |
| `DESC_5__GPC_2` |
| `DESC_5__GPC_3` |

`DESC_4`, `GPC_4`, and `GPC_5` must not appear in any opportunity.

If the engine produces a different set, the engine or the data is wrong. Do not change thresholds, formulas, or constants to force this set. See `EDGE_CASES.md` §10.

---

## 6. Error responses

### 6.1 Error body shape

Every non-2xx response uses this body:

```json
{
  "error": {
    "code": "invalid_query_parameter",
    "message": "Unknown query parameter: tier",
    "http_status": 400,
    "details": {
      "parameter": "tier"
    }
  }
}
```

| Field | Type | Nullable | Rule |
|---|---|---|---|
| `error.code` | string enum (§6.2) | No | Machine-readable |
| `error.message` | string | No | Human-readable. Must not include stack traces, file paths, SQL, or environment values |
| `error.http_status` | integer | No | Equals the HTTP status code |
| `error.details` | object | No | `{}` when there are no details |

### 6.2 Error codes

| HTTP status | `error.code` | When |
|---|---|---|
| 400 | `invalid_query_parameter` | Any unknown query parameter on `/opportunities`, or any query parameter on `/projects` |
| 400 | `invalid_project_id` | `project_id` is not one of the 10 values in §2.2 |
| 404 | `not_found` | Unknown route |
| 405 | `method_not_allowed` | Any method other than `GET` on `/projects` or `/opportunities`. The response includes the header `Allow: GET` |
| 500 | `internal_error` | Unhandled server error |
| 503 | `data_unavailable` | Only the three reasons in §6.3 |

### 6.3 `503 data_unavailable` reasons

`503` is reserved for exactly these three conditions. Nothing else produces `503`.

| `details.reason` | Condition | Extra `details` fields |
|---|---|---|
| `dataset_project_count_mismatch` | The approved dataset does not contain exactly 10 records whose `project_id` values are exactly the set in §2.2 | `expected: 10`, `found: <integer>` |
| `unparseable_in_service_date` | A non-null `in_service_date` is not a valid strict `YYYY-MM-DD` calendar date | `project_id`, `value` |
| `no_known_endpoint` | A project has neither endpoint known after endpoint normalization | `project_id` |

These are explicitly **not** `503` conditions:
- `endpoint_only` projects
- Zero-length segments
- Empty or invalid endpoint values that leave at least one known endpoint
- Coordinates outside the GA/SC validation box
- Any distance value, including `0`

The backend must not serve partial data when a `503` condition exists.

---

## 7. Worked example: one real opportunity

This example uses the real qualifying pair **DESC_2 + GPC_1**. In the official dataset, DESC_2 is `endpoint_only` with its known endpoint labeled `Thurmond Sub`. GPC_1 has two known endpoints (`endpoint_pair`), and its endpoint B is labeled `THURMOND DAM #5`, at the same coordinates as DESC_2's known endpoint. The pair therefore collides at approximately 0 km. That is a **shared-facility finding**, not an unqualified line crossing. Its absolute date gap is **3074 days**.

Fields marked `«golden»` are bound to the committed golden fixture `backend/tests/fixtures/golden/opportunity_DESC_2__GPC_1.json`. Agent 1 generates that fixture from the target dataset after the distance-model ruling is implemented. This spec does not populate those values.

Request:

```http
GET /opportunities?project_id=GPC_1 HTTP/1.1
Accept: application/json
```

Response `200 OK`. Only the `DESC_2__GPC_1` item is shown. The live response also contains `DESC_1__GPC_1`, so its real `meta.count` is `2`.

```text
{
  "data": [
    {
      "opportunity_id": "DESC_2__GPC_1",
      "rank": «golden»,
      "desc_project_id": "DESC_2",
      "gpc_project_id": "GPC_1",
      "closest_distance_km": «golden»,
      "closest_distance_mi": «golden»,
      "center_distance_km": «golden»,
      "center_distance_mi": «golden»,
      "coordination_tier": "touching_crossing",
      "coordination_tier_label": "Shared endpoint facility",
      "tier_confidence": "reduced",
      "shared_endpoint_detected": true,
      "shared_endpoint_name": "Thurmond Sub / THURMOND DAM #5",
      "distance_basis": "point_to_segment",
      "pair_geometry_confidence": "mixed",
      "desc_geometry_confidence": "endpoint_only",
      "gpc_geometry_confidence": "endpoint_pair",
      "closest_point_desc": «golden»,
      "closest_point_gpc": «golden»,
      "closest_connector": «golden»,
      "desc_in_service_date": «golden»,
      "gpc_in_service_date": «golden»,
      "date_gap_days": 3074,
      "date_gap_days_signed": «golden»,
      "is_endpoint_only_estimate": true
    }
  ],
  "meta": {
    "count": 2,
    "total_count": 6,
    "inclusion_threshold_km": 40.0,
    "inclusion_threshold_mi_display": 25,
    "inclusion_rule": "closest_distance_km < 40.0 and utilities differ",
    "ranking_rule": "closest_distance_km asc, date_gap_days asc nulls last, opportunity_id asc",
    "filter_project_id": "GPC_1",
    "dataset_version": «golden»,
    "generated_at": "2026-09-27T05:33:00Z"
  }
}
```

Binding values that do not depend on fixture numbers:

| Field | Required value |
|---|---|
| `opportunity_id` | `"DESC_2__GPC_1"` |
| `desc_project_id` | `"DESC_2"` |
| `gpc_project_id` | `"GPC_1"` |
| `closest_distance_km` | `<= 0.001` |
| `coordination_tier` | `"touching_crossing"` |
| `coordination_tier_label` | `"Shared endpoint facility"` |
| `tier_confidence` | `"reduced"` |
| `shared_endpoint_detected` | `true` |
| `shared_endpoint_name` | `"Thurmond Sub / THURMOND DAM #5"` |
| `distance_basis` | `"point_to_segment"` |
| `pair_geometry_confidence` | `"mixed"` |
| `desc_geometry_confidence` | `"endpoint_only"` |
| `gpc_geometry_confidence` | `"endpoint_pair"` |
| `is_endpoint_only_estimate` | `true` |
| `date_gap_days` | `3074` |
| `meta.count` | `2` |
| `meta.total_count` | `6` |
| `meta.filter_project_id` | `"GPC_1"` |

Rendered UI for this item, per F12:

| Element | Rendered text |
|---|---|
| Headline | `Shared endpoint facility: Thurmond Sub / THURMOND DAM #5` |
| Callout body | `Both filings name an endpoint that resolves to the same location, published as Thurmond Sub / THURMOND DAM #5. GridLock cannot confirm from public sources whether these are one shared site or separate facilities nearby. Both utilities would need to confirm.` |
| Tier text | `Shared endpoint facility` (from `coordination_tier_label`) |
| Confidence badge | `Reduced confidence` |

---

## 8. Frontend consumption rules

These rules are mandatory for every UI agent.

| # | Rule |
|---|---|
| F1 | Never compute distance on the client. Display `closest_distance_km` and `closest_distance_mi` exactly as returned |
| F2 | Never convert km to miles on the client. Use the `*_mi` fields |
| F3 | Never assign or recompute `coordination_tier`, `tier_confidence`, or `shared_endpoint_detected` on the client. Display the returned values |
| F4 | Never filter opportunities by distance on the client. The backend has already applied the 40 km gate |
| F5 | Render opportunities in `rank` order. Do not offer client-side re-sorting in v1 |
| F6 | Never compute date gaps on the client. Display `date_gap_days` |
| F7 | Draw the closest-point connector from `closest_connector` exactly. When its two positions are identical, draw a single marker instead of a line |
| F8 | Draw project geometry from `geometry` exactly. Do not smooth, snap, route, or extend lines. Draw a zero-length `LineString` as a point marker |
| F9 | Render `endpoint_only` projects as point markers with the badge `Endpoint only — route unknown` |
| F10 | When `is_endpoint_only_estimate` is `true`, show the note `Distance measured to the one known endpoint` next to the distance |
| F11 | When `tier_confidence` is `reduced`, show the badge `Reduced confidence` next to the tier label |
| F12 | When `shared_endpoint_detected` is `true`, present the item as a shared-facility finding using exactly this copy, with `{shared_endpoint_name}` replaced by the payload value unchanged. Headline: `Shared endpoint facility: {shared_endpoint_name}`. Callout body: `Both filings name an endpoint that resolves to the same location, published as {shared_endpoint_name}. GridLock cannot confirm from public sources whether these are one shared site or separate facilities nearby. Both utilities would need to confirm.` Never label the item `Crossing` or `Touching / crossing` |
| F13 | Show `0.000 km` distances as returned. Never hide, flag as an error, or replace a zero distance |
| F14 | Label center distance as secondary (`Center-to-center`) and never use it as the headline distance |
| F15 | When `data` is an empty array, show the empty state defined in `EDGE_CASES.md` §8. Do not show an error |
| F16 | On any error body, show `error.message`. Never show raw JSON or stack traces |
| F17 | Never call Overpass, Nominatim, or any geocoder or routing service |
| F18 | Never hard-code project coordinates, distances, tiers, or the expected pair list in the frontend |
| F19 | Display distances with the 3 decimals returned. Do not re-round, truncate, or reformat numeric precision |
| F20 | Show `data_warnings` in the project detail panel as plain informational text. Never treat them as errors |
| F21 | **Tier label authority.** Render `coordination_tier_label` from the payload as the only tier display text. Never derive tier display text on the client from the `coordination_tier` string value. That means no object literal keyed by tier strings, no `switch`/`case` on the value, no `if`/`else` or ternary chain comparing it to tier strings, and no translation or string-resource lookup keyed by it. There is no i18n layer on main, so the translation clause is precautionary. This payload label overrides any value-to-text mapping in any other specification. It is what keeps `Touching / crossing` and `Touching or crossing` off shared-endpoint pairs |
| F22 | Never split, parse, or reformat `shared_endpoint_name`. Insert the whole string where the F12 copy shows `{shared_endpoint_name}` |

---

## Acceptance checks

A QA agent must run all of these against a live backend loaded with the target dataset, plus the frontend where stated.

| # | Check | Pass condition |
|---|---|---|
| A1 | `GET /projects` | `200`, `meta.count == 10`, `data` length 10 |
| A2 | Project order | `project_id` sequence equals `DESC_1..DESC_5, GPC_1..GPC_5` |
| A3 | Utility enum | Every `utility` is `DESC` or `GPC` and matches the `project_id` prefix |
| A4 | Geometry consistency | `endpoint_pair` ⇔ `LineString` with 2 positions. `endpoint_only` ⇔ `Point` |
| A5 | `endpoint_only` count | Exactly 4 projects have `geometry_confidence == "endpoint_only"` (`DESC_1`, `DESC_2`, `DESC_4`, `GPC_2`) and `meta.endpoint_only_count == 4` |
| A6 | DESC_2 geometry | `DESC_2` has `geometry_confidence == "endpoint_only"` |
| A7 | Missing endpoints | Every `endpoint_only` project has `endpoint_b.known == false` and `endpoint_b.location == null` |
| A8 | Zero-length flag | `is_zero_length_segment` is `true` exactly when a `LineString` has two identical positions |
| A9 | GeoJSON order | Every `geometry` position equals `[location.lon, location.lat]` of its known endpoint |
| A10 | Zero-opportunity projects | `DESC_4`, `GPC_4`, `GPC_5` have `opportunity_count == 0` |
| A11 | `GET /opportunities` | `200`, `meta.count == 6`, `meta.total_count == 6` |
| A12 | Pair set | The set of `opportunity_id` values equals the six in §5.6 exactly |
| A13 | Excluded projects | No opportunity references `DESC_4`, `GPC_4`, or `GPC_5` |
| A14 | Gate | Every `closest_distance_km < 40.0` |
| A15 | Tier consistency | Every `coordination_tier` matches §2.4 applied to the returned `closest_distance_km`. When the returned value is exactly `0.001`, `1.600`, `8.000`, or `40.000`, the engine unit test on the full-precision value is authoritative instead |
| A16 | Tier label | Every `coordination_tier_label` equals the exact §2.4 backend label, using `Shared endpoint facility` when `shared_endpoint_detected` is `true` |
| A17 | Tier confidence | `tier_confidence == "reduced"` exactly when either side is `endpoint_only`; otherwise `"high"` |
| A18 | Shared endpoint fields | `shared_endpoint_name` is `null` exactly when `shared_endpoint_detected` is `false` |
| A19 | DESC_2 + GPC_1 finding | Item has `closest_distance_km <= 0.001`, `coordination_tier == "touching_crossing"`, `coordination_tier_label == "Shared endpoint facility"`, `shared_endpoint_detected == true`, `shared_endpoint_name == "Thurmond Sub / THURMOND DAM #5"`, `tier_confidence == "reduced"`, `distance_basis == "point_to_segment"`, `pair_geometry_confidence == "mixed"`, `date_gap_days == 3074` |
| A20 | Mile field | For every item, `abs(closest_distance_mi − closest_distance_km / 1.609344) <= 0.001`, and the same for center distance |
| A21 | Center ≥ closest | For every item, `center_distance_km >= closest_distance_km − 0.001` |
| A22 | Connector | `closest_connector.coordinates` equals the closest-point pair in DESC-then-GPC order, as `[lon, lat]` |
| A23 | Ranking | Items are sorted by the three-key rule in §5.5 and `rank` runs `1..6` with no gaps |
| A24 | Filter | `GET /opportunities?project_id=GPC_1` returns exactly `DESC_1__GPC_1` and `DESC_2__GPC_1`, with unchanged `rank` values, `meta.count == 2`, `meta.total_count == 6` |
| A25 | Filter on zero project | `GET /opportunities?project_id=DESC_4` returns `200`, `data == []`, `meta.count == 0`, `meta.total_count == 6` |
| A26 | Invalid project | `GET /opportunities?project_id=DESC_9` returns `400`, `error.code == "invalid_project_id"` |
| A27 | Unknown parameter | `GET /opportunities?tier=x` and `GET /projects?x=1` return `400 invalid_query_parameter` |
| A28 | Method | `POST /opportunities` returns `405 method_not_allowed` with header `Allow: GET` |
| A29 | Unknown route | `GET /nope` returns `404 not_found` with the §6.1 shape |
| A30 | `503` scope | Only the three §6.3 reasons produce `503`. A dataset with `endpoint_only` projects and a zero-length segment returns `200` |
| A31 | Determinism | Two consecutive calls return identical bodies after removing `meta.generated_at` |
| A32 | Golden fixture | The `DESC_2__GPC_1` item equals the `opportunity` object in `backend/tests/fixtures/golden/opportunity_DESC_2__GPC_1.json` field for field |
| A33 | No runtime lookups | With outbound network blocked, both routes still return `200` with identical bodies |
| A34 | No CEII | No response key or value contains CEII fields or data |
| A35 | Frontend label source | All three searches below return zero matches in non-test `.js`/`.jsx`/`.mjs`/`.cjs` files under `frontend/src` |
| A36 | Shared-endpoint card copy | The DESC_2 + GPC_1 card shows exactly the §7 headline and callout body, and neither `Touching / crossing` nor `Touching or crossing` appears anywhere on it |
| A37 | Label mutation test | With a stubbed payload where `coordination_tier = "under_8_km"` and `coordination_tier_label = "QA-LABEL-SENTINEL"`, the UI shows `QA-LABEL-SENTINEL`. This proves the label is not derived from the `coordination_tier` value |
| A38 | No name splitting | With a stubbed `shared_endpoint_name = "A / B / C"`, the headline and callout show `A / B / C` unchanged |

### A35 searches

Search 1 — tier value literals in non-test source. Catches object-literal maps (the keys are literals), `switch`/`case` on the value, and ternary or `if` chains comparing to literals:

```sh
rg -n -g '*.{js,jsx,mjs,cjs}' -g '!**/*.test.*' -g '!**/test/**' -g '!**/__tests__/**' -e 'touching_crossing' -e 'under_1_6_km' -e 'under_8_km' -e 'under_40_km' frontend/src
```

Search 2 — any read of the raw `coordination_tier` value. Also catches values built from string pieces:

```sh
rg -nP -g '*.{js,jsx,mjs,cjs}' -g '!**/*.test.*' -g '!**/test/**' -g '!**/__tests__/**' 'coordination_tier(?!_label)' frontend/src
```

Fallback when ripgrep lacks PCRE2:

```sh
rg -n -o -g '*.{js,jsx,mjs,cjs}' -g '!**/*.test.*' -g '!**/test/**' -g '!**/__tests__/**' 'coordination_tier\w*' frontend/src | grep -v ':coordination_tier_label$'
```

Search 3 — hardcoded tier display strings. `Shared endpoint facility` is deliberately excluded because the F12 headline legitimately contains it:

```sh
rg -n -g '*.{js,jsx,mjs,cjs}' -g '!**/*.test.*' -g '!**/test/**' -g '!**/__tests__/**' -e 'Touching / crossing' -e 'Touching or crossing' -e 'Under 1\.6 km' -e 'Under 8 km' -e 'Under 40 km' frontend/src
```

Any tier-based styling in the UI requires an approved allowlist entry before Search 2 may return a match. A37 is the behavioral backstop for anything a text search can miss.

---

## Appendix A. Engine-to-contract mapping gaps (informational)

This appendix describes **unmerged PR #8** (`backend/gridlock/official_engine.py` and `data/official/`) as read on 2026-09-27. It is **not** a defect report against PR #8, which predates this contract. It lists what the unassigned integration PR must map so the API emits this contract.

| # | Item | PR #8 engine | Contract | Risk |
|---|---|---|---|---|
| M1 | **Rounding** | Python `round()` (banker's rounding, half-to-even) | `Decimal` `ROUND_HALF_UP`; `round()` forbidden (`EDGE_CASES.md` X15) | **Highest.** A silent correctness difference: values ending in exactly 5 at the rounding digit serialize differently with no error raised |
| M2 | Geometry confidence value | `two_endpoints` | `endpoint_pair` | Medium |
| M3 | Tier values | `crossing`, `shared_row`, `shared_logistics`, `shared_crews` | `touching_crossing`, `under_1_6_km`, `under_8_km`, `under_40_km` | Medium |
| M4 | Touching rule | `distance_m <= 0.0` or `intersects` | `d <= 0.001` km or intersects | Medium |
| M5 | Distance fields | `distance_m`, `distance_km`, `distance_mi` (unqualified names) | `closest_distance_km` / `_mi` plus `center_distance_km` / `_mi` | Medium |
| M6 | Pair identity fields | `desc_id`, `gpc_id` | `desc_project_id`, `gpc_project_id`, `opportunity_id` | Low |
| M7 | Date gap field | `day_gap` (absolute) | `date_gap_days` and `date_gap_days_signed` | Low |
| M8 | Sort key | Rounded `distance_m`, then IDs | Full-precision km, then `date_gap_days`, then `opportunity_id` | Medium |
| M9 | Shared-endpoint and confidence fields | Absent | `shared_endpoint_detected`, `shared_endpoint_name`, `tier_confidence` | Medium |
| M10 | DESC_2 + GPC_1 wording | Tier `crossing`; PR #8's `docs/OFFICIAL_DATASET_ENGINE.md` describes a shared physical endpoint as a genuine touch | Label `Shared endpoint facility`; callout says GridLock cannot confirm one site versus separate nearby facilities | Flagged to P1; that document belongs to Agent 1 |

Distance model: PR #8 computes planar distance in EPSG:32617 (UTM 17N) via pyproj and shapely. The ruled target model finds closest points that way and reports the WGS 84 geodesic between them; the geodesic step belongs to the integration PR (see `GEOMETRY_MATH.md` banner and Blocker 3).
