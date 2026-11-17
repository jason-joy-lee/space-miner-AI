"""Behavior-driven mission objectives and no hidden-label leaks."""
from fastapi.testclient import TestClient
from webapp.server import app, sessions

client=TestClient(app)

def start(seed=12):
    r=client.post("/api/missions",json={"seed":seed})
    assert r.status_code==200
    return r.json()

def api(m,path,data=None):
    u=f"/api/missions/{m['session_id']}/{path}"
    r=client.post(u,json=data or {})
    assert r.status_code==200,r.text
    return r.json()

def is_done(m,key):
    return next(x for x in m["challenges"] if x["id"]==key)["completed"]


def test_challenges_require_real_actions():
    m=start()
    assert len(m["challenges"])==7
    assert all(not x["completed"] for x in m["challenges"])
    m=api(m,"train",{"k":3,"focus":"balanced"})
    assert is_done(m,"first_signal") is True
    assert not is_done(m,"model_engineer")
    m=api(m,"save-model")
    assert not is_done(m,"model_engineer")
    m=api(m,"train",{"k":7,"focus":"heat"})
    assert is_done(m,"model_engineer") is True
    assert m["model_comparison"]["before"]["k"]==3
    assert m["model_comparison"]["after"]["k"]==7
    assert not is_done(m,"label_apprentice")
    pid=m["reserve"][0]["id"]
    m=api(m,"label",{"planet_id":pid,"label":"ore"})
    assert is_done(m,"label_apprentice")
    assert not m["trained"]


def test_wrong_label_earns_detective_only_when_verified():
    m=start()
    p=sessions[m["session_id"]].world["reserve"][0]
    wrong="empty" if p.ore else "ore"
    m=api(m,"label",{"planet_id":p.id,"label":wrong})
    assert not is_done(m,"data_detective")
    assert m["research_points"]==0
    m=api(m,"scan",{"planet_id":p.id})
    assert is_done(m,"data_detective")
    assert m["label_audit"][0]["correct"] is False
    assert m["research_points"]==0
    # The verified label corrects the player's false provisional guess.
    current=next(x for x in m["training"] if x["id"]==p.id)
    assert current["ore"]==p.ore and current["verified"]


def test_inspection_and_debrief_for_mined_target():
    m=start()
    m=api(m,"train",{"k":3})
    for p in m["candidates"][:3]:
        response=client.get(f"/api/missions/{m['session_id']}/inspect/{p['id']}")
        assert response.status_code==200
    m=client.get(f"/api/missions/{m['session_id']}").json()
    assert is_done(m,"field_researcher")
    target=m["candidates"][0]
    m=api(m,"mine",{"planet_id":target["id"],"player_guess":"ore"})
    d=m["debrief"]
    assert d["planet_id"]==target["id"]
    assert d["actual"]==m["event"]["entry"]["ore"]
    assert d["predicted"]==m["event"]["entry"]["predicted"]
    assert len(d["voter_ids"])==3
    assert len(d["next_steps"])>0
    assert all("ore" not in p for p in m["candidates"] if not p["mined"])
    # Re-fetching the score never adds a second achievement or extra XP.
    again=client.get(f"/api/missions/{m['session_id']}").json()
    assert again["research_points"]==m["research_points"]
    assert again["challenges"]==m["challenges"]
