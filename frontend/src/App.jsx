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

// OpenFreeMap Liberty vector basemap (roads, cities, state/water context).
const BASEMAP_STYLE = 'https://tiles.openfreemap.org/styles/liberty'
// Initial view: Georgia–South Carolina region.
const HOME_CENTER = [-81.3, 33.2]
const HOME_ZOOM = 6
// Attribution note: the OpenFreeMap "openmaptiles" source TileJSON already
// supplies the required credit ("OpenFreeMap © OpenMapTiles Data from
// OpenStreetMap", with links). MapLibre's built-in AttributionControl renders
// that automatically, so we leave it enabled and do NOT add a customAttribution
// (which would duplicate the text).

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
  // Latest approved FeatureCollection, kept so overlays can be re-added if the
  // basemap style reloads (setStyle would otherwise drop custom sources/layers).
  const approvedFC = useRef({ type: 'FeatureCollection', features: [] })
  const [opps, setOpps] = useState([])
  const [sel, setSel] = useState(null)
  const [offline, setOffline] = useState(false)
  const [err, setErr] = useState(null)
  const [basemapError, setBasemapError] = useState(false)
  const [loading, setLoading] = useState(true)
  // Candidate-review layer is ON by default.
  const [showCandidates, setShowCandidates] = useState(true)

  useEffect(() => {
    // maplibregl.Map unchanged in v6
    map.current = new maplibregl.Map({
      container: el.current,
      style: BASEMAP_STYLE,
      center: HOME_CENTER,
      zoom: HOME_ZOOM
      // Default AttributionControl stays ENABLED: it renders the OpenFreeMap /
      // OpenMapTiles / OpenStreetMap credit provided by the source TileJSON.
    })

    // ---- Map controls (guarded so they no-op where unavailable, e.g. tests) ----
    addControls(map.current)

    // Graceful basemap-loading failure: MapLibre emits 'error' for failed tile
    // /style requests. Surface an honest badge; overlays + sidebar keep working.
    if (typeof map.current.on === 'function') {
      map.current.on('error', (e) => {
        const msg = e && e.error && e.error.message ? e.error.message : ''
        // Only flag basemap/style/tile failures, not unrelated warnings.
        if (/style|tiles?|sprite|glyph|fetch|load/i.test(msg) || !msg) {
          setBasemapError(true)
        }
      })
    }

    let cancelled = false
    let dataLoaded = false

    // Fetch project/opportunity data and populate the sidebar. This does NOT
    // depend on the basemap succeeding, so the sidebar still works if tiles or
    // the style fail to load. Idempotent — safe to call more than once.
    async function loadData() {
      if (dataLoaded || cancelled) return
      dataLoaded = true
      try {
        const [fc, o1] = await get('/projects', '/static/projects_approved.geojson')
        const [op, o2] = await get('/opportunities', '/static/opportunities.json')
        if (cancelled) return
        approvedFC.current = fc
        setOffline(o1 || o2)
        setOpps(Array.isArray(op) ? op : [])
        // Add overlays if the style is ready; otherwise the styledata/load
        // handlers below will add them once it is.
        tryAddOverlays()
        setLoading(false)
      } catch (e) {
        if (cancelled) return
        setErr('Could not load approved data.')
        setLoading(false)
      }
    }

    // Add custom sources/layers only when the style is loaded. Guarded so it is
    // a no-op until the style is ready (and under the test mock).
    function tryAddOverlays() {
      const m = map.current
      if (!m) return
      const styleReady = typeof m.isStyleLoaded !== 'function' || m.isStyleLoaded()
      if (styleReady) addOverlays(m, approvedFC.current)
    }

    // Primary path: once the map's style has loaded, fetch data and add overlays.
    map.current.on('load', () => {
      loadData().then(tryAddOverlays)
    })

    // Safety net: don't let the sidebar be hostage to the basemap. If the map
    // 'load' event is slow or never fires (e.g. degraded WebGL / tile failure),
    // load the data anyway so the UI is usable. Overlays are added if/when the
    // style becomes ready.
    const fallbackTimer = setTimeout(() => { loadData() }, 4000)

    return () => {
      cancelled = true
      clearTimeout(fallbackTimer)
      map.current.remove()
    }
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

        {basemapError && (
          <p className="badge warn" data-testid="basemap-error-state">
            Basemap tiles failed to load. Project data and overlays are still
            shown; the background map may be blank.
          </p>
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

        {/* Honest empty state. */}
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

// ---------------------------------------------------------------------------
// Map controls. Each control is guarded: if the corresponding MapLibre class
// or Map method is unavailable (e.g. under the jsdom test mock), it is skipped
// so the app and tests keep working without a real WebGL map.
// ---------------------------------------------------------------------------
function addControls(m) {
  if (!m || typeof m.addControl !== 'function') return

  // Note: attribution is handled by MapLibre's built-in AttributionControl
  // (enabled by default), which renders the required OpenFreeMap / OpenMapTiles
  // / OpenStreetMap credit from the source TileJSON. No custom control here, to
  // avoid duplicating that text.
  // Zoom + compass.
  if (maplibregl.NavigationControl) {
    m.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')
  }
  // Scale bar.
  if (maplibregl.ScaleControl) {
    m.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: 'metric' }), 'bottom-left')
  }
  // Custom: fit to loaded project/candidate geometry.
  m.addControl(new FitToProjectsControl(), 'top-right')
  // Custom: reset to the Southeast (GA–SC) home view.
  m.addControl(new ResetViewControl(), 'top-right')
}

// Add all custom sources/layers. Safe to call after style (re)load.
function addOverlays(m, fc) {
  if (!m || typeof m.addSource !== 'function') return

  // ---- Approved layers (authoritative, primary styling) ----
  if (!hasSource(m, 'p')) {
    m.addSource('p', { type: 'geojson', data: fc })
  }
  if (!hasLayer(m, 'lines')) {
    m.addLayer({
      id: 'lines', type: 'line', source: 'p',
      filter: ['==', '$type', 'LineString'],
      paint: {
        'line-width': 4,
        'line-color': ['match', ['get', 'utility'], 'DESC', COLORS.DESC, COLORS.GPC]
      }
    })
  }
  if (!hasLayer(m, 'pts')) {
    m.addLayer({
      id: 'pts', type: 'circle', source: 'p',
      filter: ['==', '$type', 'Point'],
      paint: {
        'circle-radius': 7,
        'circle-color': ['match', ['get', 'utility'], 'DESC', COLORS.DESC, COLORS.GPC]
      }
    })
  }

  // Closest-point segment overlay for APPROVED opportunities (dashed red).
  if (!hasSource(m, 'seg')) {
    m.addSource('seg', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
  }
  if (!hasLayer(m, 'seg')) {
    m.addLayer({
      id: 'seg', type: 'line', source: 'seg',
      paint: { 'line-width': 3, 'line-dasharray': [2, 1], 'line-color': '#dc2626' }
    })
  }

  // ---- Candidate-review layer (NON-AUTHORITATIVE proposed proxies) ----
  if (!hasSource(m, 'candidates')) {
    m.addSource('candidates', { type: 'geojson', data: candidateFeatureCollection })
  }
  if (!hasLayer(m, 'candidate-pts')) {
    m.addLayer({
      id: 'candidate-pts', type: 'circle', source: 'candidates',
      paint: {
        'circle-radius': 8,
        'circle-color': 'rgba(245,158,11,0.25)',
        'circle-stroke-color': CANDIDATE_COLOR,
        'circle-stroke-width': 2,
        'circle-opacity': 1
      }
    })
  }
  if (!hasLayer(m, 'candidate-labels')) {
    m.addLayer({
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
  }
}

function hasSource(m, id) {
  return typeof m.getSource === 'function' && !!m.getSource(id)
}
function hasLayer(m, id) {
  return typeof m.getLayer === 'function' && !!m.getLayer(id)
}

// Fit the view to all loaded project + candidate geometry.
class FitToProjectsControl {
  onAdd(map) {
    this._map = map
    this._c = mkButton('⤢', 'Fit to projects', () => {
      const b = new maplibregl.LngLatBounds()
      let any = false
      const eat = (fc) => {
        for (const f of (fc && fc.features) || []) {
          const g = f.geometry
          if (!g) continue
          if (g.type === 'Point') { b.extend(g.coordinates); any = true }
          else if (g.type === 'LineString') { for (const c of g.coordinates) { b.extend(c); any = true } }
        }
      }
      // Read live source data where available; fall back to fixture geometry.
      eat(candidateFeatureCollection)
      const src = map.getSource && map.getSource('p')
      if (src && src._data) eat(src._data)
      if (any) map.fitBounds(b, { padding: 80, maxZoom: 11, duration: 600 })
    })
    return this._c
  }
  onRemove() { this._c && this._c.remove(); this._map = undefined }
}

// Reset to the Southeast (GA–SC) home view.
class ResetViewControl {
  onAdd(map) {
    this._map = map
    this._c = mkButton('⌂', 'Reset to Southeast', () => {
      map.flyTo({ center: HOME_CENTER, zoom: HOME_ZOOM, duration: 600 })
    })
    return this._c
  }
  onRemove() { this._c && this._c.remove(); this._map = undefined }
}

// Build a MapLibre-styled control button container.
function mkButton(label, title, onClick) {
  const wrap = document.createElement('div')
  wrap.className = 'maplibregl-ctrl maplibregl-ctrl-group'
  const btn = document.createElement('button')
  btn.type = 'button'
  btn.title = title
  btn.setAttribute('aria-label', title)
  btn.textContent = label
  btn.addEventListener('click', onClick)
  wrap.appendChild(btn)
  return wrap
}
