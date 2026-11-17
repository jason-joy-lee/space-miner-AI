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
    st.write("You have 100 credits and five mining attempts. Each mine costs 10 credits. A mineral-rich planet returns 25. Scan training planets for 5 credits, or trust your AI's predictions.")
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
      marker=dict(size=16,color=["#30b9f1" if x else "#9c78ef" for x in predicted],line=dict(width=1,color="white")),
      name="Unexplored",hovertemplate="%{text}<br>T %{x}<br>S %{y}<extra></extra>"))
    fig.update_layout(height=430,margin=dict(l=12,r=12,t=12,b=12),paper_bgcolor="#101a33",plot_bgcolor="#101a33",
      font=dict(color="#d3e1fc"),xaxis=dict(title="Thermal signature",range=[-.5,10.5],gridcolor="#263954"),
      yaxis=dict(title="Spectral index",range=[-.5,10.5],gridcolor="#263954"))
    st.plotly_chart(fig,use_container_width=True)
    st.caption("Diamonds = surveyed examples. Circles = mining candidates, colored by AI prediction. Axes show fictional sensor features, not physical space.")
with right:
    st.subheader("02 · Train Your AI")
    s.k=st.select_slider("K: Number of neighbors",options=[1,3,5,7],value=s.k)
    score=accuracy(training,g["validation"],s.k)
    a,b=st.columns(2)
    a.metric("Actual KNN accuracy",f"{score:.0%}")
    b.metric("Majority baseline",f"{baseline(training,g['validation']):.0%}")
    st.caption("Calculated from 20 separate validation planets. Mining labels stay hidden.")
    if st.button("⚡ TRAIN / RE-EVALUATE",type="primary"):
        st.success(f"Model evaluated: {round(score*20)} of 20 validation predictions correct. KNN votes among its nearest known examples.")
    st.divider()
    st.subheader("03 · Collect More Evidence")
    extra=[p for p in g["reserve"] if p.id not in s.scanned]
    if extra:
        scan=st.selectbox("Training-sector planet",extra,format_func=lambda p:f"{p.id} · Thermal {p.thermal} · Spectral {p.spectral}")
        if st.button("🔎 Scan planet (−5 credits)",disabled=s.credits<5):
            s.scanned.append(scan.id)
            s.credits-=5
            st.rerun()
    else: st.info("All available training planets have been scanned.")

st.divider()
st.subheader("04 · Choose Your Next Mine")
unmined=[p for p in g["mining"] if p.id not in s.mined]
if unmined and len(s.mined)<5 and s.credits>=10 and not s.finished:
    chosen=st.selectbox("Candidate planet",unmined,format_func=lambda p:f"{p.id} · Thermal {p.thermal} · Spectral {p.spectral}")
    prediction,near,votes=knn(training,chosen,s.k)
    a,b,c=st.columns(3)
    a.metric("AI prediction","ORE" if prediction else "EMPTY")
    b.metric("Neighbor votes",f"{votes} / {s.k}")
    c.metric("Cost to mine","10")
    with st.expander("🔬 BUILDER MODE — How does this prediction work?"):
        st.write("KNN measures distance to the training planets and votes among the K nearest. It does not know the true answer.")
        st.dataframe([{"Neighbor":p.id,"Ore":p.ore,"Distance":round(((p.thermal-chosen.thermal)**2+(p.spectral-chosen.spectral)**2)**.5,3)} for p in near],hide_index=True)
        st.code("distance = ((x1 - x2)**2 + (y1 - y2)**2)**0.5",language="python")
    if st.button("⛏ MINE THIS PLANET",type="primary"):
        old=s.credits
        s.credits,s.mined=mine(s.credits,s.mined,chosen)
        s.history.append(dict(id=chosen.id,prediction=prediction,ore=chosen.ore,delta=s.credits-old))
        st.rerun()
else:
    st.info("Mining is complete. Review your expedition below.")

if s.history:
    last=s.history[-1]
    if last["ore"]: st.success(f"✨ {last['id']} contained ore! +15 net credits.")
    else: st.warning(f"◌ {last['id']} was empty. −10 credits.")
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
