"""Space Miner AI — mission-first playable Streamlit interface."""
import streamlit as st
import plotly.graph_objects as go
from space_miner.core import galaxy, knn, accuracy, baseline, mine
from space_miner.strategy import ranked_candidates, explanation

st.set_page_config(page_title="Space Miner AI", page_icon="🪐", layout="wide")
st.markdown("""
<style>
.stApp {background:radial-gradient(ellipse at 25% 0%,#20396a 0%,#0b1330 48%,#070d1b 100%);color:#e8f4ff}
h1,h2,h3 {color:#f1f7ff!important}
div[data-testid="stVerticalBlockBorderWrapper"] {border-color:#394a76}
[data-testid="stMetricValue"] {color:#75eed0}
div.stButton>button {border-radius:11px;border-color:#455d89;background:#1b3156;color:#e6f7ff;font-weight:650}
div.stButton>button:hover {border-color:#60d8ff;color:#fff;background:#294674}
div.stButton>button[kind="primary"] {background:linear-gradient(110deg,#007eb8,#6653d1);border:0;color:white}
.planet-card{padding:10px 13px;border:1px solid #384e7e;border-radius:14px;background:linear-gradient(145deg,#182a4e,#111d39);min-height:115px}
.planet-orb{font-size:34px;line-height:1.2}
.planet-card .code{font-size:13px;letter-spacing:1px;color:#bcdafa;font-weight:750}
.planet-card .feature{font-size:11px;color:#9eb6d5;margin-top:5px}
.mission-banner{padding:20px;border-radius:16px;background:linear-gradient(110deg,#173a61,#251c51);border:1px solid #4a608b}
.mission-banner .eyebrow{font-size:11px;color:#88dbf7;letter-spacing:2px;font-weight:750}
.mission-banner h2{margin:7px 0!important;font-size:25px}
.mission-banner .sub{color:#d4deff;font-size:13px}
.flash-good{padding:17px;background:#103d39;border:1px solid #4ce7b7;border-radius:14px}
.flash-bad{padding:17px;background:#49302e;border:1px solid #f6ad79;border-radius:14px}
.help-text{font-size:12px;color:#b3c7eb}
</style>
""", unsafe_allow_html=True)


def reset(seed=42):
    s=st.session_state
    s.seed=seed
    s.world=galaxy(seed)
    s.credits=100
    s.scanned=[]
    s.mined=set()
    s.history=[]
    s.k=3
    s.started=False
    s.finished=False
    s.trained=False
    s.selected_id=None
    s.reveal_id=None
    s.tutorial=True


if "world" not in st.session_state:
    reset()

s=st.session_state
g=s.world
training=g["starter"] + [p for p in g["reserve"] if p.id in s.scanned]
remaining=[p for p in g["mining"] if p.id not in s.mined]
by_id={p.id:p for p in g["mining"]}

st.title("✦ SPACE MINER AI")
st.caption("MISSION 01  /  THE HIDDEN ORE GALAXY  ·  A real KNN strategy game")
with st.sidebar:
    st.header("COMMAND DECK")
    st.metric("Credits",s.credits,delta=s.history[-1]["delta"] if s.history else None)
    st.metric("Mining attempts",f"{len(s.mined)} / 5")
    st.metric("Known examples",len(training))
    st.progress(len(s.mined)/5)
    st.caption(f"Galaxy seed: {s.seed}")
    if st.button("↺ Replay same galaxy",use_container_width=True):
        reset(s.seed)
        st.rerun()
    seed=st.number_input("Next galaxy seed",value=int(s.seed+1),step=1)
    if st.button("Explore new galaxy",use_container_width=True):
        reset(int(seed))
        st.rerun()

if not s.started:
    st.markdown("""
<div class="mission-banner">
 <div class="eyebrow">INCOMING TRANSMISSION · COMMANDER MOSES</div>
 <h2>Find the hidden ore. Outsmart the galaxy.</h2>
 <div class="sub">Your AI knows eight surveyed planets. You have five mining attempts to find as much ore as possible. Can you finish with more credits than you started?</div>
</div>""",unsafe_allow_html=True)
    a,b,c=st.columns(3)
    a.metric("Starting credits","100")
    b.metric("Each mine","−10")
    c.metric("Ore reward","+25")
    st.info("**Your plan:** ① Train your AI → ② Choose a blue planet → ③ Inspect its neighbors → ④ Mine to reveal the truth → ⑤ Improve your strategy.")
    st.caption("The sensors are fictional: Thermal and Spectral scores (0–10). They describe planet properties, **not actual positions in space**. Similar sensor readings often suggest similar mineral content.")
    if st.button("🚀 START EXPEDITION",type="primary",use_container_width=True):
        s.started=True
        st.rerun()
    st.stop()

st.markdown('<div class="mission-banner"><div class="eyebrow">ACTIVE MISSION · SECTOR 01</div><h2>THE HIDDEN ORE GALAXY</h2><div class="sub">Find valuable ore with limited mining attempts. Your AI sees sensor signals, not hidden mineral deposits.</div></div>',unsafe_allow_html=True)
st.write("")
a,b,c=st.columns(3)
a.metric("Credits remaining",s.credits)
b.metric("Mines left",5-len(s.mined))
c.metric("Known training planets",len(training))

