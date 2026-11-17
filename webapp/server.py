"""Local-only game API. Python core remains the sole source of ML predictions."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from secrets import token_urlsafe
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from space_miner.core import Planet, galaxy, knn, accuracy, baseline, mine
from space_miner.strategy import ranked_candidates, explanation

app = FastAPI(title="Space Miner AI Game API", version="0.2.0")
STATIC = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")

@dataclass
class Mission:
    seed: int
    world: dict
    credits: int = 100
    scanned: list[str] = field(default_factory=list)
    mined: set[str] = field(default_factory=set)
    history: list[dict] = field(default_factory=list)
    k: int = 3
    trained: bool = False
    ended: bool = False

# Local prototype only: ephemeral in-memory sessions. Do not publicly deploy
# without authentication, persistence, rate limits and session protection.
sessions: dict[str, Mission] = {}

class NewMission(BaseModel):
    seed: int = Field(default=12, ge=0, le=1000000)

class TrainChoice(BaseModel):
    k: Literal[1, 3, 5, 7]

class PlanetChoice(BaseModel):
    planet_id: str

def session_or_404(session_id: str) -> Mission:
    m=sessions.get(session_id)
    if m is None: raise HTTPException(404,"Mission not found. Create a new one.")
    return m

def known(m:Mission)->list[Planet]:
    return m.world["starter"]+[p for p in m.world["reserve"] if p.id in m.scanned]

def planet_info(p:Planet,ore_visible=False)->dict:
    d={"id":p.id,"heat":p.thermal,"spectrum":p.spectral}
    if ore_visible:d["ore"]=p.ore
    return d

def snapshot(session_id:str,m:Mission,event=None)->dict:
    training=known(m)
    remaining=[p for p in m.world["mining"] if p.id not in m.mined]
    ranking={p.id:(pred,votes,avg) for p,pred,votes,avg in ranked_candidates(training,remaining,m.k)} if m.trained else {}
    by_id={r["planet_id"]:r for r in m.history}
    candidates=[]
    for p in m.world["mining"]:
        row=planet_info(p)
        if p.id in by_id:
            r=by_id[p.id];row.update(mined=True,ore=r["ore"],predicted=r["predicted"])
        else:
            row["mined"]=False
            if m.trained:
                pred,votes,avg=ranking[p.id]
                row.update(predicted=pred,ore_votes=votes,neighbor_distance=round(avg,3))
        candidates.append(row)
    finished=m.ended or len(m.mined)>=5 or m.credits<10
    return {
        "session_id":session_id,"seed":m.seed,"credits":m.credits,
        "mines_left":5-len(m.mined),"scans_left":6-len(m.scanned),
        "k":m.k,"trained":m.trained,"finished":finished,
        "training":[planet_info(p,True)|{"new_scan":p.id in m.scanned} for p in training],
        "reserve":[planet_info(p) for p in m.world["reserve"] if p.id not in m.scanned],
        "candidates":candidates,
        "evaluation":({"accuracy":round(accuracy(training,m.world["validation"],m.k),4),
                       "baseline":round(baseline(training,m.world["validation"]),4),
                       "scores":{str(k):round(accuracy(training,m.world["validation"],k),4) for k in (1,3,5,7)}} if m.trained else None),
        "history":list(m.history),"event":event,
        "medal":("GOLD" if m.credits>=150 else "SILVER" if m.credits>=125 else "BRONZE" if m.credits>=100 else "EXPLORER") if finished else None
    }

@app.get("/")
def homepage():
    return FileResponse(STATIC/"index.html")

@app.get("/api/health")
def health():
    return {"ok":True,"service":"space-miner-ai","version":"0.2.0"}

@app.post("/api/missions")
def create_mission(request:NewMission):
    session_id=token_urlsafe(18)
    m=Mission(seed=request.seed,world=galaxy(request.seed))
    sessions[session_id]=m
    return snapshot(session_id,m)

@app.get("/api/missions/{session_id}")
def get_mission(session_id:str):
    return snapshot(session_id,session_or_404(session_id))

@app.post("/api/missions/{session_id}/train")
def train_model(session_id:str,request:TrainChoice):
    m=session_or_404(session_id)
    if m.ended or len(m.mined)>=5:raise HTTPException(409,"The mission has ended.")
    m.k=request.k;m.trained=True
    return snapshot(session_id,m,{"kind":"train","k":m.k})

@app.post("/api/missions/{session_id}/scan")
def scan_planet(session_id:str,request:PlanetChoice):
    m=session_or_404(session_id)
    if m.ended or len(m.mined)>=5:raise HTTPException(409,"The mission has ended.")
    found=next((p for p in m.world["reserve"] if p.id==request.planet_id),None)
    if found is None or found.id in m.scanned:raise HTTPException(400,"Choose a currently unscanned training planet.")
    if m.credits<5:raise HTTPException(400,"Not enough credits to scan.")
    m.credits-=5;m.scanned.append(found.id);m.trained=False
    return snapshot(session_id,m,{"kind":"scan","planet":planet_info(found,True),"delta":-5})

@app.get("/api/missions/{session_id}/inspect/{planet_id}")
def inspect_planet(session_id:str,planet_id:str):
    m=session_or_404(session_id)
    p=next((p for p in m.world["mining"] if p.id==planet_id),None)
    if p is None:raise HTTPException(404,"Candidate planet not found.")
    if p.id in m.mined:return {"planet":planet_info(p,True),"mined":True}
    if not m.trained:return {"planet":planet_info(p),"trained":False}
    predicted,neighbors,votes=knn(known(m),p,m.k)
    return {"planet":planet_info(p),"trained":True,"k":m.k,"predicted":predicted,
            "ore_votes":votes,"explanation":explanation(predicted,votes,m.k),
            "neighbors":[planet_info(n,True)|{"distance":round(((n.thermal-p.thermal)**2+(n.spectral-p.spectral)**2)**.5,3)} for n in neighbors]}

@app.post("/api/missions/{session_id}/mine")
def mine_planet(session_id:str,request:PlanetChoice):
    m=session_or_404(session_id)
    if m.ended:raise HTTPException(409,"The mission has ended.")
    if not m.trained:raise HTTPException(400,"Train your AI before mining.")
    p=next((p for p in m.world["mining"] if p.id==request.planet_id),None)
    if p is None:raise HTTPException(400,"Choose a valid mining candidate.")
    predicted,_,votes=knn(known(m),p,m.k)
    try: after,mined_ids=mine(m.credits,m.mined,p)
    except ValueError as exc:raise HTTPException(400,str(exc)) from exc
    old=m.credits;m.credits,m.mined=after,mined_ids
    entry={"planet_id":p.id,"ore":p.ore,"predicted":predicted,"ore_votes":votes,"k":m.k,"delta":m.credits-old}
    m.history.append(entry)
    return snapshot(session_id,m,{"kind":"mine","planet":planet_info(p,True),"entry":entry})

@app.post("/api/missions/{session_id}/end")
def finish_mission(session_id:str):
    m=session_or_404(session_id);m.ended=True
    return snapshot(session_id,m,{"kind":"end"})
