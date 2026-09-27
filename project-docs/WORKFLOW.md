# GridLock — Build Workflow

> Living document. Updated every phase. Last updated: 2026-09-26 (Phase 1)

---

## AI Division of Labour

| System | What it does | What it never does |
|---|---|---|
| **Perplexity** | Creates branches, pushes code/docs to GitHub via MCP, researches sources, writes agents, fixes bugs, updates all living docs | Approves data, merges to main, makes scoring decisions |
| **Kiro** | Runs code locally, executes pytest and npm audit, verifies map renders, reports failures | Approves data, merges to main |
| **Abhiram** | Reviews all data decisions, approves checkpoints, makes all merge calls, sets priorities | — |

---

## Branch Strategy

| Branch pattern | Purpose |
|---|---|
| `main` | Approved, demo-ready code only |
| `backend/feature-name` | Backend features and fixes |
| `frontend/feature-name` | Frontend features and fixes |
| `research/phase-name` | Source validation, agent work, data files |
| `phase-N/description` | Major phase deliverables |

**Rule:** Every PR targeting `main` starts as DRAFT. Abhiram converts to Ready and merges.

---

## Phase Gates

Each phase has a named Checkpoint. The next phase does not start until the Checkpoint is explicitly approved by Abhiram.

| Phase | Checkpoint condition |
|---|---|
| 1 → 2 | 18 DESC projects verified, Georgia Power source resolved, approved_projects.csv populated with at least 2 cross-utility projects with INFERRED+ geometries |
| 2 → 3 | PostGIS schema populated, ST_Distance returns correct results for at least 1 real project pair, all tests pass |
| 3 → 4 | FastAPI /opportunities returns real data, map renders real layers, evidence drawer shows correct numbers |
| 4 → Submit | Demo path fully cached, all audit findings 0 high/0 critical, README complete |

---

## What Perplexity Does at Each Phase

### Every phase:
- Update `README.md` phase status table
- Update `project-docs/PHASE_STATUS.md`
- Update `docs/DECISION_LOG.md` with any new architectural decisions
- Update `docs/DATA_LIMITATIONS.md` if data scope changed
- Re-run security review checklist

### Phase-specific:
- **Phase 1:** Source research, document extraction, manifest + ledger + rejected log
- **Phase 2:** Geocoding agent, coordinate CSV, DB loader script
- **Phase 3:** Engine ↔ DB integration, API endpoints, map layer wiring
- **Phase 4:** Demo caching, cost estimator, polish, final audit

---

## Commit Message Convention

```
type(scope): short description

Longer explanation if needed.

Security: note any CVE decisions.
Phase: which phase this belongs to.
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `security`, `data`

Scopes: `backend`, `frontend`, `db`, `data`, `docs`, `deps`, `security`

---

## Open Source Connector Policy

Before adding any open-source GitHub connector or library:

1. Does it improve ingestion, verification, analysis, or demo quality?
2. Is it reliable enough for a live presentation?
3. Is it dev-only or production? (security implications differ)
4. Does it introduce any credentials / permission scope beyond what’s needed?
5. Can the core app work if this connector fails?

All approved connectors are listed in `project-docs/TECH_STACK.md`.
