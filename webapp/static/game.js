/* Space Miner AI: browser-only presentation; Python API owns all rules. */
(()=>{'use strict';
const $=id=>document.getElementById(id),positions=[[16,18],[38,13],[63,18],[84,24],[21,41],[40,39],[66,42],[85,51],[14,70],[36,76],[62,76],[83,79]];
let mission=null,k=3,focus='balanced',selected=null,inspection=null,playerGuess=null,inspectSeq=0,sessionSeed=12,busy=false;
const cls=id=>'p'+((Number(id.split('-')[1])-1)%12),orb=id=>'<span class="orb '+cls(id)+'"></span>';
const pct=v=>Math.round(v*100)+'%',hide=id=>$(id).hidden=true,show=id=>$(id).hidden=false;
const e=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let toastTimer;function toast(message){$('toast').textContent=message;$('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('show'),2700)}
async function api(path,method='GET',data){const opts={method,headers:{'Content-Type':'application/json'}};if(data!==undefined)opts.body=JSON.stringify(data);const res=await fetch(path,opts);let response;try{response=await res.json()}catch{throw Error('Unexpected server response')}if(!res.ok)throw Error(response.detail||'Request failed');return response}
async function act(callback){if(busy)return;busy=true;try{await callback()}catch(err){toast(err.message||'Action failed')}finally{busy=false}}
function rank(){return (mission?.candidates||[]).filter(p=>!p.mined&&p.predicted!==undefined).sort((a,b)=>Number(b.predicted)-Number(a.predicted)||b.ore_votes-a.ore_votes||a.neighbor_distance-b.neighbor_distance||a.id.localeCompare(b.id))[0]}
function cur(){return mission?.candidates.find(p=>p.id===selected)}
function render(){
if(!mission)return;
$('research').textContent=mission.research_points||0;$('credits').textContent=mission.credits;$('mines').textContent=mission.mines_left;$('status').textContent=mission.trained?'ONLINE':'OFFLINE';$('status').style.color=mission.trained?'#60efbf':'#f8b392';
$('known-count').textContent=mission.training.length+' / 14';
$('known').innerHTML=mission.training.map(p=>'<div class="known-row"><b>'+e(p.id)+(p.new_scan?' ✦':'')+'</b><i class="'+(p.ore?'':'empty-label')+'">'+(p.ore?'◆ ORE':'◌ EMPTY')+'</i></div>').join('');
$('scan-target').innerHTML=mission.reserve.map(p=>'<option value="'+e(p.id)+'">'+e(p.id)+' · Heat '+p.heat+' · Spectrum '+p.spectrum+'</option>').join('')||'<option value="">All known</option>';
$('scan').disabled=!mission.reserve.length||mission.finished||mission.credits<5;
$('train').disabled=mission.finished;
document.querySelectorAll('[data-k]').forEach(button=>button.classList.toggle('active',Number(button.dataset.k)===k));document.querySelectorAll('[data-focus]').forEach(button=>button.classList.toggle('active',button.dataset.focus===focus));$('focus-help').textContent=({balanced:'Both sensors count equally.',heat:'Heat differences count more in KNN distance.',spectrum:'Spectrum differences count more in KNN distance.'})[focus];
$('khelp').textContent=({1:'K=1 follows the single nearest example. It can be fooled by noisy data.',3:'K=3 asks the 3 most similar examples. 2/3 ORE votes predicts ore; 1/3 predicts empty.',5:'K=5 gathers a broader vote. More examples do not always mean better results.',7:'K=7 asks almost every starter example. It can overlook smaller ore clusters.'})[k];
$('train').textContent='⚡ '+(mission.trained&&k===mission.k&&focus===mission.focus?'RETRAIN AI':'TRAIN AI WITH K='+k);
$('tip').innerHTML=mission.trained?(k===mission.k&&focus===mission.focus?'AI ONLINE: inspect its real voters, make a guess, then mine.':'K changed. Click TRAIN again to update predictions.'):'STEP 1: click TRAIN AI to reveal the ore predictions.';
if(mission.evaluation){const ev=mission.evaluation;$('evaluation').innerHTML='ACCURACY ON 20 TEST PLANETS<br><strong>'+pct(ev.accuracy)+'</strong> · K='+mission.k+' · '+e(mission.focus)+' focus<small class="scores">'+Object.entries(ev.scores).map(([n,v])=>'K'+n+': '+pct(v)).join(' &nbsp; | &nbsp; ')+'</small><p class="muted">Baseline '+pct(ev.baseline)+'. These are real Python KNN test results, not guaranteed mining outcomes.</p>'}
else $('evaluation').innerHTML='TEST ACCURACY<br><strong>Not trained</strong>';
renderMap();renderDetails();renderVoterEvidence();
const best=rank();
if(best&&!mission.finished){show('recommend');$('recommend').innerHTML='<small>AI TOP RECOMMENDATION</small><strong>'+e(best.id)+'</strong><p>'+best.ore_votes+'/'+mission.k+' known neighbors have ore. Not a probability.</p><button id="inspect-best" class="outline wide">INSPECT THIS PLANET</button>';$('inspect-best').onclick=()=>choose(best.id)}else hide('recommend');
$('history').innerHTML=mission.history.length?mission.history.map(r=>'<span class="chip '+(r.ore?'good':'bad')+'">'+e(r.planet_id)+' '+(r.ore?'◆ ORE':'◌ EMPTY')+' '+(r.delta>0?'+':'')+r.delta+'</span>').join(''):'No discoveries yet.';
}
function renderMap(){
if(!mission)return;
$('planets').innerHTML=mission.candidates.map(p=>{const pos=positions[Number(p.id.split('-')[1])-1];const result=p.mined?(p.ore?'mined-ore':'mined-empty'):(mission.trained?(p.predicted?'ore':'empty'):'');const text=p.mined?(p.ore?'◆ FOUND':'◌ EMPTY'):(mission.trained?(p.predicted?'◆ ORE SIGNAL':'◌ EMPTY SIGNAL'):'UNEXPLORED');
return '<button class="node '+result+(selected===p.id?' selected':'')+'" data-id="'+p.id+'" style="left:'+pos[0]+'%;top:'+pos[1]+'%" aria-label="'+p.id+' '+text+'">'+orb(p.id)+'<b>'+p.id+'</b><small>'+text+'</small></button>'}).join('');
$('planets').querySelectorAll('button').forEach(b=>b.onclick=()=>choose(b.dataset.id));
}
function renderDetails(){
const p=cur();if(!p){$('details').innerHTML='<div class="placeholder">✧<p>Select a planet on the map to examine its readings.</p></div>';return}
let html='<div class="intel-orb">'+orb(p.id)+'</div><div class="intel-name">'+e(p.id)+'</div><div class="intel-row"><span>HEAT SENSOR</span><b>'+p.heat+' / 10</b></div><div class="intel-row"><span>SPECTRUM SENSOR</span><b>'+p.spectrum+' / 10</b></div>';
if(p.mined){html+='<div class="intel-status">'+(p.ore?'◆ CONFIRMED ORE':'◌ CONFIRMED EMPTY')+'</div><p class="muted">This result stays visible. Mine another world to continue.</p>'}
else if(!mission.trained){html+='<div class="intel-status">AI OFFLINE</div><p class="muted">Train AI to unlock its prediction for this planet.</p>'}
else{const votes=p.ore_votes;html+='<div class="intel-status">'+(p.predicted?'◆ AI PREDICTS ORE':'◌ AI PREDICTS EMPTY')+'</div><div class="votes"><strong>'+votes+' / '+mission.k+' ORE VOTES</strong><div class="vote-bar">'+Array.from({length:mission.k},(_,i)=>'<i class="'+(i<votes?'yes':'')+'"></i>').join('')+'</div><p class="muted">'+votes+' of '+mission.k+' nearest known planets have ore. '+(p.predicted?'The majority predicts ORE.':'The majority predicts EMPTY.')+' This vote is not a calibrated probability.</p></div><button id="mine" class="primary wide" '+(mission.finished?'disabled':'')+'>⛏ MINE & REVEAL (−10)</button><button id="math" class="outline wide" style="margin-top:8px">⌘ SEE NEAREST NEIGHBORS</button>'}
$('details').innerHTML=html;
if($('guess-ore'))$('guess-ore').onclick=()=>{playerGuess='ore';renderDetails()};if($('guess-empty'))$('guess-empty').onclick=()=>{playerGuess='empty';renderDetails()};if($('mine'))$('mine').onclick=()=>minePlanet(p.id);
if($('math'))$('math').onclick=math;
}
function choose(id){selected=id;renderMap();renderDetails()}
function setMission(m){mission=m;k=m.k;if(!m.candidates.some(p=>p.id===selected&&!p.mined))selected=null;render()}
function reveal(event){
if(!event)return;const p=event.planet,scan=event.kind==='scan',good=p.ore;
$('reveal-type').textContent=scan?'TRAINING SCAN DISCOVERY':'MINING RESULT';
$('reveal-orb').innerHTML=orb(p.id);
$('reveal-title').textContent=(scan?'SCAN COMPLETE · ':good?'ORE DISCOVERED · ':'EMPTY WORLD · ')+p.id;
$('reveal-message').textContent=scan?'New permanent training example: '+(good?'ORE':'EMPTY')+'. Train the AI again to use it.':'Your AI predicted '+(event.entry.predicted?'ORE':'EMPTY')+'; actual result: '+(good?'ORE':'EMPTY')+'. '+(event.entry.predicted===good?'Your prediction was correct!':'Your AI made a mistake. Try another K or scan more training examples.');
$('reveal-credits').textContent=scan?'−5 CREDITS / +1 SAMPLE':(event.entry.delta>0?'+':'')+event.entry.delta+' CREDITS';
show('reveal');
}
function end(){if(!mission)return;$('medal').textContent=mission.medal+' EXPEDITION';$('recap').textContent='Final credits: '+mission.credits+'. Ore discovered: '+mission.history.filter(x=>x.ore).length+' out of '+mission.history.length+' mines. Compare your results with another K.';show('ending')}
async function create(seed=12){await act(async()=>{sessionSeed=seed;selected=null;setMission(await api('/api/missions','POST',{seed}));hide('intro');hide('ending');hide('reveal');toast('EXPEDITION LAUNCHED · TRAIN AI WITH K=3')})}
async function train(){if(!mission)return;await act(async()=>{const d=await api('/api/missions/'+mission.session_id+'/train','POST',{k,focus});setMission(d);toast('K='+d.k+' · TEST ACCURACY '+pct(d.evaluation.accuracy))})}
async function scan(){if(!mission)return;const id=$('scan-target').value;if(!id)return;await act(async()=>{const d=await api('/api/missions/'+mission.session_id+'/scan','POST',{planet_id:id});setMission(d);reveal(d.event)})}
async function minePlanet(id){if(!mission)return;await act(async()=>{const d=await api('/api/missions/'+mission.session_id+'/mine','POST',{planet_id:id,player_guess:playerGuess});setMission(d);reveal(d.event)})}
async function math(){const p=cur();if(!mission?.trained||!p){toast('Train and select a planet first');return}await act(async()=>{const d=await api('/api/missions/'+mission.session_id+'/inspect/'+p.id);if(d.mined){toast('Select an unmined planet');return}
const X=x=>42+x*47,Y=y=>280-y*24;let svg='<svg viewBox="0 0 555 315">';
for(let i=0;i<=5;i++){let n=i*2;svg+='<line x1="'+X(n)+'" y1="30" x2="'+X(n)+'" y2="280" stroke="#314b73"/><line x1="42" y1="'+Y(n)+'" x2="512" y2="'+Y(n)+'" stroke="#314b73"/>'}
d.neighbors.forEach(n=>svg+='<line x1="'+X(p.heat)+'" y1="'+Y(p.spectrum)+'" x2="'+X(n.heat)+'" y2="'+Y(n.spectrum)+'" stroke="#b9c9f2" stroke-width="2" stroke-dasharray="5 5"/>');
mission.training.forEach(n=>svg+='<circle cx="'+X(n.heat)+'" cy="'+Y(n.spectrum)+'" r="6" fill="'+(n.ore?'#52edb8':'#ffc086')+'"/>');
svg+='<circle cx="'+X(p.heat)+'" cy="'+Y(p.spectrum)+'" r="11" fill="#fff" stroke="#28c9f2" stroke-width="3"/><text x="270" y="307" fill="#abc8e9" text-anchor="middle" font-size="12">HEAT</text><text x="15" y="165" fill="#abc8e9" transform="rotate(-90 15 165)" font-size="12">SPECTRUM</text></svg>';
$('mathplot').innerHTML=svg;$('neighbors').innerHTML=d.neighbors.map(n=>'<span class="neighbor">'+e(n.id)+' · '+(n.ore?'ORE':'EMPTY')+' · distance '+n.distance+'</span>').join('');show('learn')})}
$('launch').onclick=()=>{if(mission){hide('intro');return}create(12)};$('train').onclick=train;$('scan').onclick=scan;
$('koptions').onclick=ev=>{const b=ev.target.closest('[data-k]');if(!b)return;k=Number(b.dataset.k);render();if(mission?.trained&&k!==mission.k)toast('K CHANGED · CLICK TRAIN TO UPDATE PREDICTIONS')};
$('focus-options').onclick=ev=>{const b=ev.target.closest('[data-focus]');if(!b)return;focus=b.dataset.focus;render();if(mission?.trained&&focus!==mission.focus)toast('SENSOR FOCUS CHANGED · TRAIN TO APPLY')};$('builder').onclick=math;$('close-learn').onclick=()=>hide('learn');
$('help').onclick=()=>{$('launch').textContent='RETURN TO GAME';show('intro')};
$('restart').onclick=()=>create(sessionSeed);$('retry').onclick=()=>create(sessionSeed);$('next').onclick=()=>create(sessionSeed+1);
$('continue').onclick=()=>{hide('reveal');if(mission?.finished)end()};
$('learn').onclick=ev=>{if(ev.target===$('learn'))hide('learn')};
document.addEventListener('keydown',ev=>{if(ev.key==='Escape')hide('learn')});
})();