"""Space Miner AI — guided single-galaxy learning game with genuine KNN."""
from html import escape
import streamlit as st
import plotly.graph_objects as go

from space_miner.core import galaxy, knn, accuracy, baseline, mine
from space_miner.strategy import ranked_candidates, explanation

st.set_page_config(page_title="Space Miner AI", page_icon="🪐", layout="wide")
st.markdown("""
<style>
.stApp{background:radial-gradient(ellipse at 30% 0%,#1e3563,#0b1431 48%,#070e21);color:#e7f3ff}
h1,h2,h3{color:#f2f7ff!important}
[data-testid="stMetricValue"]{color:#72ecc2}
div.stButton>button{border-radius:12px;background:#1a3156;color:#edf9ff;border:1px solid #456294;font-weight:650}
div.stButton>button:hover{background:#294b78;color:white;border-color:#71dfff}
div.stButton>button[kind="primary"]{background:linear-gradient(110deg,#0788bc,#6954d2);border:0;color:white}
.mission{padding:19px 22px;border-radius:16px;background:linear-gradient(110deg,#153e66,#272055);border:1px solid #486c96}
.mission .eyebrow{color:#80e4ff;font-size:11px;letter-spacing:2px;font-weight:800}
.mission h2{margin:6px 0!important;font-size:25px}
.mission p{margin:4px 0;color:#d8eaff;font-size:13px}
.planet{border:1px solid #384e78;background:linear-gradient(155deg,#1c3156,#111d39);border-radius:14px;padding:12px;min-height:135px}
.planet.selected{border:2px solid #65daff;background:#173e64}
.planet.mined-ore{border-color:#25bf8d;background:#143c37}
.planet.mined-empty{border-color:#9f755c;background:#302b39}
.planet .orb{font-size:32px;line-height:1.25}
.planet .name{font-size:13px;font-weight:800;letter-spacing:1px;color:#dcecff}
.planet .detail{font-size:11px;color:#a9bede;margin-top:5px}
.planet .signal{font-size:12px;font-weight:750;letter-spacing:.3px}
@keyframes planet-reveal{0%{transform:scale(.82);filter:brightness(.6)}45%{transform:scale(1.15);filter:brightness(1.9)}100%{transform:scale(1);filter:brightness(1)}}
.revealed-orb{display:inline-block;font-size:65px;animation:planet-reveal 1.3s ease-in-out 1}
.reveal{padding:18px 22px;border:1px solid #49c5f5;border-radius:16px;background:linear-gradient(120deg,#133954,#272254);margin:10px 0}
.reveal h3{margin:3px 0 7px!important}
.reveal.good{border-color:#44dcac;background:linear-gradient(120deg,#103c35,#173b56)}
.reveal.bad{border-color:#d2a470;background:linear-gradient(120deg,#44302b,#1d2b46)}
.tag{display:inline-block;padding:4px 9px;border-radius:20px;background:#244168;color:#bdeaff;font-size:11px}
.step{padding:10px 13px;border:1px solid #34476d;border-radius:12px;background:#142543;font-size:13px;margin:7px 0}
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
    s.spotlight=None
    s.last_trained_k=None


if "world" not in st.session_state:
    reset()

s=st.session_state
g=s.world
training=g["starter"]+[p for p in g["reserve"] if p.id in s.scanned]
all_mining=g["mining"]
remaining=[p for p in all_mining if p.id not in s.mined]
by_id={p.id:p for p in all_mining}
orbs=["🪐","🌕","🔵","🟣","🌘","🟠","🔴","🌎","🌑","🌗","🪐","🌖"]


def planet_orb(planet):
    return orbs[int(planet.id.split("-")[-1]) % len(orbs)]


st.title("✦ SPACE MINER AI")
st.caption("MISSION 01 · THE HIDDEN ORE GALAXY | Genuine KNN, fictional sensor readings")

with st.sidebar:
    st.header("MISSION STATUS")
    st.metric("Credits",s.credits,delta=(s.history[-1]["delta"] if s.history and s.spotlight and s.spotlight["kind"]=="mine" else None))
    st.metric("Mines remaining",5-len(s.mined))
    st.metric("Known training planets",f"{len(training)}/14")
    st.progress(len(s.mined)/5)
    st.caption("Your mined planets are still shown on the board, marked with their actual results.")
    if st.button("↺ Replay same galaxy",use_container_width=True):
        reset(s.seed)
        st.rerun()
    seed=st.number_input("Try another galaxy seed",value=int(s.seed+1),step=1)
    if st.button("Explore new galaxy",use_container_width=True):
        reset(int(seed))
        st.rerun()

if not s.started:
    st.markdown("""
<div class="mission">
<div class="eyebrow">COMMANDER MOSES · INCOMING TRANSMISSION</div>
<h2>Can your AI discover the hidden ore?</h2>
<p>You have five mining attempts. Mine an ore planet and gain 15 net credits. Mine an empty one and lose 10. Train your AI using known examples, then choose where to mine.</p>
</div>""",unsafe_allow_html=True)
    a,b,c=st.columns(3)
    a.metric("Starting budget",100)
    b.metric("Successful mine","+15 net")
    c.metric("Empty mine","−10")
    st.info("**How to play:** ① Train AI → ② Inspect a recommended planet → ③ Mine → ④ Discover the truth → ⑤ Change K or scan a training example to improve.")
    st.caption("**Sensor coordinates are NOT locations in space.** Each planet has fictional Heat and Spectrum values (0–10). Similar readings can mean similar mineral outcomes.")
    if st.button("🚀 START EXPEDITION",type="primary",use_container_width=True):
        s.started=True
        st.rerun()
    st.stop()

st.markdown("""<div class="mission"><div class="eyebrow">ACTIVE MISSION · SECTOR 01</div>
<h2>THE HIDDEN ORE GALAXY</h2><p>Train your AI. Choose a target. Find ore before your mining attempts run out.</p></div>""",unsafe_allow_html=True)
st.write("")

if s.spotlight:
    event=s.spotlight
    p=event["planet"]
    is_ore=event["ore"]
    typ=event["kind"]
    header=("NEW TRAINING PLANET SCANNED" if typ=="scan" else "ORE DISCOVERED" if is_ore else "EMPTY PLANET")
    tone="good" if is_ore else "bad"
    message=(f"New labeled example added: {'ORE' if is_ore else 'EMPTY'}. Your AI now has {len(training)} known planets. Train it again to update predictions."
             if typ=="scan" else
             f"Actual result: {'ORE' if is_ore else 'EMPTY'}. AI predicted {event['prediction']}. Net credits: {event['delta']:+d}.")
    st.markdown(f"""<div class="reveal {tone}">
    <div class="tag">{escape('SCAN DISCOVERY' if typ=='scan' else 'MINING RESULT')}</div>
    <div class="revealed-orb">{planet_orb(p)}</div>
    <h3>{escape(header)} — {escape(p.id)}</h3>
    <p>{escape(message)}</p>
    <p style="color:#a9cdeb;font-size:12px">Heat {p.thermal} · Spectrum {p.spectral} · {'✅ Confirmed ore' if is_ore else '◌ Confirmed empty'}</p>
    </div>""",unsafe_allow_html=True)
    if typ=="scan":
        st.info("The newly discovered planet is now **permanently visible** in the surveyed-data list below. The ore/empty result will not disappear when you change settings.")
    elif event["prediction"] != ("ORE" if is_ore else "EMPTY"):
        st.warning("The AI prediction was incorrect. Neighbor votes are evidence, not a guarantee. Try checking other K settings or adding examples.")
    if st.button("✓ Got it — continue",type="primary"):
        s.spotlight=None
        st.rerun()

st.subheader("1 · Train your AI")
st.markdown("**The first decision:** How many known examples should the AI consult?")
control,scan_panel=st.columns([1.05,1],gap="large")
with control:
    previous_k=s.k
    s.k=st.select_slider("Choose the number of neighbors (K)",options=[1,3,5,7],value=s.k)
    if s.k!=previous_k:
        s.trained=False
    scores={k:accuracy(training,g["validation"],k) for k in (1,3,5,7)}
    comparisons=[{"K":k,"Correct out of 20":int(round(20*val)),"Accuracy":f"{val:.0%}","Selected":"◀" if k==s.k else ""} for k,val in scores.items()]
    st.dataframe(comparisons,hide_index=True,use_container_width=True)
    st.caption("These are **real** results on 20 hidden evaluation examples. A higher score means more examples classified correctly, but it does not guarantee finding ore.")
    if s.k!=3:
        st.info(f"You selected **K={s.k}**. This uses {s.k} nearby examples instead of three. After training, see whether the recommended planets change.")
    else:
        st.caption("**K=3** means three nearest examples vote. Two ore votes predicts ORE; one ore vote predicts EMPTY.")
    if st.button("⚡ TRAIN AI & REVEAL PREDICTIONS",type="primary",use_container_width=True):
        s.trained=True
        s.last_trained_k=s.k
        st.rerun()
    st.success(f"AI READY with K={s.k}. Choose a planet below.") if s.trained else st.warning("Next → Click TRAIN AI. Mining predictions stay hidden until then.")

with scan_panel:
    st.markdown("**Add more training examples (optional)**")
    st.caption("Scanning costs 5 credits and reveals the actual ore label of **one training planet**. It is not a mining target.")
    optional=[p for p in g["reserve"] if p.id not in s.scanned]
    if optional:
        target=st.selectbox("Planet to scan",optional,format_func=lambda p:f"{p.id} · Heat {p.thermal}, Spectrum {p.spectral}")
        if st.button("🔎 SCAN AND REVEAL PLANET",disabled=s.credits<5 or s.finished):
            s.scanned.append(target.id)
            s.credits-=5
            s.trained=False
            s.spotlight={"kind":"scan","planet":target,"ore":target.ore}
            st.rerun()
    else:
        st.success("All six optional training planets have been scanned.")
    with st.expander(f"📋 Surveyed planets — {len(training)} known (never disappear)"):
        st.dataframe([{"Planet":p.id,"Heat":p.thermal,"Spectrum":p.spectral,"Confirmed mineral":"💎 ORE" if p.ore else "EMPTY","Status":"NEW SCAN" if p.id in s.scanned else "STARTER"} for p in training],hide_index=True,use_container_width=True)
    st.caption("**What does K do?** K=1 trusts one neighbor; K=3 asks three; K=5 or 7 uses a broader vote. More is not always better.")

ranking=ranked_candidates(training,remaining,s.k)
if s.selected_id not in {p.id for p in remaining}:
    s.selected_id=ranking[0][0].id if ranking else None
selected=by_id.get(s.selected_id)

st.divider()
st.subheader("2 · Choose a mining target")
if not s.trained:
    st.info("Train your AI above first. The planets will display clear ore / empty recommendations once your AI is online.")
elif ranking:
    best=ranking[0]
    st.success(f"**AI's first recommendation: {best[0].id}** — {best[2]}/{s.k} nearby training planets have ore. You can choose any planet; this recommendation is not a guaranteed win.")
    st.caption("💎 **ORE signal** = most of K neighbors contain ore. 🌑 **EMPTY signal** = most do not. **2/3 ore votes predicts ORE; 1/3 ore votes predicts EMPTY.** Predictions can still be wrong.")

st.markdown("**Galaxy board — mined planets remain visible with confirmed outcomes**")
mined_results={row["id"]:row for row in s.history}
all_planets=sorted(all_mining,key=lambda p:p.id)
for start in range(0,len(all_planets),4):
    columns=st.columns(4)
    for col,p in zip(columns,all_planets[start:start+4]):
        mined_record=mined_results.get(p.id)
        pred,neighbors,votes=knn(training,p,s.k)
        if mined_record:
            status="✅ FOUND ORE" if mined_record["ore"] else "◌ CONFIRMED EMPTY"
            cardtype="mined-ore" if mined_record["ore"] else "mined-empty"
            signal="#70efbb" if mined_record["ore"] else "#f2b583"
        elif not s.trained:
            status="UNKNOWN · TRAIN AI FIRST";cardtype="";signal="#a8bad9"
        else:
            status="💎 AI: ORE" if pred else "🌑 AI: EMPTY"
            cardtype="selected" if s.selected_id==p.id else ""
            signal="#58ddf2" if pred else "#b69dfa"
        extra=f"Ore votes: {votes}/{s.k}" if s.trained and not mined_record else "Not mined yet" if not mined_record else "Mining completed"
        with col:
            st.markdown(f"""<div class="planet {cardtype}">
            <div class="orb">{planet_orb(p)}</div><div class="name">{escape(p.id)}</div>
            <div class="signal" style="color:{signal}">{escape(status)}</div>
            <div class="detail">Heat {p.thermal} · Spectrum {p.spectral}</div>
            <div class="detail">{escape(extra)}</div></div>""",unsafe_allow_html=True)
            if not mined_record:
                if st.button("✓ SELECTED" if s.selected_id==p.id else "Inspect this planet",key=f"pick-{p.id}",disabled=not s.trained or s.finished,use_container_width=True):
                    s.selected_id=p.id
                    st.rerun()
            else:
                st.caption("✓ Permanently revealed")

if selected and s.trained and not s.finished and len(s.mined)<5 and s.credits>=10:
    st.divider()
    st.subheader(f"3 · Decide whether to mine {selected.id}")
    predicted,neighbors,votes=knn(training,selected,s.k)
    decision,why=st.columns([1,1],gap="large")
    with decision:
        st.metric("AI PREDICTS","💎 ORE" if predicted else "🌑 EMPTY")
        st.metric("Ore votes",f"{votes} / {s.k}")
        st.info(f"**What does {votes}/{s.k} mean?** {votes} of the {s.k} nearest known planets contain ore. "
                f"{'The majority predicts ore.' if predicted else 'The majority predicts empty.'} "
                "This is **not** the actual mineral result.")
        st.write("⛏️ Mine costs 10 credits. If ore is found, receive 25 credits (net +15). Otherwise lose 10.")
        if st.button("⛏️ MINE — REVEAL THE TRUTH",type="primary",use_container_width=True):
            before=s.credits
            s.credits,s.mined=mine(s.credits,s.mined,selected)
            s.history.append({"id":selected.id,"prediction":"ORE" if predicted else "EMPTY","ore":selected.ore,"delta":s.credits-before})
            s.spotlight={"kind":"mine","planet":selected,"ore":selected.ore,"prediction":"ORE" if predicted else "EMPTY","delta":s.credits-before}
            s.selected_id=None
            st.rerun()
    with why:
        st.markdown("**Why did the AI predict this?**")
        st.write(explanation(predicted,votes,s.k))
        st.dataframe([{"Neighbor":p.id,"Known result":"ORE" if p.ore else "EMPTY",
            "Distance":round(((p.thermal-selected.thermal)**2+(p.spectral-selected.spectral)**2)**.5,2)} for p in neighbors],
            hide_index=True,use_container_width=True)
        with st.expander("🔬 Builder Mode — view actual KNN geometry"):
            fig=go.Figure()
            for label,color,name in [(True,"#4be2b2","Known ore"),(False,"#f9b56a","Known empty")]:
                ps=[p for p in training if p.ore==label]
                fig.add_trace(go.Scatter(x=[p.thermal for p in ps],y=[p.spectral for p in ps],mode="markers",name=name,
                    marker=dict(color=color,size=11),text=[p.id for p in ps]))
            for n in neighbors:
                fig.add_trace(go.Scatter(x=[selected.thermal,n.thermal],y=[selected.spectral,n.spectral],
                    mode="lines",line=dict(color="#82b6ff",dash="dash"),showlegend=False))
            fig.add_trace(go.Scatter(x=[selected.thermal],y=[selected.spectral],
                mode="markers",name="Selected target",marker=dict(color="#fff",size=17,symbol="star")))
            fig.update_layout(height=340,paper_bgcolor="#141f3c",plot_bgcolor="#141f3c",font=dict(color="#e7edfa"),
                xaxis=dict(title="Heat sensor score",range=[0,10],gridcolor="#30415e"),
                yaxis=dict(title="Spectrum sensor score",range=[0,10],gridcolor="#30415e"),
                margin=dict(l=8,r=8,t=8,b=8))
            st.plotly_chart(fig,use_container_width=True)
            st.caption("This is a plot of *sensor values*, not a map of physical planet positions.")
            st.code("distance = ((heat1-heat2)**2 + (spectrum1-spectrum2)**2)**0.5",language="python")

if s.history:
    st.divider()
    st.subheader("Discovery log — permanent record")
    st.dataframe([{"Planet":r["id"],"AI predicted":r["prediction"],"Actual":"ORE" if r["ore"] else "EMPTY",
                   "Credits gained/lost":r["delta"]} for r in s.history],hide_index=True,use_container_width=True)

finished=s.finished or len(s.mined)>=5 or s.credits<10
if finished:
    st.divider()
    medal="🥇 GOLD" if s.credits>=150 else "🥈 SILVER" if s.credits>=125 else "🥉 BRONZE" if s.credits>=100 else "EXPLORER"
    st.subheader("🏆 MISSION COMPLETE")
    a,b,c=st.columns(3)
    a.metric("Final credits",s.credits)
    b.metric("Ore discoveries",sum(row["ore"] for row in s.history))
    c.metric("Rank",medal)
    st.info("Try another K or scan strategy on the same seeded galaxy. Your choices can change, but hidden answers stay fixed.")
elif st.button("End expedition and see score"):
    s.finished=True
    st.rerun()

st.caption("Learning game: all sensor readings are fictional. KNN computations and held-out validation accuracy are genuine. Neighbor votes are not calibrated probabilities.")
