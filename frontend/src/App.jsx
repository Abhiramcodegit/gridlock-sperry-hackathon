// MapLibre GL JS v6 migration notes:
// - v6 is ESM-only; default export removed. Use namespace import.
// - The worker is bundled automatically by Vite in v6 — no manual
//   setWorkerUrl() wiring is needed (the old CSP worker file was removed).
// - Map, LngLatBounds, etc. are unchanged in call signature.
// - See: https://maplibre.org/maplibre-gl-js/docs/guides/v5-to-v6-migration-guide/
import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import {
  candidateFeatureCollection,
  CANDIDATE_RECORDS,
  PROPOSED_TOTAL,
  PROPOSED_WITHOUT_GEOMETRY,
} from './candidateFixture'

const COLORS = { DESC: '#1f6feb', GPC: '#d97706' }
// Candidate-review styling: amber + dashed, deliberately distinct from the
// authoritative approved styling so it can never be mistaken for approved data.
const CANDIDATE_COLOR = '#f59e0b'

async function get(path, fallback) {
  try {
    const r = await fetch('/api' + path)
    if (!r.ok) throw 0
    return [await r.json(), false]
  } catch {
    const r = await fetch(fallback)
    if (!r.ok) throw new Error('fallback failed for ' + path)
    return [await r.json(), true]
  }
}

