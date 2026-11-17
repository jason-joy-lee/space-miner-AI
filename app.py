import streamlit as st
import plotly.graph_objects as go
from space_miner.core import galaxy, knn, accuracy, baseline, mine

st.set_page_config(page_title="Space Miner AI", page_icon="🪐",layout="wide")
st.markdown("""<style>.stApp{background:radial-gradient(ellipse at 15% 0%,#192b53,#080e20 70%);color:#e9f2ff}h1,h2,h3{color:#e6f4ff!important}[data-testid="stMetricValue"]{color:#62edba}</style>""",unsafe_allow_html=True)

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
    s.just_mined=False

if "world" not in st.session_state: reset()
s=st.session_state
g=s.world
training=g["starter"]+[p for p in g["reserve"] if p.id in s.scanned]
st.title("✦ SPACE MINER AI")
st.caption("MISSION 01 — THE HIDDEN ORE GALAXY  ·  Real KNN  ·  Synthetic worlds")
with st.sidebar:
    st.header("COMMAND DECK")
    st.metric("Credits",s.credits)
    st.metric("Mining actions",f"{len(s.mined)}/5")
    st.metric("Known training planets",len(training))
    st.progress(len(s.mined)/5)
    st.caption(f"Galaxy seed {s.seed}")
    if st.button("↺ Replay same galaxy"):
        reset(s.seed)
        st.rerun()
    new_seed=st.number_input("New galaxy seed",value=int(s.seed+1),step=1)
    if st.button("Explore a new galaxy"):
        reset(int(new_seed))
        st.rerun()

if not s.started:
    st.subheader("Can your AI find valuable planets?")
    st.write("**Goal:** Pick five planets and earn as many credits as you can. Finding ore gives you **+15 net credits**; mining an empty planet loses **10 credits**.")
    st.info("**How to play:** ① Look at known examples → ② Train your AI → ③ Choose a planet predicted to contain ore → ④ Mine and see whether it was right → ⑤ Try another strategy.")
    st.write("**The mystery:** Every planet has two fictional sensor readings: Thermal (X) and Spectral (Y), each between 0 and 10. Planets with similar readings often have similar minerals, but not always. The chart is a **map of sensor measurements**, not a map of planet locations.")
    a,b,c=st.columns(3)
    a.metric("STARTING CREDITS",100)
    b.metric("MINING COST",10)
    c.metric("SUCCESSFUL RETURN",25)
    if st.button("🚀 START MISSION",type="primary"):
        s.started=True
        st.rerun()
    st.stop()

left,right=st.columns([1.5,1],gap="large")
with left:
    st.subheader("01 · Unknown Galaxy")
    fig=go.Figure()
    for ore,color,name in [(True,"#34e1b2","Known ore"),(False,"#ffbd60","Known empty")]:
        pts=[p for p in training if p.ore==ore]
        fig.add_trace(go.Scatter(x=[p.thermal for p in pts],y=[p.spectral for p in pts],mode="markers",
          marker=dict(size=14,color=color,symbol="diamond"),name=name,text=[p.id for p in pts],
          hovertemplate="%{text}<br>T %{x}<br>S %{y}<extra></extra>"))
    remaining=[p for p in g["mining"] if p.id not in s.mined]
    predicted=[knn(training,p,s.k)[0] for p in remaining]
    fig.add_trace(go.Scatter(x=[p.thermal for p in remaining],y=[p.spectral for p in remaining],
      mode="markers+text",text=[p.id for p in remaining],textposition="top center",
      marker=dict(size=16,color=(["#30b9f1" if x else "#9c78ef" for x in predicted] if s.trained else ["#9ca3af"]*len(remaining)),line=dict(width=1,color="white")),
      name="Unexplored",hovertemplate="%{text}<br>T %{x}<br>S %{y}<extra></extra>"))
    fig.update_layout(height=430,margin=dict(l=12,r=12,t=12,b=12),paper_bgcolor="#101a33",plot_bgcolor="#101a33",
      font=dict(color="#d3e1fc"),xaxis=dict(title="Thermal signature",range=[-.5,10.5],gridcolor="#263954"),
      yaxis=dict(title="Spectral index",range=[-.5,10.5],gridcolor="#263954"))
    st.plotly_chart(fig,use_container_width=True)
    st.info("**Read this chart:** 🟢 green diamonds = known ORE; 🟠 orange diamonds = known EMPTY. Circles = planets you may mine. Once trained, 🔵 blue circles mean AI predicts ORE; 🟣 purple circles mean AI predicts EMPTY. Gray circles have not been predicted yet.")
    with st.expander("What do the two axes actually mean?", expanded=False):
        st.write("**X — Thermal signature:** imaginary heat-sensor reading, 0–10. **Y — Spectral index:** imaginary light-sensor reading, 0–10. Neither is a real scientific unit. Each dot is one planet placed according to its two sensor numbers. Nearby dots have similar measurements — they are **not physically nearby in space**. KNN finds dots with similar measurements.")
