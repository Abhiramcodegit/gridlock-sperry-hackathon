import json, pathlib
from fastapi import FastAPI
from .engine import Project, find_opportunities
app = FastAPI(title="GridLock")
DATA = pathlib.Path(__file__).resolve().parents[2] / "data" / "approved" / "projects_approved.geojson"
def load():
    if not DATA.exists(): return []
    fc = json.loads(DATA.read_text()); out = []
    for f in fc["features"]:
        p = f["properties"]
        out.append(Project(p["id"], p["utility"], p["name"], f["geometry"], p.get("geometry_confidence","unresolved"),
                           review_status=p.get("review_status","proposed")))
    return out
@app.get("/health")
def health(): return {"ok": True}
@app.get("/projects")
def projects(): return json.loads(DATA.read_text()) if DATA.exists() else {"type":"FeatureCollection","features":[]}
@app.get("/opportunities")
def opportunities(): return find_opportunities(load())
