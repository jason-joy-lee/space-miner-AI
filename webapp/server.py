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

from space_miner.core import Planet, galaxy, knn, accuracy, baseline, mine, feature_distance
from space_miner.strategy import ranked_candidates, explanation

app = FastAPI(title="Space Miner AI Game API", version="0.4.0")
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
    focus: str = "balanced"
    ended: bool = False
    research_points: int = 0
    provisional_labels: dict[str, bool] = field(default_factory=dict)
    label_audit: list[dict] = field(default_factory=list)
    saved_model: dict | None = None

# Local prototype only: ephemeral in-memory sessions. Do not publicly deploy
# without authentication, persistence, rate limits and session protection.
sessions: dict[str, Mission] = {}

class NewMission(BaseModel):
    seed: int = Field(default=12, ge=0, le=1000000)

class TrainChoice(BaseModel):
    k: Literal[1, 3, 5, 7]
    focus: Literal["balanced", "heat", "spectrum"] = "balanced"

class PlanetChoice(BaseModel):
    planet_id: str

class LabelChoice(PlanetChoice):
    label: Literal["ore", "empty"]

class LabelChoice(PlanetChoice):
    label: Literal["ore", "empty"]

class MineChoice(PlanetChoice):
    player_guess: Literal["ore", "empty"] | None = None

def session_or_404(session_id: str) -> Mission:
    m=sessions.get(session_id)
    if m is None: raise HTTPException(404,"Mission not found. Create a new one.")
    return m

def known(m:Mission)->list[Planet]:
    """Never expose hidden reserve truth when a player supplies a provisional label."""
    result=list(m.world["starter"])
    for p in m.world["reserve"]:
        if p.id in m.scanned:
            result.append(p)
        elif p.id in m.provisional_labels:
            result.append(Planet(p.id,p.thermal,p.spectral,m.provisional_labels[p.id]))
    return result


def model_record(m:Mission)->dict:
    """Capture a repeatable model snapshot, without candidate ground-truth."""
    training=known(m)
    return {
        "k":m.k,"focus":m.focus,"training_count":len(training),
        "validation_accuracy":round(accuracy(training,m.world["validation"],m.k,m.focus),4),
        "predictions":{p.id:knn(training,p,m.k,m.focus)[0] for p in m.world["mining"]}
    }


def model_diff(m:Mission)->dict|None:
    if not m.trained or m.saved_model is None:return None
    before=m.saved_model
    after=model_record(m)
    changed=[{"id":p.id,"before":before["predictions"][p.id],"after":after["predictions"][p.id]}
             for p in m.world["mining"] if before["predictions"][p.id]!=after["predictions"][p.id]]
    return {
        "before":{key:value for key,value in before.items() if key!="predictions"},
        "after":{key:value for key,value in after.items() if key!="predictions"},
        "changed":changed,"changed_count":len(changed),
        "accuracy_delta":round(after["validation_accuracy"]-before["validation_accuracy"],4)
    }

def planet_info(p:Planet,ore_visible=False)->dict:
    d={"id":p.id,"heat":p.thermal,"spectrum":p.spectral}
    if ore_visible:d["ore"]=p.ore
    return d

def snapshot(session_id:str,m:Mission,event=None)->dict:
    training=known(m)
    remaining=[p for p in m.world["mining"] if p.id not in m.mined]
    ranking={p.id:(pred,votes,avg) for p,pred,votes,avg in ranked_candidates(training,remaining,m.k,m.focus)} if m.trained else {}
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
        "k":m.k,"focus":m.focus,"trained":m.trained,"finished":finished,
        "research_points":m.research_points,
        "label_audit":list(m.label_audit),
        "saved_model":({key:value for key,value in m.saved_model.items() if key!="predictions"} if m.saved_model else None),
        "model_comparison":model_diff(m),
        "training":[planet_info(p,True)|{"new_scan":p.id in m.scanned,
                           "verified":(p.id not in m.provisional_labels or p.id in m.scanned),
                           "provisional":p.id in m.provisional_labels and p.id not in m.scanned} for p in training],
        "reserve":[planet_info(p)|{"provisional_label":("ore" if m.provisional_labels[p.id] else "empty")
                    if p.id in m.provisional_labels else None}
                    for p in m.world["reserve"] if p.id not in m.scanned],
        "candidates":candidates,
        "evaluation":({"accuracy":round(accuracy(training,m.world["validation"],m.k,m.focus),4),
                       "baseline":round(baseline(training,m.world["validation"]),4),
                       "scores":{str(k):round(accuracy(training,m.world["validation"],k,m.focus),4) for k in (1,3,5,7)}} if m.trained else None),
        "history":list(m.history),"event":event,
        "medal":("GOLD" if m.credits>=150 else "SILVER" if m.credits>=125 else "BRONZE" if m.credits>=100 else "EXPLORER") if finished else None
    }

@app.get("/")
def homepage():
    return FileResponse(STATIC/"index.html")

@app.get("/api/health")
def health():
    return {"ok":True,"service":"space-miner-ai","version":"0.4.0"}

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
    m.k=request.k;m.focus=request.focus;m.trained=True
    return snapshot(session_id,m,{"kind":"train","k":m.k,"focus":m.focus})

