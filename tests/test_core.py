import pytest
from space_miner.core import Planet,galaxy,knn,accuracy,mine

def p(i,x,y,ore): return Planet(i,x,y,ore)

def test_seed():
    a=galaxy(42)
    assert a==galaxy(42)
    assert [len(a[k]) for k in ("starter","reserve","validation","mining")]==[8,6,20,12]
    assert len({p.id for group in a.values() for p in group})==46
    assert {p.ore for p in a["starter"]}=={True,False}

def test_knn_does_not_cheat():
    train=[p("a",0,0,True),p("b",1,0,True),p("c",9,9,False)]
    assert knn(train,p("x",.2,.2,False),3)[0] is True
    assert knn(train,p("x",.2,.2,True),3)[0] is True
    with pytest.raises(ValueError): knn(train,p("x",0,0,True),2)

def test_validation():
    t=[p("a",0,0,True),p("b",9,9,False)]
    v=[p("x",.1,.1,True),p("y",8.9,8.9,False)]
    assert accuracy(t,v,1)==1

def test_mining():
    rich=p("r",0,0,True)
    credits,seen=mine(100,set(),rich)
    assert (credits,seen)==(115,{"r"})
    with pytest.raises(ValueError): mine(credits,seen,rich)
    with pytest.raises(ValueError): mine(5,set(),rich)
    with pytest.raises(ValueError): mine(100,{"a","b","c","d","e"},rich)
