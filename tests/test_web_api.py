"""API checks: real KNN, state integrity, and no hidden-label leaks."""
from fastapi.testclient import TestClient
from webapp.server import app, sessions

client=TestClient(app)

def start(seed=12):
    res=client.post("/api/missions",json={"seed":seed})
    assert res.status_code==200
    return res.json()

def endpoint(m,action):
    return f"/api/missions/{m['session_id']}/{action}"

def test_homepage_assets_and_health():
    assert client.get("/").status_code==200
    assert "SPACE MINER AI" in client.get("/").text
    assert client.get("/static/game.js").status_code==200
    assert client.get("/static/styles.css").status_code==200
    assert client.get("/api/health").json()["ok"] is True

def test_no_hidden_labels_until_mined():
    m=start()
    assert len(m["training"])==8
    assert len(m["candidates"])==12
    assert all("ore" not in p for p in m["candidates"])
    p=m["candidates"][0]
    detail=client.get(endpoint(m,f"inspect/{p['id']}")).json()
    assert "ore" not in detail["planet"]
    assert detail["trained"] is False
    m=client.post(endpoint(m,"train"),json={"k":3}).json()
    assert m["evaluation"]["accuracy"] >= .75
    assert m["evaluation"]["accuracy"] > m["evaluation"]["baseline"]
    detail=client.get(endpoint(m,f"inspect/{p['id']}")).json()
    assert "ore" not in detail["planet"]
    assert detail["predicted"]==(detail["ore_votes"]>=2)
    assert len(detail["neighbors"])==3
    mined=client.post(endpoint(m,"mine"),json={"planet_id":p["id"]}).json()
    assert next(x for x in mined["candidates"] if x["id"]==p["id"])["mined"]
    assert all("ore" not in x for x in mined["candidates"] if x["id"]!=p["id"])

def test_different_k_affects_recommendations():
    m=start()
    a=client.post(endpoint(m,"train"),json={"k":3}).json()
    b=client.post(endpoint(m,"train"),json={"k":7}).json()
    assert a["evaluation"]["accuracy"]==.9
    assert b["evaluation"]["accuracy"]==.55
    assert any(x.get("predicted")!=y.get("predicted") for x,y in zip(a["candidates"],b["candidates"]))

def test_scan_is_training_only_and_invalidates_model():
    m=start()
    m=client.post(endpoint(m,"train"),json={"k":3}).json()
    scanned=m["reserve"][0]["id"]
    m=client.post(endpoint(m,"scan"),json={"planet_id":scanned}).json()
    assert m["credits"]==95
    assert m["trained"] is False
    assert m["event"]["kind"]=="scan"
    assert m["event"]["planet"]["id"]==scanned
    assert "ore" in m["event"]["planet"]
    assert client.post(endpoint(m,"scan"),json={"planet_id":scanned}).status_code==400
    assert client.post(endpoint(m,"mine"),json={"planet_id":m["candidates"][0]["id"]}).status_code==400

def test_five_mine_limit_and_rewards():
    m=start()
    m=client.post(endpoint(m,"train"),json={"k":3}).json()
    ids=[p["id"] for p in m["candidates"]]
    for i in range(5):
        old=m["credits"]
        m=client.post(endpoint(m,"mine"),json={"planet_id":ids[i]}).json()
        assert m["credits"]-old in (-10,15)
    assert m["finished"] and m["mines_left"]==0
    assert client.post(endpoint(m,"mine"),json={"planet_id":ids[5]}).status_code==400

def test_isolated_sessions_and_invalid_input():
    a=start()
    b=start()
    assert a["session_id"]!=b["session_id"]
    assert a["candidates"]==b["candidates"]
    assert client.get(endpoint(b,"")).json()["history"]==[]
    assert client.post(endpoint(a,"train"),json={"k":2}).status_code==422
    assert client.post(endpoint(a,"scan"),json={"planet_id":"PX-01"}).status_code==400
    assert client.get("/api/missions/bad-session").status_code==404
