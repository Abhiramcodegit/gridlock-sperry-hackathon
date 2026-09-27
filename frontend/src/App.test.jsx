// Agent 3 — frontend map-wiring tests.
// -----------------------------------------------------------------------------
// These tests exercise App.jsx WITHOUT a live backend and WITHOUT a real map.
//
// Two things are mocked:
//   1. maplibre-gl  — jsdom has no WebGL/canvas map. The mock provides a Map
//      whose `.on('load', cb)` invokes the callback so App's data-loading path
//      (which lives inside the 'load' handler and flips `loading` -> false)
//      actually runs. Layer/source methods are inert stubs.
//   2. global.fetch — every test drives the exact network shape it needs.
//
// App.jsx fetches, in order:
//   /api/projects       (fallback /static/projects_approved.geojson)
//   /api/opportunities  (fallback /static/opportunities.json)
// `get()` falls back to the static file on a non-ok primary response, and only
// throws (-> error state) when the fallback ALSO fails.
// -----------------------------------------------------------------------------
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor, within, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// ---- maplibre-gl mock -------------------------------------------------------
// Captured 'load' handlers so tests can control WHEN the map finishes loading.
// By default the map auto-fires 'load' on a microtask (mirrors real timing);
// set `autoFireLoad = false` to hold it and observe the transient loading UI.
const mapLoadHandlers = []
let autoFireLoad = true

// Manually invoke every registered 'load' handler (used when autoFireLoad is
// off, to release the loading state at a controlled point).
function fireMapLoad() {
  for (const cb of mapLoadHandlers) cb()
}

vi.mock('maplibre-gl', () => {
  class Map {
    constructor() {
      this._handlers = {}
    }
    on(event, cb) {
      if (event === 'load') {
        mapLoadHandlers.push(cb)
        if (autoFireLoad) {
          // Fire asynchronously, like the real 'load' event, so React state
          // updates happen after initial render (mirrors real timing).
          Promise.resolve().then(() => cb())
        }
      }
      return this
    }
    addSource() { return this }
    addLayer() { return this }
    getLayer() { return true }
    getSource() { return { setData: () => {} } }
    setLayoutProperty() { return this }
    fitBounds() { return this }
    flyTo() { return this }
    remove() { return this }
  }
  class LngLatBounds {
    extend() { return this }
  }
  return { __esModule: true, Map, LngLatBounds, default: { Map, LngLatBounds } }
})

// Mock the CSS side-effect import so it is a harmless no-op under jsdom.
vi.mock('maplibre-gl/dist/maplibre-gl.css', () => ({}))

// Import App AFTER the mocks are registered.
import App from './App.jsx'

// ---- fetch helpers ----------------------------------------------------------
function jsonResponse(body, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(body),
  })
}

