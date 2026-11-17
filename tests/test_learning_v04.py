"""V0.4 learning-game API: labeling does not reveal answers; comparison is real."""
from fastapi.testclient import TestClient
from webapp.server import app

client=TestClient(app)

def mission(seed=12):
    r=client.post("/api/missions",json={"seed":seed})
    assert r.status_code==200
    return r.json()

def url(m,path):
    return f"/api/missions/{m['session_id']}/{path}"

def train(m,k=3,focus="balanced"):
    r=client.post(url(m,"train"),json={"k":k,"focus":focus})
    assert r.status_code==200
    return r.json()

def test_annotation_is_provisional_and_never_leaks_hidden_truth():
    m=mission()
    target=m["reserve"][0]["id"]
    r=client.post(url(m,"label"),json={"planet_id":target,"label":"ore"})
    assert r.status_code==200
    m=r.json()
    assert m["trained"] is False
    assert len(m["training"])==9
    label=next(p for p in m["training"] if p["id"]==target)
    assert label["provisional"] is True
    assert label["verified"] is False
    assert label["ore"] is True  # this is the user's guess, not ground truth
    assert "ore" not in next(p for p in m["reserve"] if p["id"]==target)
    assert m["event"]["provisional_label"]=="ore"
    assert "label_correct" not in m["event"]
    assert all("ore" not in p for p in m["candidates"])
    assert client.post(url(m,"label"),json={"planet_id":"PX-01","label":"ore"}).status_code==400

def test_label_is_verified_by_scan_and_retrained():
    m=mission()
    p=m["reserve"][0]
    m=client.post(url(m,"label"),json={"planet_id":p["id"],"label":"empty"}).json()
    m=train(m)
    inspection=client.get(url(m,f"inspect/{m['candidates'][0]['id']}")).json()
    assert all("provisional" in n for n in inspection["neighbors"])
    scan=client.post(url(m,"scan"),json={"planet_id":p["id"]})
    assert scan.status_code==200
    m=scan.json()
    assert m["credits"]==95
    assert m["trained"] is False
    assert m["event"]["label_verified"] is True
    assert m["label_audit"][0]["planet_id"]==p["id"]
    verified=next(x for x in m["training"] if x["id"]==p["id"])
    assert verified["verified"] and not verified["provisional"]
    assert verified["ore"]==m["event"]["planet"]["ore"]
    assert client.post(url(m,"label"),json={"planet_id":p["id"],"label":"empty"}).status_code==400

def test_model_a_b_comparison_is_not_hardcoded():
    m=mission()
    assert client.post(url(m,"save-model")).status_code==400
    m=train(m,3,"balanced")
    a=client.post(url(m,"save-model"))
    assert a.status_code==200
    m=a.json()
    assert "predictions" not in m["saved_model"]
    assert m["model_comparison"]["changed_count"]==0
    first=m["model_comparison"]["before"]["validation_accuracy"]
    m=train(m,7,"balanced")
    comp=m["model_comparison"]
    assert comp["before"]["k"]==3
    assert comp["after"]["k"]==7
    assert comp["before"]["validation_accuracy"]==first
    assert comp["accuracy_delta"]==round(comp["after"]["validation_accuracy"]-first,4)
    assert comp["changed_count"]==len(comp["changed"])
    assert all("ore" not in c for c in comp["changed"])
    for c in comp["changed"]:
        assert c["before"]!=c["after"]

def test_provisional_data_can_be_revised_without_buying_secret_answers():
    m=mission()
    pid=m["reserve"][0]["id"]
    m=client.post(url(m,"label"),json={"planet_id":pid,"label":"ore"}).json()
    m=train(m)
    m=client.post(url(m,"save-model")).json()
    m=client.post(url(m,"label"),json={"planet_id":pid,"label":"empty"}).json()
    assert m["trained"] is False
    assert m["model_comparison"] is None
    assert m["research_points"]==0
    m=train(m)
    assert m["model_comparison"] is not None
