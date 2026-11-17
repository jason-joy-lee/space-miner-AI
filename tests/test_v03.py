"""V0.3 — player agency and honest nearest-neighbor evidence."""
from fastapi.testclient import TestClient

from space_miner.core import Planet, feature_distance, knn, galaxy
from webapp.server import app

client=TestClient(app)

def start(seed=12):
    response=client.post("/api/missions",json={"seed":seed})
    assert response.status_code==200
    return response.json()

def url(state,path):
    return f"/api/missions/{state['session_id']}/{path}"

def test_focus_changes_real_distances_and_can_change_the_nearest_neighbor():
    a=Planet("A",0,2,True)
    b=Planet("B",2,0,False)
    target=Planet("T",.5,.5,False)
    # Two sensors have noninterchangeable effects on weighted distance.
    assert feature_distance(a,target,"heat") < feature_distance(b,target,"heat")
    assert feature_distance(a,target,"spectrum") > feature_distance(b,target,"spectrum")
    assert knn([a,b],target,1,"heat")[0] is True
    assert knn([a,b],target,1,"spectrum")[0] is False

def test_focus_training_and_voter_provenance():
    state=start()
    res=client.post(url(state,"train"),json={"k":3,"focus":"heat"})
    assert res.status_code==200
    state=res.json()
    assert state["focus"]=="heat"
    assert len(state["evaluation"]["scores"])==4
    p=state["candidates"][0]
    inspect=client.get(url(state,f"inspect/{p['id']}")).json()
    assert inspect["focus"]=="heat"
    assert len(inspect["neighbors"])==3
    assert all("ore" in n and "distance" in n for n in inspect["neighbors"])
    training_ids={n["id"] for n in state["training"]}
    assert all(n["id"] in training_ids for n in inspect["neighbors"])
    assert "ore" not in inspect["planet"]
    assert inspect["predicted"] == (sum(n["ore"] for n in inspect["neighbors"])>=2)

def test_personal_prediction_earns_points_without_changing_ore():
    state=start()
    state=client.post(url(state,"train"),json={"k":3}).json()
    chosen=state["candidates"][0]["id"]
    wrong_or_right="ore"
    r=client.post(url(state,"mine"),json={"planet_id":chosen,"player_guess":wrong_or_right})
    assert r.status_code==200
    state=r.json()
    entry=state["event"]["entry"]
    assert entry["player_guess"]==wrong_or_right
    assert entry["guess_correct"] == entry["ore"]
    assert state["research_points"]==(20 if entry["ore"] else 0)
    assert state["credits"]==100+(15 if entry["ore"] else -10)
    assert client.post(url(state,"mine"),json={"planet_id":chosen,"player_guess":"empty"}).status_code==400

def test_bad_focus_and_guess_are_rejected():
    state=start()
    assert client.post(url(state,"train"),json={"k":3,"focus":"secret"}).status_code==422
    state=client.post(url(state,"train"),json={"k":3,"focus":"balanced"}).json()
    assert client.post(url(state,"mine"),json={
        "planet_id":state["candidates"][0]["id"],"player_guess":"maybe"
    }).status_code==422

def test_strategy_reproducible():
    assert galaxy(12)==galaxy(12)
    a=start(12)
    b=start(12)
    a=client.post(url(a,"train"),json={"k":5,"focus":"spectrum"}).json()
    b=client.post(url(b,"train"),json={"k":5,"focus":"spectrum"}).json()
    assert a["candidates"]==b["candidates"]
    assert a["evaluation"]==b["evaluation"]

def test_targeted_scouting_never_exposes_hidden_reserve_labels():
    state=start()
    state=client.post(url(state,"train"),json={"k":3,"focus":"heat"}).json()
    selected=state["candidates"][0]
    details=client.get(url(state,f"inspect/{selected['id']}")).json()
    scouts=details["scout_options"]
    assert len(scouts)==3
    assert all("ore" not in scout for scout in scouts)
    assert scouts==sorted(scouts,key=lambda scout:(scout["distance"],scout["id"]))
    ids={p["id"] for p in state["reserve"]}
    assert all(q["id"] in ids for q in scouts)
    new_state=client.post(url(state,"scan"),json={"planet_id":scouts[0]["id"]}).json()
    assert new_state["trained"] is False
    assert new_state["credits"]==95
