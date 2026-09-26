import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
const COLORS = { DESC: '#1f6feb', GPC: '#d97706' }
async function get(path, fallback) {
  try { const r = await fetch('/api' + path); if (!r.ok) throw 0; return [await r.json(), false] }
  catch { const r = await fetch(fallback); return [await r.json(), true] }
}
export default function App() {
  const el = useRef(null), map = useRef(null)
  const [opps, setOpps] = useState([]), [sel, setSel] = useState(null), [offline, setOffline] = useState(false), [err, setErr] = useState(null)
  useEffect(() => {
    map.current = new maplibregl.Map({ container: el.current, style: 'https://demotiles.maplibre.org/style.json', center: [-81.5, 32.6], zoom: 6.5 })
    map.current.on('load', async () => {
      try {
        const [fc, o1] = await get('/projects', '/static/projects_approved.geojson')
        const [op, o2] = await get('/opportunities', '/static/opportunities.json')
        setOffline(o1 || o2); setOpps(op)
        map.current.addSource('p', { type: 'geojson', data: fc })
        map.current.addLayer({ id: 'lines', type: 'line', source: 'p', filter: ['==', '$type', 'LineString'],
          paint: { 'line-width': 4, 'line-color': ['match', ['get', 'utility'], 'DESC', COLORS.DESC, COLORS.GPC] } })
        map.current.addLayer({ id: 'pts', type: 'circle', source: 'p', filter: ['==', '$type', 'Point'],
          paint: { 'circle-radius': 7, 'circle-color': ['match', ['get', 'utility'], 'DESC', COLORS.DESC, COLORS.GPC] } })
        map.current.addSource('seg', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
        map.current.addLayer({ id: 'seg', type: 'line', source: 'seg', paint: { 'line-width': 3, 'line-dasharray': [2, 1], 'line-color': '#dc2626' } })
      } catch (e) { setErr('Could not load approved data.') }
    })
    return () => map.current.remove()
  }, [])
  function pick(o) {
    setSel(o); const s = o.closest_segment
    map.current.getSource('seg').setData({ type: 'Feature', geometry: { type: 'LineString', coordinates: s } })
    const b = new maplibregl.LngLatBounds(s[0], s[0]); b.extend(s[1]); map.current.fitBounds(b, { padding: 160, maxZoom: 12 })
  }
  return (<div className="app">
    <aside>
      <h1>GridLock</h1>
      {offline && <p className="badge warn">Offline fallback: static approved data</p>}
      {err && <p className="badge err">{err}</p>}
      {!err && opps.length === 0 && <p>No approved cross-utility opportunities yet.</p>}
      <ol>{opps.map((o, i) => <li key={i}><button onClick={() => pick(o)}>
        <b>{o.project_a} ↔ {o.project_b}</b><span>{(o.distance_m/1000).toFixed(2)} km · {o.tier} · score {o.score}</span></button></li>)}</ol>
      {sel && <section className="drawer"><h2>Evidence</h2>
        <p>Minimum distance (full geometry): {(sel.distance_m/1000).toFixed(3)} km</p>
        <p>Tier: {sel.tier} — {sel.coordination_action}</p>
        <p>Timeline: {sel.timeline_status} ({sel.timeline_overlap_fraction})</p>
        <p>Confidence: {sel.confidence_multiplier}</p></section>}
    </aside><main ref={el} /></div>)
}
