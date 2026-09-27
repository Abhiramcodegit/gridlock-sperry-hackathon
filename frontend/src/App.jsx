// MapLibre GL JS v6 migration notes:
// - v6 is ESM-only; default export removed. Use namespace import.
// - v6 ships its render worker as a SEPARATE ESM file (maplibre-gl-worker.mjs).
//   Vite does NOT auto-emit that worker for a namespace import, so in a
//   PRODUCTION build `new Worker(<url>)` resolves to a path the preview/host
//   serves as index.html (text/html) — the worker dies on the MIME check and
//   vector tiles never decode (only the raster hillshade paints). We fix this
//   by resolving the worker through Vite's `?worker&url` import (which emits
//   the worker AND its maplibre-gl-shared sibling) and handing it to
//   maplibregl.setWorkerUrl(). `?worker&url` is mandatory here — plain `?url`
//   emits the worker without its shared sibling and fails on first import in
//   production builds only (dev happens to work either way).
// - Map, LngLatBounds, etc. are unchanged in call signature.
// - See: https://maplibre.org/maplibre-gl-js/docs/guides/v5-to-v6-migration-guide/
import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'

// Point MapLibre at the Vite-resolved worker URL so the render worker loads
// reliably in both dev and production builds.
if (typeof maplibregl.setWorkerUrl === 'function') {
  maplibregl.setWorkerUrl(maplibreWorkerUrl)
}

const COLORS = { DESC: '#1f6feb', GPC: '#d97706' }
// Candidate-review styling: amber + dashed, deliberately distinct from the
// authoritative approved styling so it can never be mistaken for approved data.
const CANDIDATE_COLOR = '#f59e0b'

// OpenFreeMap Liberty vector basemap (roads, cities, state/water context).
const BASEMAP_STYLE = 'https://tiles.openfreemap.org/styles/liberty'
// Initial view: Georgia–South Carolina region.
const HOME_CENTER = [-81.3, 33.2]
const HOME_ZOOM = 6
// How long to wait for the basemap to finish (reach 'idle') before we treat a
// map 'error' as a genuine basemap failure and show the badge.
const BASEMAP_IDLE_GRACE_MS = 6000
// Attribution note: the OpenFreeMap "openmaptiles" source TileJSON already
// supplies the required credit ("OpenFreeMap © OpenMapTiles Data from
// OpenStreetMap", with links). MapLibre's built-in AttributionControl renders
// that automatically, so we leave it enabled and do NOT add a customAttribution
// (which would duplicate the text).

const EMPTY_FC = { type: 'FeatureCollection', features: [] }

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

// Fetch the NON-AUTHORITATIVE candidate-review geometry at runtime. Per F18 the
// coordinates are NOT hardcoded in the bundle; they live in a static data asset
// derived from data/normalized/projects_proposed.csv. Returns a normalized
// FeatureCollection (never throws).
async function getCandidates() {
  try {
    const r = await fetch('/static/candidates_proposed.geojson')
    if (!r.ok) throw 0
    const fc = await r.json()
    if (!fc || !Array.isArray(fc.features)) return EMPTY_FC
    return fc
  } catch {
    return EMPTY_FC
  }
}