export default function App() {
  const el = useRef(null), map = useRef(null)
  const [opps, setOpps] = useState([])
  const [sel, setSel] = useState(null)
  const [offline, setOffline] = useState(false)
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(true)
  // Candidate-review layer is ON by default (requirement 3).
  const [showCandidates, setShowCandidates] = useState(true)

  useEffect(() => {
    // maplibregl.Map unchanged in v6
    map.current = new maplibregl.Map({
      container: el.current,
      style: 'https://demotiles.maplibre.org/style.json',
      center: [-81.5, 32.6],
      zoom: 6.5
    })

    map.current.on('load', async () => {
      try {
        const [fc, o1] = await get('/projects', '/static/projects_approved.geojson')
        const [op, o2] = await get('/opportunities', '/static/opportunities.json')
        setOffline(o1 || o2)
        setOpps(Array.isArray(op) ? op : [])

        // ---- Approved layers (authoritative, primary styling) ----
        // addSource / addLayer API unchanged in v6
        map.current.addSource('p', { type: 'geojson', data: fc })
        map.current.addLayer({
          id: 'lines', type: 'line', source: 'p',
          filter: ['==', '$type', 'LineString'],
          paint: {
            'line-width': 4,
            'line-color': ['match', ['get', 'utility'], 'DESC', COLORS.DESC, COLORS.GPC]
          }
        })
        map.current.addLayer({
          id: 'pts', type: 'circle', source: 'p',
          filter: ['==', '$type', 'Point'],
          paint: {
            'circle-radius': 7,
            'circle-color': ['match', ['get', 'utility'], 'DESC', COLORS.DESC, COLORS.GPC]
          }
        })

        // Closest-point segment overlay for APPROVED opportunities (dashed red).
        // Only ever driven by opportunity records from the approved-only API.
        map.current.addSource('seg', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] }
        })
        map.current.addLayer({
          id: 'seg', type: 'line', source: 'seg',
          paint: { 'line-width': 3, 'line-dasharray': [2, 1], 'line-color': '#dc2626' }
        })

        // ---- Candidate-review layer (NON-AUTHORITATIVE proposed proxies) ----
        // Sourced from an isolated fixture, not a backend endpoint. Amber +
        // dashed outline. No lines are ever drawn between the two proxies, and
        // no coordination tier is ever assigned to them.
        map.current.addSource('candidates', {
          type: 'geojson',
          data: candidateFeatureCollection
        })
        map.current.addLayer({
          id: 'candidate-pts', type: 'circle', source: 'candidates',
          paint: {
            'circle-radius': 8,
            'circle-color': 'rgba(245,158,11,0.25)',
            'circle-stroke-color': CANDIDATE_COLOR,
            'circle-stroke-width': 2,
            // dashed stroke isn't supported on circle; the label + amber fill
            // + the dashed sidebar styling carry the "non-authoritative" signal.
            'circle-opacity': 1
          }
        })
        map.current.addLayer({
          id: 'candidate-labels', type: 'symbol', source: 'candidates',
          layout: {
            'text-field': ['concat', ['get', 'id'], '\n', ['get', 'label']],
            'text-size': 11,
            'text-offset': [0, 1.4],
            'text-anchor': 'top',
            'text-allow-overlap': true
          },
          paint: {
            'text-color': '#92400e',
            'text-halo-color': '#fffbeb',
            'text-halo-width': 1.5
          }
        })

        setLoading(false)
      } catch (e) {
        setErr('Could not load approved data.')
        setLoading(false)
      }
    })

    return () => map.current.remove()
  }, [])

  // Toggle candidate-review layer visibility (on by default).
  useEffect(() => {
    if (!map.current) return
    const vis = showCandidates ? 'visible' : 'none'
    for (const id of ['candidate-pts', 'candidate-labels']) {
      if (map.current.getLayer && map.current.getLayer(id)) {
        map.current.setLayoutProperty(id, 'visibility', vis)
      }
    }
  }, [showCandidates, loading])

  function pick(o) {
    setSel(o)
    const s = o.closest_segment
    // setData unchanged in v6
    map.current.getSource('seg').setData({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: s }
    })
    // LngLatBounds unchanged in v6
    const b = new maplibregl.LngLatBounds(s[0], s[0])
    b.extend(s[1])
    map.current.fitBounds(b, { padding: 160, maxZoom: 12 })
  }

  function flyToCandidate(c) {
    if (!map.current) return
    map.current.flyTo({ center: c.coordinates, zoom: 11 })
  }

  const showEmptyState = !loading && !err && opps.length === 0

  return (
    <div className="app">
      <aside>
        <h1>GridLock</h1>

        {loading && (
          <p className="badge" data-testid="loading-state">Loading map data…</p>
        )}

        {offline && !err && (
          <p className="badge warn" data-testid="fallback-state">
            Offline fallback: showing static approved data (API unavailable).
          </p>
        )}

        {err && (
          <p className="badge err" data-testid="error-state">{err}</p>
        )}

        {/* Approved coordination opportunities (approved-only, authoritative). */}
        {!loading && !err && opps.length > 0 && (
          <ol data-testid="opportunity-list">
            {opps.map((o, i) => (
              <li key={i}>
                <button onClick={() => pick(o)}>
                  <b>{o.project_a} ↔ {o.project_b}</b>
                  <span>{(o.distance_m / 1000).toFixed(2)} km · {o.tier} · score {o.score}</span>
                </button>
              </li>
            ))}
          </ol>
        )}

        {/* Honest empty state (requirement 7). */}
        {showEmptyState && (
          <p className="empty" data-testid="empty-state">
            No approved coordination opportunities currently qualify. Showing 2
            proposed proxy locations for review; these are excluded from
            opportunity analysis.
          </p>
        )}

        {/* Candidate-review panel — proposed proxies, non-authoritative. */}
        {!loading && !err && (
          <section className="candidates">
            <div className="candidate-head">
              <h2>Candidate review</h2>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={showCandidates}
                  onChange={(e) => setShowCandidates(e.target.checked)}
                  data-testid="candidate-layer-toggle"
                />
                Show candidates
              </label>
            </div>

            <p className="disclaimer" data-testid="candidate-disclaimer">
              Candidate locations are for review and are not approved project
              geometries.
            </p>

            <ul className="candidate-list">
              {CANDIDATE_RECORDS.map((c) => (
                <li key={c.id} data-testid={`candidate-item-${c.id}`}>
                  <button
                    className="candidate-item"
                    onClick={() => flyToCandidate(c)}
                    data-testid={`candidate-marker-${c.id}`}
                  >
                    <b>{c.id} — {c.name}</b>
                    <span data-testid={`candidate-label-${c.id}`}>{c.label}</span>
                    <span className="src">{c.geometry_source}</span>
                  </button>
                </li>
              ))}
            </ul>

            <p className="candidate-count" data-testid="candidate-count">
              {PROPOSED_WITHOUT_GEOMETRY} of {PROPOSED_TOTAL} proposed records
              have no geometry and are not shown on the map.
            </p>
          </section>
        )}

        {sel && (
          <section className="drawer" data-testid="opportunity-detail">
            <h2>Evidence</h2>
            <p>Minimum distance (full geometry): {(sel.distance_m / 1000).toFixed(3)} km</p>
            <p>Tier: {sel.tier} — {sel.coordination_action}</p>
            <p>Timeline: {sel.timeline_status} ({sel.timeline_overlap_fraction})</p>
            <p>Confidence: {sel.confidence_multiplier}</p>
          </section>
        )}
      </aside>
      <main ref={el} />
    </div>
  )
}