@app.post("/api/missions/{session_id}/scan")
def scan_planet(session_id:str,request:PlanetChoice):
    m=session_or_404(session_id)
    if m.ended or len(m.mined)>=5:raise HTTPException(409,"The mission has ended.")
    found=next((p for p in m.world["reserve"] if p.id==request.planet_id),None)
    if found is None or found.id in m.scanned:raise HTTPException(400,"Choose a currently unscanned training planet.")
    if m.credits<5:raise HTTPException(400,"Not enough credits to scan.")
    m.credits-=5
    previous=m.provisional_labels.pop(found.id,None)
    m.scanned.append(found.id)
    m.trained=False
    label_correct=None if previous is None else previous==found.ore
    if previous is not None:
        m.label_audit.append({"planet_id":found.id,"player_label":"ore" if previous else "empty",
                              "verified_label":"ore" if found.ore else "empty","correct":label_correct})
        if label_correct:m.research_points+=10
    return snapshot(session_id,m,{"kind":"scan","planet":planet_info(found,True),"delta":-5,
                                  "label_verified":previous is not None,"label_correct":label_correct})

@app.post("/api/missions/{session_id}/label")
def label_training_planet(session_id:str,request:LabelChoice):
    """Player-provided label is provisional, not confirmed by the game."""
    m=session_or_404(session_id)
    if m.ended or len(m.mined)>=5:raise HTTPException(409,"Mission ended.")
    p=next((q for q in m.world["reserve"] if q.id==request.planet_id),None)
    if p is None or p.id in m.scanned:
        raise HTTPException(400,"Only unverified training planets may be labeled.")
    m.provisional_labels[p.id]=request.label=="ore"
    m.trained=False
    return snapshot(session_id,m,{"kind":"label","planet_id":p.id,
                                  "provisional_label":request.label})


@app.post("/api/missions/{session_id}/save-model")
def save_model(session_id:str):
    m=session_or_404(session_id)
    if not m.trained:raise HTTPException(400,"Train a model before saving Model A.")
    if m.ended or len(m.mined)>=5:raise HTTPException(409,"Mission ended.")
    m.saved_model=model_record(m)
    return snapshot(session_id,m,{"kind":"save-model",
                         "message":"Model A saved. Change K, sensors or labels, then retrain."})


@app.get("/api/missions/{session_id}/inspect/{planet_id}")
def inspect_planet(session_id:str,planet_id:str):
    m=session_or_404(session_id)
    p=next((p for p in m.world["mining"] if p.id==planet_id),None)
    if p is None:raise HTTPException(404,"Candidate planet not found.")
    if p.id in m.mined:return {"planet":planet_info(p,True),"mined":True}
    if not m.trained:return {"planet":planet_info(p),"trained":False}
    predicted,neighbors,votes=knn(known(m),p,m.k,m.focus)
    scouting=sorted((q for q in m.world["reserve"] if q.id not in m.scanned),
                   key=lambda q:(feature_distance(q,p,m.focus),q.id))
    return {"planet":planet_info(p),"trained":True,"k":m.k,"predicted":predicted,
            "ore_votes":votes,"focus":m.focus,"explanation":explanation(predicted,votes,m.k),
            "scout_options":[planet_info(q)|{"distance":round(feature_distance(q,p,m.focus),3)} for q in scouting[:3]],
            "neighbors":[planet_info(n,True)|{"provisional":(n.id in m.provisional_labels and n.id not in m.scanned),"distance":round(feature_distance(n,p,m.focus),3)} for n in neighbors]}

@app.post("/api/missions/{session_id}/mine")
def mine_planet(session_id:str,request:MineChoice):
    m=session_or_404(session_id)
    if m.ended:raise HTTPException(409,"The mission has ended.")
    if not m.trained:raise HTTPException(400,"Train your AI before mining.")
    p=next((p for p in m.world["mining"] if p.id==request.planet_id),None)
    if p is None:raise HTTPException(400,"Choose a valid mining candidate.")
    predicted,_,votes=knn(known(m),p,m.k,m.focus)
    try: after,mined_ids=mine(m.credits,m.mined,p)
    except ValueError as exc:raise HTTPException(400,str(exc)) from exc
    old=m.credits;m.credits,m.mined=after,mined_ids
    guess_correct = None if request.player_guess is None else (request.player_guess=="ore")==p.ore
    if guess_correct: m.research_points+=20
    entry={"planet_id":p.id,"ore":p.ore,"predicted":predicted,"ore_votes":votes,
           "k":m.k,"focus":m.focus,"delta":m.credits-old,
           "player_guess":request.player_guess,"guess_correct":guess_correct}
    m.history.append(entry)
    return snapshot(session_id,m,{"kind":"mine","planet":planet_info(p,True),"entry":entry})

@app.post("/api/missions/{session_id}/end")
def finish_mission(session_id:str):
    m=session_or_404(session_id);m.ended=True
    return snapshot(session_id,m,{"kind":"end"})