// Default "happy path": approved API responds, both empty (the real state).
//   /api/projects      -> empty FeatureCollection
//   /api/opportunities -> []
function installDefaultFetch() {
  const fetchMock = vi.fn((url) => {
    if (url === '/api/projects') {
      return jsonResponse({ type: 'FeatureCollection', features: [] })
    }
    if (url === '/api/opportunities') {
      return jsonResponse([])
    }
    // Static fallbacks (should not be hit on the happy path).
    if (url === '/static/projects_approved.geojson') {
      return jsonResponse({ type: 'FeatureCollection', features: [] })
    }
    if (url === '/static/opportunities.json') {
      return jsonResponse([])
    }
    return jsonResponse(null, false, 404)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

beforeEach(() => {
  mapLoadHandlers.length = 0
  autoFireLoad = true
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

// -----------------------------------------------------------------------------
// 1. Loading state.
// -----------------------------------------------------------------------------
describe('1. loading state', () => {
  it('shows the loading badge while map load is pending, then clears it once loaded', async () => {
    installDefaultFetch()
    // Hold the map 'load' event so the transient loading state is observable.
    autoFireLoad = false

    render(<App />)

    // While load has not fired, `loading` is still true: the badge is shown.
    expect(screen.getByTestId('loading-state')).toHaveTextContent(/loading map data/i)
    // The loaded-only UI (candidate panel) is not present yet.
    expect(screen.queryByTestId('candidate-item-GPC-004')).toBeNull()

    // Release the map 'load' event; App loads data and clears loading.
    await act(async () => {
      fireMapLoad()
    })

    await waitFor(() => {
      expect(screen.queryByTestId('loading-state')).toBeNull()
    })
    // Loaded UI now present.
    expect(screen.getByTestId('candidate-item-GPC-004')).toBeInTheDocument()
  })
})

// -----------------------------------------------------------------------------
// 2. Approved-empty opportunity state.
// -----------------------------------------------------------------------------
describe('2. approved-empty opportunity state', () => {
  it('renders the exact empty-state text when approved projects and opportunities are empty', async () => {
    installDefaultFetch()
    render(<App />)

    const empty = await screen.findByTestId('empty-state')
    // Whitespace-tolerant match of the exact copy from App.jsx.
    expect(empty).toHaveTextContent(
      /No approved coordination opportunities currently qualify\. Showing 2 proposed proxy locations for review; these are excluded from opportunity analysis\./i
    )
    // No opportunity list is rendered when there are no opportunities.
    expect(screen.queryByTestId('opportunity-list')).toBeNull()
  })
})

// -----------------------------------------------------------------------------
// 3. Exactly two candidate-review items.
// -----------------------------------------------------------------------------
describe('3. exactly two candidate-review items', () => {
  it('renders exactly two candidate items, one per proposed proxy id', async () => {
    installDefaultFetch()
    render(<App />)

    // Wait for the candidate panel (renders once loading completes).
    await screen.findByTestId('candidate-item-GPC-004')

    const items = screen.getAllByTestId(/^candidate-item-/)
    expect(items).toHaveLength(2)

    expect(screen.getByTestId('candidate-item-GPC-004')).toBeInTheDocument()
    expect(screen.getByTestId('candidate-item-DESC-003')).toBeInTheDocument()

    // The sidebar count of geometry-less proposed records is honest (32 of 34).
    expect(screen.getByTestId('candidate-count')).toHaveTextContent(
      /32 of 34 proposed records/i
    )
  })
})

// -----------------------------------------------------------------------------
// 4. Exact proxy label text.
// -----------------------------------------------------------------------------
describe('4. exact proxy label text', () => {
  it('labels each candidate exactly "Proposed — inferred substation proxy"', async () => {
    installDefaultFetch()
    render(<App />)

    const gpc = await screen.findByTestId('candidate-label-GPC-004')
    const desc = screen.getByTestId('candidate-label-DESC-003')

    // Exact string, including the em dash.
    expect(gpc).toHaveTextContent('Proposed — inferred substation proxy')
    expect(desc).toHaveTextContent('Proposed — inferred substation proxy')
    expect(gpc.textContent.trim()).toBe('Proposed — inferred substation proxy')
    expect(desc.textContent.trim()).toBe('Proposed — inferred substation proxy')
  })
})

// -----------------------------------------------------------------------------
// 5. Candidate-layer toggle.
// -----------------------------------------------------------------------------
describe('5. candidate-layer toggle', () => {
  it('toggle is on by default and flips off/on, controlling candidate visibility', async () => {
    installDefaultFetch()
    const user = userEvent.setup()
    render(<App />)

    const toggle = await screen.findByTestId('candidate-layer-toggle')
    // On by default (requirement: candidate layer visible on load).
    expect(toggle).toBeChecked()
    // Candidate items are visible while the toggle is on.
    expect(screen.getByTestId('candidate-item-GPC-004')).toBeInTheDocument()

    await user.click(toggle)
    expect(toggle).not.toBeChecked()

    await user.click(toggle)
    expect(toggle).toBeChecked()
  })
})

// -----------------------------------------------------------------------------
// 6. Disclaimer.
// -----------------------------------------------------------------------------
describe('6. disclaimer', () => {
  it('shows the non-authoritative candidate disclaimer', async () => {
    installDefaultFetch()
    render(<App />)

    const disclaimer = await screen.findByTestId('candidate-disclaimer')
    expect(disclaimer).toBeVisible()
    expect(disclaimer).toHaveTextContent(
      /not approved project geometries/i
    )
  })
})

// -----------------------------------------------------------------------------
// 7. No tier or opportunity line for proposed proxies.
// -----------------------------------------------------------------------------
describe('7. no tier or opportunity line for proposed proxies', () => {
  it('does not render any opportunity list/detail or tier text for the proposed proxies', async () => {
    installDefaultFetch()
    render(<App />)

    await screen.findByTestId('candidate-item-GPC-004')

    // No opportunity list and no opportunity detail drawer.
    expect(screen.queryByTestId('opportunity-list')).toBeNull()
    expect(screen.queryByTestId('opportunity-detail')).toBeNull()

    // The proposed proxy ids never appear inside an opportunity row.
    // (There is no opportunity-list element at all here, which is the point.)
    const gpcItem = screen.getByTestId('candidate-item-GPC-004')
    const descItem = screen.getByTestId('candidate-item-DESC-003')

    // No coordination tier vocabulary leaks into the candidate rows.
    for (const item of [gpcItem, descItem]) {
      const text = item.textContent
      expect(text).not.toMatch(/\btier\b/i)
      expect(text).not.toMatch(/\bscore\b/i)
      expect(text).not.toMatch(/coordination action/i)
      // km distance readouts belong to opportunity rows, not candidates.
      expect(text).not.toMatch(/\bkm\b/i)
    }

    // The label still correctly marks them as proposed proxies (not approved).
    expect(within(gpcItem).getByTestId('candidate-label-GPC-004')).toHaveTextContent(
      'Proposed — inferred substation proxy'
    )
  })
})

// -----------------------------------------------------------------------------
// 8. Fetch failure / error state.
// -----------------------------------------------------------------------------
describe('8. fetch failure produces an honest error state, not a crash', () => {
  it('renders the error badge when both the API and the static fallback fail', async () => {
    // Primary AND fallback both reject/fail so get() throws -> catch -> setErr.
    const fetchMock = vi.fn(() => Promise.reject(new Error('network down')))
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    const errorEl = await screen.findByTestId('error-state')
    expect(errorEl).toBeInTheDocument()
    expect(errorEl).toHaveTextContent(/could not load approved data/i)

    // The app did not crash: the shell heading is still present.
    expect(screen.getByRole('heading', { name: /gridlock/i })).toBeInTheDocument()
    // Error state and empty state are mutually exclusive.
    expect(screen.queryByTestId('empty-state')).toBeNull()
  })
})

// -----------------------------------------------------------------------------
// 9. Static fallback state.
// -----------------------------------------------------------------------------
describe('9. static fallback state', () => {
  it('shows the offline fallback badge when the API is down but static files serve', async () => {
    // Primary /api/* responses are non-ok; static fallbacks succeed.
    const fetchMock = vi.fn((url) => {
      if (url.startsWith('/api/')) {
        return jsonResponse(null, false, 503)
      }
      if (url === '/static/projects_approved.geojson') {
        return jsonResponse({ type: 'FeatureCollection', features: [] })
      }
      if (url === '/static/opportunities.json') {
        return jsonResponse([])
      }
      return jsonResponse(null, false, 404)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    const fallback = await screen.findByTestId('fallback-state')
    expect(fallback).toBeInTheDocument()
    expect(fallback).toHaveTextContent(/offline fallback/i)

    // Fallback is a healthy state, not an error.
    expect(screen.queryByTestId('error-state')).toBeNull()
    // Static data is still empty, so the empty state also shows.
    expect(await screen.findByTestId('empty-state')).toBeInTheDocument()
  })
})