with right:
    st.subheader("02 · Train Your AI")
    previous_k=s.k
    s.k=st.select_slider("K: How many examples should AI consult?",options=[1,3,5,7],value=s.k)
    if s.k!=previous_k: s.trained=False
    st.caption("**K=1:** trust the single closest known planet (sensitive to noise). **K=3 or 5:** let several similar examples vote (often steadier). **K=7:** smooth more, but can overlook small mineral regions. No K is always best.")
    score=accuracy(training,g["validation"],s.k)
    a,b=st.columns(2)
    a.metric("Actual KNN accuracy",f"{score:.0%}")
    b.metric("Majority baseline",f"{baseline(training,g['validation']):.0%}")
    st.caption("**Accuracy** = correct answers on 20 hidden practice-test examples. **Baseline** = score from always guessing the most common training class. Higher is generally better, but neither guarantees success on a particular planet.")
    if st.button("⚡ TRAIN AI & REVEAL PREDICTIONS",type="primary"):
        s.trained=True
        st.rerun()
    if s.trained:
        st.success(f"AI ready: {round(score*20)} / 20 validation examples correct. Blue circles are AI-predicted ore targets. Try K=1, 3, 5, 7 and re-train to compare accuracy.")
    else:
        st.warning("**Next action:** click TRAIN AI to reveal which unknown planets are predicted to contain ore.")
    st.divider()
    st.subheader("03 · Collect More Evidence")
    extra=[p for p in g["reserve"] if p.id not in s.scanned]
    if extra:
        scan=st.selectbox("Training-sector planet",extra,format_func=lambda p:f"{p.id} · Thermal {p.thermal} · Spectral {p.spectral}")
        st.caption("Scanning reveals the truth about a different training planet (not a mineable target). It gives AI one more example. Extra examples can help, but do not guarantee better accuracy.")
        if st.button("🔎 Scan planet (−5 credits)",disabled=s.credits<5):
            s.trained=False
            s.scanned.append(scan.id)
            s.credits-=5
            st.rerun()
    else: st.info("All available training planets have been scanned.")

st.divider()
st.subheader("04 · Choose Your Next Mine")
if not s.trained:
    st.info("**Step 1:** Train your AI above. After training, this section will rank the planets it predicts contain ore.")
unmined=[p for p in g["mining"] if p.id not in s.mined]
if unmined and len(s.mined)<5 and s.credits>=10 and not s.finished and s.trained:
    predictions=[(p, *knn(training,p,s.k)[::2]) for p in unmined]
    ranking=sorted(predictions,key=lambda item:(not item[1],-item[2]/s.k,item[0].id))
    st.write("**Try this:** A blue planet with many ore votes is a reasonable candidate to investigate. The vote fraction is NOT a calibrated probability — even a unanimous vote can be wrong.")
    st.dataframe([{"Planet":p.id,"AI says":"ORE ✓" if pred else "EMPTY","Ore votes":f"{votes}/{s.k}","Sensors":f"T={p.thermal}, S={p.spectral}"} for p,pred,votes in ranking],hide_index=True,use_container_width=True)
    chosen=st.selectbox("Select a planet to mine (ranked by predicted ore votes)",[r[0] for r in ranking],format_func=lambda p:f"{p.id} · Thermal {p.thermal} · Spectral {p.spectral}")
    prediction,near,votes=knn(training,chosen,s.k)
    a,b,c=st.columns(3)
    a.metric("AI prediction","ORE" if prediction else "EMPTY")
    b.metric("Neighbor votes",f"{votes} / {s.k}")
    c.metric("Cost to mine","10")
    with st.expander("🔬 BUILDER MODE — How does this prediction work?"):
        st.write("KNN measures distance to the training planets and votes among the K nearest. It does not know the true answer.")
        st.dataframe([{"Neighbor":p.id,"Ore":p.ore,"Distance":round(((p.thermal-chosen.thermal)**2+(p.spectral-chosen.spectral)**2)**.5,3)} for p in near],hide_index=True)
        st.code("distance = ((x1 - x2)**2 + (y1 - y2)**2)**0.5",language="python")
    st.caption("Cost: −10 credits. If ore is found: +25 reward (net +15). Otherwise: net −10. You have five mining attempts.")
    if st.button("⛏ MINE THIS PLANET",type="primary"):
        old=s.credits
        s.credits,s.mined=mine(s.credits,s.mined,chosen)
        s.history.append(dict(id=chosen.id,prediction=prediction,ore=chosen.ore,delta=s.credits-old))
        st.rerun()
elif s.trained:
    st.info("Mining is complete. Review your expedition below.")

if s.history:
    last=s.history[-1]
    if last["ore"]: st.success(f"✨ {last['id']} contained ore! +15 net credits.")
    else: st.warning(f"◌ {last['id']} was empty. −10 credits.")
    if last["prediction"]!=last["ore"]:
        st.info("**Why was AI wrong?** KNN copies the majority label of similar training planets, but nearby measurements do not always mean the same mineral status. Try another K or scan extra examples before your next mine.")
    else:
        st.info("**Why did AI get it right?** The nearby examples voted for the correct class. This is one result, not proof that AI will be right every time.")
    st.dataframe([{"Planet":h["id"],"AI predicted":"Ore" if h["prediction"] else "Empty","Actual":"Ore" if h["ore"] else "Empty","Credit change":h["delta"]} for h in s.history],hide_index=True,use_container_width=True)
if len(s.mined)==5 or s.credits<10 or s.finished:
    st.subheader("🏆 Expedition Report")
    medal="🥇 GOLD" if s.credits>=150 else "🥈 SILVER" if s.credits>=125 else "🥉 BRONZE" if s.credits>=100 else "Mission Complete"
    st.metric("Final credits",s.credits)
    st.write(f"**{medal}** · Successful mines {sum(h['ore'] for h in s.history)} / {len(s.history)}")
    st.caption("A higher classification accuracy does not always guarantee higher mining profit.")
elif st.button("End expedition now"):
    s.finished=True
    st.rerun()

st.caption("Educational fiction. The KNN predictions and accuracy are real calculations, not demo percentages.")
