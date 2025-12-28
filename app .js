async function getExpr(){
  const res = await fetch('/expr');
  if(!res.ok) return;
  const j = await res.json();
  document.getElementById('expr').textContent = j.expr;
  document.getElementById('score').textContent = j.score;
  document.getElementById('rounds').textContent = j.rounds;
  clearFeedback();
  document.getElementById('answer').value = '';
  document.getElementById('answer').focus();
}

function showFeedback(text, ok){
  const f = document.getElementById('feedback');
  f.textContent = text;
  f.className = 'feedback ' + (ok ? 'ok' : 'bad');
}

function clearFeedback(){
  const f = document.getElementById('feedback');
  f.textContent = '';
  f.className = 'feedback';
}

document.getElementById('submit').addEventListener('click', async ()=>{
  const answer = document.getElementById('answer').value.trim();
  if(answer === '') { showFeedback('Please type an answer or press Skip.', false); return; }
  const res = await fetch('/check', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({answer})
  });
  const j = await res.json();
  if(j.error){ showFeedback(j.error, false); return; }
  showFeedback(j.feedback, j.correct);
  document.getElementById('score').textContent = j.score;
  document.getElementById('rounds').textContent = j.rounds;
  // after short delay load next
  setTimeout(getExpr, 900);
});

document.getElementById('skip').addEventListener('click', getExpr);
document.getElementById('reset').addEventListener('click', async ()=>{
  await fetch('/reset', {method:'POST'});
  document.getElementById('score').textContent = '0';
  document.getElementById('rounds').textContent = '0';
  getExpr();
});

document.addEventListener('keydown', (e) => {
  if(e.key === 'Enter') document.getElementById('submit').click();
});

// init
getExpr();
