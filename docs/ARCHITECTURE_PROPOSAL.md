# Architecture
Public filings → proposed CSV → human review → approved GeoJSON → deterministic engine (Python/Shapely in UTM 17N; PostGIS geography in production SQL) → FastAPI → React + MapLibre.

**Fallback:** the frontend loads `public/static/*.json` if the API is down. The core demo needs no live AI.

**Why UTM 17N (EPSG:32617):** covers the SC/GA border area with ~0.04% scale error (~16 m at 40 km boundary).

## Startup
```
cp .env.example .env
docker compose up
cd frontend && npm i && npm run dev
```
