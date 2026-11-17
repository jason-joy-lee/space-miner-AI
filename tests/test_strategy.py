from space_miner.core import Planet
from space_miner.strategy import ranked_candidates, explanation


def p(name, x, y, ore):
    return Planet(name, x, y, ore)


def test_ranked_candidates_never_peek_at_candidate_label():
    train = [p("t1",0,0,True),p("t2",1,0,True),p("t3",10,10,False)]
    a=[p("mine1",.3,.1,False),p("mine2",9.5,9.5,True)]
    b=[p("mine1",.3,.1,True),p("mine2",9.5,9.5,False)]
    x=ranked_candidates(train,a,3)
    y=ranked_candidates(train,b,3)
    assert [(p.id,pred,votes,dist) for p,pred,votes,dist in x] == [
        (p.id,pred,votes,dist) for p,pred,votes,dist in y
    ]
    assert x[0][0].id == "mine1"
    assert x[0][1] is True


def test_ranking_prefers_predicted_ore_then_votes():
    train=[p("a",0,0,True),p("b",.1,.1,True),p("c",9,9,False)]
    candidates=[p("empty",9,9,False),p("ore",0,0,False)]
    ranked=ranked_candidates(train,candidates,1)
    assert ranked[0][0].id=="ore"
    assert ranked[0][2]==1


def test_explanation_is_a_vote_not_a_probability():
    message=explanation(True,2,3)
    assert "2 contained ore" in message
    assert "majority voted ORE" in message
    assert "not a guaranteed or calibrated probability" in message