if s.reveal_id:
    last=s.history[-1]
    if last["ore"]:
        st.markdown(f'<div class="flash-good"><strong>💎 ORE DISCOVERED — {last["id"]}!</strong><br>Mining cost −10, reward +25 → <strong>+15 net credits</strong>. Your AI predicted {"ORE" if last["prediction"] else "EMPTY"}.</div>',unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="flash-bad"><strong>🌑 EMPTY PLANET — {last["id"]}</strong><br>No reward; you spent <strong>10 credits</strong>. Your AI predicted {"ORE" if last["prediction"] else "EMPTY"}.</div>',unsafe_allow_html=True)
    if last["prediction"] != last["ore"]:
        st.caption("The AI was wrong! Similar sensor readings do not always imply identical ore labels. More training samples or a different K may help — but neither guarantees success.")
    if st.button("Continue exploring →",type="primary"):
        s.reveal_id=None
        st.rerun()

if s.tutorial:
    with st.container(border=True):
        st.markdown("#### 👋 First mission? Here's the trick.")
        st.write("The **small known sample** is what your AI learns from. **Blue planets** are predicted to have ore; **purple planets** are predicted empty. Your job is to decide which to risk a mining attempt on.")
        st.write("**K** means how many similar known examples vote on each prediction. Try K=3 first. You can change it later and compare how the predictions change.")
        if st.button("Got it — hide tips"):
            s.tutorial=False
            st.rerun()

st.subheader("1 · Train your AI")
controls, scanbox=st.columns([1.1,1],gap="large")
with controls:
    s.k=st.select_slider("How many neighbors should vote? (K)",options=[1,3,5,7],value=s.k)
    score=accuracy(training,g["validation"],s.k)
    base=baseline(training,g["validation"])
    x,y=st.columns(2)
    x.metric("KNN validation accuracy",f"{score:.0%}")
    y.metric("Simple baseline",f"{base:.0%}")
    st.caption("Tested on 20 separate examples. Accuracy is calculated by KNN, **not invented**. Validation planets are not mineable targets.")
    if st.button("⚡ TRAIN AI / REFRESH PREDICTIONS",type="primary",use_container_width=True):
        s.trained=True
        st.rerun()
    if s.trained:
        st.success("AI ONLINE. Your predictions appear in the planet cards below.")
    else:
        st.warning("Train your AI to reveal which planets it thinks contain ore.")
with scanbox:
    st.markdown("**Improve your training examples**")
    st.caption("A scan costs 5 credits and reveals an additional *training-sector* planet, not a mining target. It might help accuracy, but not always.")
    extra=[p for p in g["reserve"] if p.id not in s.scanned]
    if extra:
        survey=st.selectbox("Scan a new training planet",extra,format_func=lambda p:f"{p.id} · Heat {p.thermal} · Spectrum {p.spectral}")
        if st.button("🔎 SCAN FOR 5 CREDITS",disabled=s.credits<5 or s.finished):
            s.scanned.append(survey.id)
            s.credits-=5
            s.trained=False
            st.rerun()
    else:
        st.info("All six optional training samples have been collected.")
    with st.expander("How should I choose K?"):
        st.write("**K=1:** nearest single example, easily fooled by noisy data. **K=3 or 5:** more examples vote; often steadier. **K=7:** broad voting can miss smaller ore clusters. There is no universally best K.")
        st.write("Look at validation accuracy to compare settings. That score estimates performance on new examples, but does not guarantee any single mine.")

# Compute the ranking only AFTER Streamlit has read the current K selection.
ranking=ranked_candidates(training,remaining,s.k)
if s.selected_id not in {p.id for p in remaining}:
    s.selected_id=ranking[0][0].id if ranking else None
selected=by_id.get(s.selected_id)

st.divider()
st.subheader("2 · Choose a planet")
st.caption("Select a planet card below. The colored prediction is based on real KNN results; ore is not revealed until you mine.")
if not s.trained:
    st.info("Next step → Click **TRAIN AI** above. Planet cards are intentionally unexplored until then.")
else:
    st.markdown("**AI suggestion:** Start by inspecting a blue planet with several ore votes. Vote fractions are not calibrated probabilities.")
    if ranking:
        best=ranking[0]
        st.caption(f"Top current AI recommendation: **{best[0].id}** · predicted {'ORE' if best[1] else 'EMPTY'} · {best[2]}/{s.k} ore votes.")

orbs=["🪐","🌑","🌎","🔴","🌕","🟠","🔵","🪐","🌗","🟣","🛰️","🌖"]
for offset in range(0,len(ranking),4):
    cols=st.columns(4)
    for j,row in enumerate(ranking[offset:offset+4]):
        planet,pred,votes,_=row
        original=int(planet.id.split("-")[-1])-1
        color=("#55d6ff" if pred else "#b39cff") if s.trained else "#b6bfd8"
        label=("ORE SIGNAL" if pred else "EMPTY SIGNAL") if s.trained else "UNEXPLORED"
        with cols[j]:
            st.markdown(f"""<div class="planet-card">
            <div class="planet-orb">{orbs[original%len(orbs)]}</div>
            <div class="code">{planet.id}</div>
            <div style="font-size:11px;color:{color};font-weight:750">{label}</div>
            <div class="feature">Heat {planet.thermal} · Spectrum {planet.spectral}</div>
            {f'<div class="feature">Ore votes: {votes}/{s.k}</div>' if s.trained else ''}
            </div>""",unsafe_allow_html=True)
            selected_label="✓ SELECTED" if s.selected_id==planet.id else "Inspect planet"
            if st.button(selected_label,key=f"select-{planet.id}",use_container_width=True):
                s.selected_id=planet.id
                st.rerun()

if selected and s.trained and not s.finished and len(s.mined)<5 and s.credits>=10:
    st.divider()
    st.subheader(f"3 · Planet {selected.id} — Mining Decision")
    decision,detail=st.columns([1.0,1.15],gap="large")
    result,neighbors,votes=knn(training,selected,s.k)
    with decision:
        st.metric("AI prediction","💎 ORE" if result else "🌑 EMPTY")
        st.metric("Known ore votes",f"{votes} / {s.k}")
        st.write(explanation(result,votes,s.k))
        st.caption("Mining: −10 credits. Found ore: +25 reward (net +15). No ore: −10 net.")
        if st.button("⛏ MINE THIS PLANET",type="primary",use_container_width=True):
            previous=s.credits
            s.credits,s.mined=mine(s.credits,s.mined,selected)
            s.history.append({"id":selected.id,"prediction":result,"ore":selected.ore,"delta":s.credits-previous})
            s.reveal_id=selected.id
            s.selected_id=None
            st.rerun()
    with detail:
        st.markdown("**Why did the AI choose that?**")
        st.write("These are its nearest surveyed examples. Each example gets one vote.")
        rows=[{"Example":p.id,"Known result":"💎 ORE" if p.ore else "EMPTY",
               "Distance":round(((p.thermal-selected.thermal)**2+(p.spectral-selected.spectral)**2)**.5,2)}
              for p in neighbors]
        st.dataframe(rows,hide_index=True,use_container_width=True)
        st.caption("Smaller distances mean more similar **sensor measurements**, not physically closer stars.")
        with st.expander("🔬 BUILDER MODE · Show the math and feature map"):
            fig=go.Figure()
            for label,color,name in [(True,"#4ae4b1","Known ore"),(False,"#ffb85b","Known empty")]:
                pts=[p for p in training if p.ore==label]
                fig.add_trace(go.Scatter(x=[p.thermal for p in pts],y=[p.spectral for p in pts],mode="markers",name=name,
                    marker=dict(size=12,color=color),text=[p.id for p in pts],
                    hovertemplate="%{text}<br>Heat %{x}<br>Spectrum %{y}<extra></extra>"))
            for p in neighbors:
                fig.add_trace(go.Scatter(x=[selected.thermal,p.thermal],y=[selected.spectral,p.spectral],
                    mode="lines",line=dict(color="#91c4ff",width=2,dash="dash"),showlegend=False,hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=[selected.thermal],y=[selected.spectral],mode="markers",name="Selected",
                marker=dict(symbol="star",size=18,color="#ffffff")))
            fig.update_layout(height=360,margin=dict(l=8,r=8,t=8,b=8),paper_bgcolor="#151f3b",
                plot_bgcolor="#151f3b",font=dict(color="#cce4ff"),
                xaxis=dict(title="Thermal sensor value (0–10)",range=[0,10],gridcolor="#34415c"),
                yaxis=dict(title="Spectral sensor value (0–10)",range=[0,10],gridcolor="#34415c"))
            st.plotly_chart(fig,use_container_width=True)
            st.code("distance = ((heat_1 - heat_2)**2 + (spectrum_1 - spectrum_2)**2)**0.5",language="python")
            st.caption("This chart is a 2D **feature space**, not a geographic star map.")

if s.history:
    st.divider()
    st.subheader("Expedition log")
    st.dataframe([{"Planet":h["id"],"Predicted":"Ore" if h["prediction"] else "Empty",
                   "Actual":"Ore" if h["ore"] else "Empty","Credit change":h["delta"]}
                  for h in s.history],hide_index=True,use_container_width=True)

finished=s.finished or len(s.mined)==5 or s.credits<10
if finished:
    st.divider()
    st.subheader("🏆 EXPEDITION COMPLETE")
    medal="GOLD" if s.credits>=150 else "SILVER" if s.credits>=125 else "BRONZE" if s.credits>=100 else "EXPLORER"
    a,b,c=st.columns(3)
    a.metric("Final credits",s.credits)
    b.metric("Ore discoveries",sum(h["ore"] for h in s.history))
    c.metric("Medal",medal)
    st.info("Try the same galaxy with a different K or more training examples. Compare results — don't assume your last strategy will always win.")
elif st.button("End expedition and review score"):
    s.finished=True
    st.rerun()

st.caption("All planets and sensor readings are synthetic. KNN prediction, voting and held-out evaluation use real calculations. No external LLM is involved.")