export default function App() {
  const el = useRef(null), map = useRef(null)
  // Tracked geometry (item 3): kept in refs so the Fit-to-projects control and
  // the styledata re-add path can read them WITHOUT touching MapLibre private
  // fields (source._data). Mirrors of the React state below.
  const approvedFCRef = useRef(EMPTY_FC)
  const candidateFCRef = useRef(EMPTY_FC)

  const [opps, setOpps] = useState([])
  const [candidates, setCandidates] = useState(EMPTY_FC)
  const [proposedTotal, setProposedTotal] = useState(0)
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
    // Pass getters so the Fit control always reads the latest tracked geometry.
    addControls(map.current, {
      getApproved: () => approvedFCRef.current,
      getCandidates: () => candidateFCRef.current,
    })

    let cancelled = false
    let dataLoaded = false
    let mapReachedIdle = false

    // ---- Narrowed basemap-failure detection (item 1) ----
    // We no longer flag every 'error' (the old `|| !msg` catch-all produced
    // false positives on benign MapLibre errors even when tiles returned 200).
    // A basemap failure is only reported when BOTH are true:
    //   (a) an 'error' clearly attributable to the basemap fired
    //       (it references the openmaptiles/basemap source, OR carries an
    //        HTTP error status, OR names the style/tiles/sprite/glyphs), AND
    //   (b) the map has not reached 'idle' within a grace window (i.e. the
    //       basemap genuinely did not finish rendering).
    let basemapErrorSeen = false
    function maybeReportBasemapFailure() {
      if (cancelled) return
      if (basemapErrorSeen && !mapReachedIdle) setBasemapError(true)
    }
    function isBasemapError(e) {
      if (!e) return false
      // MapLibre attaches sourceId for source/tile errors.
      if (e.sourceId) return e.sourceId === 'openmaptiles' || e.sourceId === 'ne2_shaded'
      const status = e.error && (e.error.status || e.error.statusCode)
      if (typeof status === 'number' && status >= 400) return true
      const msg = e.error && e.error.message ? String(e.error.message) : ''
      // Require an explicit basemap-resource keyword; no empty-message catch-all.
      return /\b(style|tile|tiles|sprite|glyph|glyphs)\b/i.test(msg)
    }

    if (typeof map.current.on === 'function') {
      map.current.on('error', (e) => {
        if (isBasemapError(e)) {
          basemapErrorSeen = true
          // Defer: if the map still reaches 'idle', this was transient/benign.
          setTimeout(maybeReportBasemapFailure, BASEMAP_IDLE_GRACE_MS)
        }
      })
      // 'idle' fires once the map has finished loading and rendering the current
      // view. Reaching it means the basemap is fine, regardless of earlier
      // transient errors — so we clear any pending/!shown failure state.
      map.current.on('idle', () => {
        mapReachedIdle = true
        if (!cancelled) setBasemapError(false)
      })
    }

    // Fetch project/opportunity/candidate data and populate the sidebar. This
    // does NOT depend on the basemap succeeding, so the sidebar still works if
    // tiles or the style fail to load. Idempotent — safe to call more than once.
    async function loadData() {
      if (dataLoaded || cancelled) return
      dataLoaded = true
      try {
        const [fc, o1] = await get('/projects', '/static/projects_approved.geojson')
        const [op, o2] = await get('/opportunities', '/static/opportunities.json')
        const cand = await getCandidates()
        if (cancelled) return
        approvedFCRef.current = fc || EMPTY_FC
        candidateFCRef.current = cand
        setOffline(o1 || o2)
        setOpps(Array.isArray(op) ? op : [])
        setCandidates(cand)
        setProposedTotal(candidateProposedTotal(cand))
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
      if (styleReady) addOverlays(m, approvedFCRef.current, candidateFCRef.current)
    }

    // Primary path: once the map's style has loaded, fetch data and add overlays.
    map.current.on('load', () => {
      loadData().then(tryAddOverlays)
    })

    // Item 4: re-add overlays after a style (re)load. setStyle() drops custom
    // sources/layers; 'styledata' fires when a new style finishes loading, so
    // we re-apply our guarded overlays. Guarded add makes this idempotent for
    // the many 'styledata' events MapLibre emits during normal tile loading.
    map.current.on('styledata', () => {
      if (!cancelled) tryAddOverlays()
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
    map.current.flyTo({ center: c.geometry.coordinates, zoom: 11 })
  }

  const showEmptyState = !loading && !err && opps.length === 0
  const candidateFeatures = candidates.features || []
  const withoutGeometry = Math.max(0, proposedTotal - candidateFeatures.length)

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

        {/* Honest empty state (verbatim copy relied upon by the test suite). */}
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
              {candidateFeatures.map((c) => (
                <li key={c.properties.id} data-testid={`candidate-item-${c.properties.id}`}>
                  <button
                    className="candidate-item"
                    onClick={() => flyToCandidate(c)}
                    data-testid={`candidate-marker-${c.properties.id}`}
                  >
                    <b>{c.properties.id} — {c.properties.name}</b>
                    <span data-testid={`candidate-label-${c.properties.id}`}>{c.properties.label}</span>
                    <span className="src">{c.properties.geometry_source}</span>
                  </button>
                </li>
              ))}
            </ul>

            <p className="candidate-count" data-testid="candidate-count">
              {withoutGeometry} of {proposedTotal} proposed records
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

// Total proposed-record count. Prefer the value the data asset reports in its
// metadata; fall back to the number of features present. Never hardcoded.
function candidateProposedTotal(fc) {
  const meta = fc && fc.metadata
  if (meta && Number.isFinite(meta.proposed_total)) return meta.proposed_total
  return (fc && fc.features ? fc.features.length : 0)
}

// ---------------------------------------------------------------------------
// Map controls. Each control is guarded: if the corresponding MapLibre class
// or Map method is unavailable (e.g. under the jsdom test mock), it is skipped
// so the app and tests keep working without a real WebGL map.
// ---------------------------------------------------------------------------
function addControls(m, geom) {
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
  // Custom: fit to loaded project/candidate geometry (reads tracked state).
  m.addControl(new FitToProjectsControl(geom), 'top-right')
  // Custom: reset to the Southeast (GA–SC) home view.
  m.addControl(new ResetViewControl(), 'top-right')
}

// Add all custom sources/layers. Safe to call after style (re)load.
function addOverlays(m, approvedFC, candidateFC) {
  if (!m || typeof m.addSource !== 'function') return

  // ---- Approved layers (authoritative, primary styling) ----
  if (!hasSource(m, 'p')) {
    m.addSource('p', { type: 'geojson', data: approvedFC || EMPTY_FC })
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
    m.addSource('seg', { type: 'geojson', data: EMPTY_FC })
  }
  if (!hasLayer(m, 'seg')) {
    m.addLayer({
      id: 'seg', type: 'line', source: 'seg',
      paint: { 'line-width': 3, 'line-dasharray': [2, 1], 'line-color': '#dc2626' }
    })
  }

  // ---- Candidate-review layer (NON-AUTHORITATIVE proposed proxies) ----
  if (!hasSource(m, 'candidates')) {
    m.addSource('candidates', { type: 'geojson', data: candidateFC || EMPTY_FC })
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
// Item 3: reads tracked geometry via injected getters — no source._data.
class FitToProjectsControl {
  constructor(geom) { this._geom = geom || {} }
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
      const getApproved = this._geom.getApproved || (() => EMPTY_FC)
      const getCandidates = this._geom.getCandidates || (() => EMPTY_FC)
      eat(getApproved())
      eat(getCandidates())
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
