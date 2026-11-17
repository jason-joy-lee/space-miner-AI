/* Space Miner AI: browser-only presentation; Python API owns all rules. */
(()=>{'use strict';
const $=id=>document.getElementById(id),positions=[[16,18],[38,13],[63,18],[84,24],[21,41],[40,39],[66,42],[85,51],[14,70],[36,76],[62,76],[83,79]];
let mission=null,k=3,focus='balanced',selected=null,inspection=null,playerGuess=null,inspectSeq=0,sessionSeed=12,busy=false;
let tutorialStep=-1,voterStep=-1,voterData=null,trainingSeen=false;
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
$('known').innerHTML=mission.training.map(p=>'<div class="known-row"><b>'+e(p.id)+(p.new_scan?' ✦':'')+(p.provisional?' [DRAFT]':'')+'</b><i class="'+(p.ore?'':'empty-label')+'">'+(p.ore?'◆ ORE':'◌ EMPTY')+'</i></div>').join('');
$('scan-target').innerHTML=mission.reserve.map(p=>'<option value="'+e(p.id)+'">'+e(p.id)+' · Heat '+p.heat+' · Spectrum '+p.spectrum+'</option>').join('')||'<option value="">All known</option>';
$('scan').disabled=!mission.reserve.length||mission.finished||mission.credits<5;
$('train').disabled=mission.finished;
document.querySelectorAll('[data-k]').forEach(button=>button.classList.toggle('active',Number(button.dataset.k)===k));document.querySelectorAll('[data-focus]').forEach(button=>button.classList.toggle('active',button.dataset.focus===focus));$('focus-help').textContent=({balanced:'Both sensors count equally.',heat:'Heat differences count more in KNN distance.',spectrum:'Spectrum differences count more in KNN distance.'})[focus];
$('khelp').textContent=({1:'K=1 follows the single nearest example. It can be fooled by noisy data.',3:'K=3 asks the 3 most similar examples. 2/3 ORE votes predicts ore; 1/3 predicts empty.',5:'K=5 gathers a broader vote. More examples do not always mean better results.',7:'K=7 asks almost every starter example. It can overlook smaller ore clusters.'})[k];
$('train').textContent='⚡ '+(mission.trained&&k===mission.k&&focus===mission.focus?'RETRAIN AI':'TRAIN AI WITH K='+k);
$('tip').innerHTML=mission.trained?(k===mission.k&&focus===mission.focus?'AI ONLINE: inspect its real voters, make a guess, then mine.':'K changed. Click TRAIN again to update predictions.'):'STEP 1: click TRAIN AI to reveal the ore predictions.';
if(mission.evaluation){const ev=mission.evaluation;$('evaluation').innerHTML='ACCURACY ON 20 TEST PLANETS<br><strong>'+pct(ev.accuracy)+'</strong> · K='+mission.k+' · '+e(mission.focus)+' focus<small class="scores">'+Object.entries(ev.scores).map(([n,v])=>'K'+n+': '+pct(v)).join(' &nbsp; | &nbsp; ')+'</small><p class="muted">Baseline '+pct(ev.baseline)+'. These are real Python KNN test results, not guaranteed mining outcomes.</p>'}
else $('evaluation').innerHTML='TEST ACCURACY<br><strong>Not trained</strong>';
renderMap();renderDetails();renderVoterEvidence();renderDecision();renderLab();renderTutorial();renderChallenges();renderDebrief();
const best=rank();
if(best&&!mission.finished&&!selected){show('recommend');$('recommend').innerHTML='<small>AI TOP RECOMMENDATION</small><strong>'+e(best.id)+'</strong><p>'+best.ore_votes+'/'+mission.k+' known neighbors have ore. Not a probability.</p><button id="inspect-best" class="outline wide">INSPECT THIS PLANET</button>';$('inspect-best').onclick=()=>choose(best.id)}else hide('recommend');
$('history').innerHTML=mission.history.length?mission.history.map(r=>'<span class="chip '+(r.ore?'good':'bad')+'">'+e(r.planet_id)+' '+(r.ore?'◆ ORE':'◌ EMPTY')+' '+(r.delta>0?'+':'')+r.delta+'</span>').join(''):'No discoveries yet.';
}
function renderMap(){
if(!mission)return;
$('planets').innerHTML=mission.candidates.map(p=>{const pos=positions[Number(p.id.split('-')[1])-1];const result=p.mined?(p.ore?'mined-ore':'mined-empty'):(mission.trained?(p.predicted?'ore':'empty'):'');const text=p.mined?(p.ore?'◆ FOUND':'◌ EMPTY'):(mission.trained?(p.predicted?'◆ ORE SIGNAL':'◌ EMPTY SIGNAL'):'UNEXPLORED');
return '<button class="node '+result+(selected===p.id?' selected':'')+'" data-id="'+p.id+'" style="left:'+pos[0]+'%;top:'+pos[1]+'%" aria-label="'+p.id+' '+text+'">'+orb(p.id)+'<b>'+p.id+'</b><small>'+text+'</small></button>'}).join('');
$('planets').querySelectorAll('button').forEach(b=>b.onclick=()=>choose(b.dataset.id));
}
function renderDetails(){
const p=cur(),el=$('details');
if(!p){el.innerHTML='<div class="placeholder">✧<p>Select a planet on the galaxy map to inspect its sensor readings.</p></div>';return}
const confirmed=p.mined?('<div class="intel-status">'+(p.ore?'◆ CONFIRMED ORE':'◌ CONFIRMED EMPTY')+'</div><p class="muted">This is an actual mining result.</p>'):'';
el.innerHTML='<div class="target-brief"><div class="target-orb">'+orb(p.id)+'</div><div><small>SELECTED TARGET</small><div class="target-name">'+e(p.id)+'</div><div class="target-type">'+(p.mined?'MINED · RESULT CONFIRMED':'UNKNOWN MINERAL STATUS')+'</div></div></div><div class="target-sensors"><div><small>HEAT</small><strong>'+p.heat+'</strong></div><div><small>SPECTRUM</small><strong>'+p.spectrum+'</strong></div></div>'+confirmed+(p.mined?'':!mission.trained?'<div class="intel-status">AI OFFLINE · TRAIN FIRST</div>':'');
}
function renderDecision(){
const el=$('decision'),p=cur();
if(!p||p.mined||!mission?.trained||mission.finished){el.hidden=true;return}
el.hidden=false;
const ready=inspection&&inspection.trained&&inspection.planet.id===p.id;
el.innerHTML='<h3>YOUR DECISION</h3><p class="muted">Compare the target Heat/Spectrum with the training examples above. You may agree or disagree with the AI.</p><div class="guess-buttons"><button id="guess-ore" class="outline '+(playerGuess==='ore'?'active':'')+'" '+(!ready?'disabled':'')+'>💎 I PREDICT ORE</button><button id="guess-empty" class="outline '+(playerGuess==='empty'?'active':'')+'" '+(!ready?'disabled':'')+'>◌ I PREDICT EMPTY</button></div><div class="decision-cost"><span>Mining costs <b>10 Credits</b></span><span>Correct personal guess: <b>+20 Research XP</b></span></div><button id="mine" class="primary wide" '+(!ready||!playerGuess?'disabled':'')+'>⛏ MINE & REVEAL</button>'+(!ready?'<p class="muted">Loading KNN evidence before you decide…</p>':'');
if($('guess-ore'))$('guess-ore').onclick=()=>{playerGuess='ore';renderDecision()};
if($('guess-empty'))$('guess-empty').onclick=()=>{playerGuess='empty';renderDecision()};
if($('mine'))$('mine').onclick=()=>minePlanet(p.id);
}
function voterChart(p,near){
const X=x=>20+x*20,Y=y=>195-y*17;
let svg='<svg viewBox="0 0 235 218" aria-label="KNN voters in sensor feature space">';
for(let i=0;i<=10;i+=2){svg+='<line x1="'+X(i)+'" y1="22" x2="'+X(i)+'" y2="195" stroke="#365274" opacity=".5"/><line x1="20" y1="'+Y(i)+'" x2="220" y2="'+Y(i)+'" stroke="#365274" opacity=".5"/>'}
mission.training.forEach(n=>svg+='<circle cx="'+X(n.heat)+'" cy="'+Y(n.spectrum)+'" r="4" opacity=".38" fill="'+(n.ore?'#55e7b7':'#ffb777')+'"/>');
near.forEach(n=>svg+='<line x1="'+X(p.heat)+'" y1="'+Y(p.spectrum)+'" x2="'+X(n.heat)+'" y2="'+Y(n.spectrum)+'" stroke="'+(n.ore?'#55e7b7':'#ffb777')+'" stroke-width="2" stroke-dasharray="3 3"/><circle cx="'+X(n.heat)+'" cy="'+Y(n.spectrum)+'" r="7" fill="'+(n.ore?'#55e7b7':'#ffb777')+'"/><text x="'+(X(n.heat)+8)+'" y="'+(Y(n.spectrum)-7)+'" fill="#fff" font-size="8">'+e(n.id)+'</text>');
return svg+'<circle cx="'+X(p.heat)+'" cy="'+Y(p.spectrum)+'" r="9" fill="#59cefc" stroke="white" stroke-width="2"/></svg>';
}
function renderVoterEvidence(){
const el=$('voter-evidence'),p=cur();
if(!mission?.trained||!p||p.mined){el.hidden=true;return}
el.hidden=false;
if(!inspection||inspection.planet.id!==p.id){el.innerHTML='<h3>KNN EVIDENCE</h3><p class="muted">Loading the nearest training planets and their Heat/Spectrum readings…</p>';return}
const near=inspection.neighbors;
const row=n=>'<div class="evidence-row '+(n.ore?'has-ore':'no-ore')+'"><b>'+e(n.id)+(n.provisional?'<small class="draft-tag">DRAFT</small>':'')+'</b><span>'+n.heat+'</span><span>'+n.spectrum+'</span><span>'+n.distance+'</span><strong>'+(n.ore?'ORE':'EMPTY')+'</strong></div>';
const oreVotes=inspection.ore_votes,emptyVotes=inspection.k-oreVotes;
const scout=inspection.scout_options||[];
el.innerHTML='<div class="evidence-title"><div><h3>KNN EVIDENCE · K='+inspection.k+'</h3><p class="muted">'+e(inspection.focus.toUpperCase())+' sensor focus · Closest known training planets</p></div><button id="replay-evidence" class="evidence-replay" title="Replay each KNN vote" aria-label="Replay KNN votes">↻</button></div>'+
'<div class="evidence-columns"><span>PLANET</span><span>HEAT</span><span>SPEC.</span><span>DIST.</span><span>LABEL</span></div>'+
'<div class="evidence-rows">'+near.map(row).join('')+'</div>'+
'<div class="evidence-tally"><strong>AI PREDICTS '+(inspection.predicted?'ORE':'EMPTY')+'</strong><span>'+oreVotes+' ORE / '+emptyVotes+' EMPTY</span></div>'+
'<p class="muted">Each training planet votes its stored label. <b>DRAFT</b> means you assigned an unverified label; a scan can correct it. Votes are not probabilities.</p>'+
'<details class="evidence-expand"><summary>View sensor-space connections and distance math</summary><div class="voter-plot">'+voterChart(p,near)+'</div><p class="muted">These lines connect similar sensor readings, not physical distances between planets. The selected sensor focus changes the weighted distance.</p></details>'+
(scout.length?'<details class="evidence-expand scout-expand"><summary>Collect stronger evidence (optional)</summary><p class="muted">Scan the training report with sensor readings nearest to this target. Cost: 5 Credits. This does not reveal the target\'s hidden ore label.</p><button id="scout-suggest" class="outline wide">PREPARE SCAN · '+e(scout[0].id)+'</button></details>':'');
$('replay-evidence').onclick=()=>showVoteAnimation(inspection);
if($('scout-suggest'))$('scout-suggest').onclick=()=>{$('scan-target').value=scout[0].id;toast('Scan target '+scout[0].id+' selected. Use the Scan panel on the left to confirm.')};
}
async function inspectSelected(id){
if(!mission?.trained)return;
const seq=++inspectSeq,session=mission.session_id;
try{const d=await api('/api/missions/'+session+'/inspect/'+id);if(seq!==inspectSeq||selected!==id||mission?.session_id!==session)return;inspection=d;renderVoterEvidence();renderDecision();if(d.trained&&!d.mined&&tutorialStep===3)showVoteAnimation(d)}catch(err){if(seq===inspectSeq)toast(err.message)}
}
function choose(id){selected=id;inspection=null;playerGuess=null;renderMap();renderDetails();renderVoterEvidence();renderDecision();inspectSelected(id);if(tutorialStep===2)advanceTutorial(3)}
function setMission(m){mission=m;k=m.k;focus=m.focus;inspection=null;playerGuess=null;inspectSeq++;if(!m.candidates.some(p=>p.id===selected&&!p.mined))selected=null;render();if(selected&&m.trained)inspectSelected(selected)}

function reveal(event){
if(!event)return;const p=event.planet,scan=event.kind==='scan',good=p.ore;
$('reveal-type').textContent=scan?'TRAINING SCAN DISCOVERY':'MINING RESULT';
$('reveal-orb').innerHTML=orb(p.id);
$('reveal-title').textContent=(scan?'SCAN COMPLETE · ':good?'ORE DISCOVERED · ':'EMPTY WORLD · ')+p.id;
$('reveal-message').textContent=scan?'New permanent training example: '+(good?'ORE':'EMPTY')+'. Train the AI again to use it.':'AI predicted '+(event.entry.predicted?'ORE':'EMPTY')+'. Your guess: '+(event.entry.player_guess||'none')+'. Actual: '+(good?'ORE':'EMPTY')+'. '+(event.entry.guess_correct?'Correct personal guess: +20 Research XP!':'Study the voters and try again.');
$('reveal-credits').textContent=scan?'−5 CREDITS / +1 SAMPLE':(event.entry.delta>0?'+':'')+event.entry.delta+' CREDITS';
show('reveal');
}
function end(){if(!mission)return;$('medal').textContent=mission.medal+' EXPEDITION';$('recap').textContent='Final credits: '+mission.credits+'. Ore discovered: '+mission.history.filter(x=>x.ore).length+' out of '+mission.history.length+' mines. Compare your results with another K.';show('ending')}
async function create(seed=12){await act(async()=>{sessionSeed=seed;selected=null;setMission(await api('/api/missions','POST',{seed}));hide('intro');hide('ending');hide('reveal');toast('EXPEDITION LAUNCHED · TRAIN AI WITH K=3');startTutorial()})}
async function train(){if(!mission)return;await act(async()=>{const d=await api('/api/missions/'+mission.session_id+'/train','POST',{k,focus});setMission(d);trainingSeen=true;if(tutorialStep===1)advanceTutorial(2);toast('K='+d.k+' · TEST ACCURACY '+pct(d.evaluation.accuracy))})}
async function scan(){if(!mission)return;const id=$('scan-target').value;if(!id)return;await act(async()=>{const d=await api('/api/missions/'+mission.session_id+'/scan','POST',{planet_id:id});setMission(d);reveal(d.event);if(tutorialStep===4)advanceTutorial(5)})}
async function minePlanet(id){if(!mission)return;await act(async()=>{const d=await api('/api/missions/'+mission.session_id+'/mine','POST',{planet_id:id,player_guess:playerGuess});setMission(d);reveal(d.event);if(tutorialStep===5)advanceTutorial(6)})}
async function math(){const p=cur();if(!mission?.trained||!p){toast('Train and select a planet first');return}await act(async()=>{const d=await api('/api/missions/'+mission.session_id+'/inspect/'+p.id);if(d.mined){toast('Select an unmined planet');return}
const X=x=>42+x*47,Y=y=>280-y*24;let svg='<svg viewBox="0 0 555 315">';
for(let i=0;i<=5;i++){let n=i*2;svg+='<line x1="'+X(n)+'" y1="30" x2="'+X(n)+'" y2="280" stroke="#314b73"/><line x1="42" y1="'+Y(n)+'" x2="512" y2="'+Y(n)+'" stroke="#314b73"/>'}
d.neighbors.forEach(n=>svg+='<line x1="'+X(p.heat)+'" y1="'+Y(p.spectrum)+'" x2="'+X(n.heat)+'" y2="'+Y(n.spectrum)+'" stroke="#b9c9f2" stroke-width="2" stroke-dasharray="5 5"/>');
mission.training.forEach(n=>svg+='<circle cx="'+X(n.heat)+'" cy="'+Y(n.spectrum)+'" r="6" fill="'+(n.ore?'#52edb8':'#ffc086')+'"/>');
svg+='<circle cx="'+X(p.heat)+'" cy="'+Y(p.spectrum)+'" r="11" fill="#fff" stroke="#28c9f2" stroke-width="3"/><text x="270" y="307" fill="#abc8e9" text-anchor="middle" font-size="12">HEAT</text><text x="15" y="165" fill="#abc8e9" transform="rotate(-90 15 165)" font-size="12">SPECTRUM</text></svg>';
$('mathplot').innerHTML=svg;$('neighbors').innerHTML=d.neighbors.map(n=>'<span class="neighbor">'+e(n.id)+' · '+(n.ore?'ORE':'EMPTY')+' · distance '+n.distance+'</span>').join('');show('learn')})}

function renderChallenges(){
if(!mission)return;
const challenges=mission.challenges||[];
const done=challenges.filter(c=>c.completed).length;
$('challenge-count').textContent=done+' / '+challenges.length+' completed';
$('challenges').innerHTML=challenges.map(c=>'<div class="challenge '+(c.completed?'completed':'')+'"><div class="challenge-symbol">'+(c.completed?'✓':'◇')+'</div><div class="challenge-info"><b>'+e(c.name)+'</b><small>'+e(c.objective)+'</small><span>'+e(c.hint)+'</span></div></div>').join('');
}
function renderDebrief(){
const panel=$('debrief'),d=mission?.debrief;
if(!d){panel.hidden=true;return}
panel.hidden=false;
const hint=d.prediction_correct?'CORRECT AI PREDICTION':'AI PREDICTION ERROR — INVESTIGATE';
panel.innerHTML='<div class="debrief-title">'+(d.prediction_correct?'✓':'!')+' '+e(hint)+' · '+e(d.planet_id)+'</div><p>'+e(d.analysis)+'</p><b>TRY NEXT:</b><ol>'+d.next_steps.map(x=>'<li>'+e(x)+'</li>').join('')+'</ol><div class="debrief-neighbors">Previous voters: '+e(d.voter_ids.join(', ')||'none')+'</div>';
}
const tutorialScript=[
["Welcome, cadet","Your mission: understand the real evidence before taking risks. Start by reading a training report; scan, train, inspect, predict and improve."],
["Train your first model","Choose K=3, then press TRAIN AI. The AI uses known labels and the two synthetic sensor readings."],
["Choose a target","Click a candidate planet in the star map. The right side will show its data and actual K nearest surveyed voters."],
["Reveal the voters","Use the interactive vote reveal: each surveyed planet votes its confirmed ORE or EMPTY label."],
["Gather evidence","Optional but recommended: annotate an unverified report and verify it with a paid scan. You can also continue after observing the voters."],
["Make your prediction","After annotating or scanning, TRAIN AI again. Then select I SAY ORE or I SAY EMPTY and mine to reveal the truth."],
["Compare and improve","Save Model A, change K, sensor focus or annotated training data, and train Model B. Review the changed predictions."],
["Cadet graduation","You've explored the entire learning loop. Continue mining or replay the same galaxy to test a new idea."]
];
function startTutorial(){if(!mission){toast('Launch expedition before starting tutorial');return}tutorialStep=1;renderTutorial()}
function closeTutorial(){tutorialStep=-1;renderTutorial()}
function advanceTutorial(step){if(tutorialStep<0)return;tutorialStep=Math.max(tutorialStep,step);renderTutorial()}
function skipTutorialStep(){if(tutorialStep>=0&&tutorialStep<7)advanceTutorial(tutorialStep+1)}
function renderTutorial(){
const panel=$('tutorial-panel');document.querySelectorAll('.tutorial-highlight').forEach(el=>el.classList.remove('tutorial-highlight'));
if(tutorialStep<0||!mission){panel.hidden=true;return}
panel.hidden=false;
const i=Math.min(tutorialStep,tutorialScript.length-1);
$('tutorial-title').textContent=(i+1)+' / '+tutorialScript.length+' · '+tutorialScript[i][0];
$('tutorial-description').textContent=tutorialScript[i][1];
$('tutorial-progress').textContent='●'.repeat(i+1)+' ○'.repeat(tutorialScript.length-i-1);
const targets={1:'train',2:'map',3:'voter-evidence',4:'label-target',5:'decision',6:'save-model'};
const highlight=$(targets[i]);if(highlight&&!highlight.hidden)highlight.classList.add('tutorial-highlight');
}
function renderLab(){
if(!mission)return;
const choices=mission.reserve||[];
$('label-target').innerHTML=choices.map(p=>'<option value="'+e(p.id)+'">'+e(p.id)+' · H '+p.heat+' · S '+p.spectrum+(p.provisional_label?' · draft '+e(p.provisional_label):'')+'</option>').join('')||'<option value="">No unverified reports</option>';
$('label-ore').disabled=$('label-empty').disabled=!choices.length||mission.finished;
$('save-model').disabled=!mission.trained||mission.finished;
$('label-status').textContent=choices.length?'Provisional labels join training data, but may be wrong. Use a scan to verify your hypothesis.':'Every optional training report has been verified.';
$('label-audit').innerHTML=mission.label_audit.length?mission.label_audit.map(row=>'<div class="audit-row">'+e(row.planet_id)+' · you labeled '+e(row.player_label)+' · verified '+e(row.verified_label)+' · '+(row.correct?'✓ Correct (+10 XP)':'✕ Incorrect; label corrected')+'</div>').join(''):'No verified manual labels yet.';
const comparison=mission.model_comparison;
if(comparison){
let changes=comparison.changed.map(row=>'<div class="model-change">'+e(row.id)+' <b>'+(row.before?'ORE':'EMPTY')+' → '+(row.after?'ORE':'EMPTY')+'</b></div>').join('');
$('comparison').innerHTML='<div class="model-comparison"><div><b>MODEL A</b><p>K='+comparison.before.k+' · '+e(comparison.before.focus)+'</p><strong>'+pct(comparison.before.validation_accuracy)+'</strong><small>'+comparison.before.training_count+' training examples</small></div><div><b>MODEL B</b><p>K='+comparison.after.k+' · '+e(comparison.after.focus)+'</p><strong>'+pct(comparison.after.validation_accuracy)+'</strong><small>'+comparison.after.training_count+' training examples</small></div></div><p><b>'+comparison.changed_count+' / 12</b> mining predictions changed. Accuracy delta '+(comparison.accuracy_delta>=0?'+':'')+pct(comparison.accuracy_delta)+'.</p>'+(changes||'<p>No predictions changed. Try another K, feature focus or a label.</p>');
if(tutorialStep===6)advanceTutorial(7);
}else if(mission.saved_model){
$('comparison').textContent='Model A saved: K='+mission.saved_model.k+', '+mission.saved_model.focus+' focus, accuracy '+pct(mission.saved_model.validation_accuracy)+'. Change an input and retrain to see Model B.';
}else $('comparison').textContent='First train your AI and SAVE CURRENT AS MODEL A. Change K, sensor weight or manual labels, then retrain to see real prediction changes.';
}
async function labelReport(label){
if(!mission)return;
const id=$('label-target').value;
if(!id)return;
await act(async()=>{
const d=await api('/api/missions/'+mission.session_id+'/label','POST',{planet_id:id,label});
setMission(d);toast('PROVISIONAL LABEL SAVED: '+id+' = '+label.toUpperCase()+'. Train or verify with SCAN.');
if(tutorialStep===4)advanceTutorial(5);
});
}
async function saveModel(){
if(!mission)return;
await act(async()=>{setMission(await api('/api/missions/'+mission.session_id+'/save-model','POST'));toast('MODEL A SAVED — change a setting and retrain')});
}
function showVoteAnimation(data){
voterData=data;voterStep=-1;
$('vote-title').textContent=data.planet.id+' · '+data.k+' NEAREST VOTERS';
$('vote-steps').innerHTML='';
$('vote-result').textContent='Each known planet votes according to its currently labeled training record. A provisional label may be wrong until verified.';
$('vote-next').textContent='REVEAL FIRST VOTER →';
show('voting');
}
function nextVoter(){
if(!voterData)return;
voterStep++;
const list=voterData.neighbors;
if(voterStep<list.length){
const n=list[voterStep],line=document.createElement('div');
line.className='vote-entry '+(n.ore?'yes':'no');
line.textContent=(voterStep+1)+'. '+n.id+' · Distance '+n.distance+' · votes '+(n.ore?'ORE':'EMPTY')+' ('+(n.provisional?'provisional':'verified')+')';
$('vote-steps').appendChild(line);
$('vote-next').textContent=voterStep+1===list.length?'SHOW FINAL VOTE →':'NEXT VOTER →';
}else{
$('vote-result').textContent=voterData.ore_votes+' ORE / '+(voterData.k-voterData.ore_votes)+' EMPTY — KNN predicts '+(voterData.predicted?'ORE':'EMPTY')+'. This is a majority label, NOT a probability or confirmed ore result.';
$('vote-next').textContent='CLOSE AND CONTINUE';
if(tutorialStep===3)advanceTutorial(4);
if(voterStep>list.length)hide('voting');
}
}

$('launch').onclick=()=>{if(mission){hide('intro');return}create(12)};$('train').onclick=train;$('scan').onclick=scan;
$('koptions').onclick=ev=>{const b=ev.target.closest('[data-k]');if(!b)return;k=Number(b.dataset.k);render();if(mission?.trained&&k!==mission.k)toast('K CHANGED · CLICK TRAIN TO UPDATE PREDICTIONS')};
$('focus-options').onclick=ev=>{const b=ev.target.closest('[data-focus]');if(!b)return;focus=b.dataset.focus;render();if(mission?.trained&&focus!==mission.focus)toast('SENSOR FOCUS CHANGED · TRAIN TO APPLY')};$('tutorial-start').onclick=startTutorial;$('tutorial-close').onclick=closeTutorial;$('tutorial-skip').onclick=closeTutorial;$('tutorial-next').onclick=skipTutorialStep;$('save-model').onclick=saveModel;$('label-ore').onclick=()=>labelReport('ore');$('label-empty').onclick=()=>labelReport('empty');$('vote-next').onclick=nextVoter;$('vote-close').onclick=()=>{hide('voting');if(tutorialStep===3)advanceTutorial(4)};
$('builder').onclick=math;$('close-learn').onclick=()=>hide('learn');
$('help').onclick=()=>{$('launch').textContent='RETURN TO GAME';show('intro')};
$('restart').onclick=()=>create(sessionSeed);$('retry').onclick=()=>create(sessionSeed);$('next').onclick=()=>create(sessionSeed+1);
$('continue').onclick=()=>{hide('reveal');if(mission?.finished)end()};
$('learn').onclick=ev=>{if(ev.target===$('learn'))hide('learn')};
document.addEventListener('keydown',ev=>{if(ev.key==='Escape')hide('learn')});
})();