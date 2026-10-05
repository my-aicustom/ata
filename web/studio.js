'use strict';
const $=id=>document.getElementById(id);
const roles=[['mulai_di_sini','Mulai di Sini','★'],['ledger','Ledger','▤'],['topic_framer','Topic Framer','◎'],['source_finder','Source Finder','🔍'],['research_brief','Research Brief','▧'],['matrix_synthesis','Matrix Synthesis','📊'],['method_fit','Method Fit','⌘'],['drafting_assistant','Drafting','✎'],['critic','Critic','◇'],['stats_reviewer','Stats Reviewer','▥'],['contribution_builder','Contribution','💡'],['style_editor','Style Editor','✨'],['abstract_writer','Abstract','📝'],['ai_disclosure','AI Disclosure','⚖️'],['mock_examiner','Mock Examiner','◉'],['defense_pack','Defense Pack','🛡️']];
let role='ledger',history=[],busy=false,files=[],attachments=[];
const phaseRoles = {
  1: ['mulai_di_sini', 'ledger', 'topic_framer'],
  2: ['source_finder', 'research_brief', 'matrix_synthesis'],
  3: ['method_fit', 'drafting_assistant', 'critic'],
  4: ['method_fit', 'drafting_assistant'],
  5: ['stats_reviewer', 'drafting_assistant', 'critic'],
  6: ['contribution_builder', 'style_editor', 'abstract_writer', 'ai_disclosure'],
  7: ['mock_examiner', 'defense_pack']
};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function markdown(text){
  const inline=line=>esc(line).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/`([^`]+)`/g,'<code>$1</code>');
  const cells=line=>line.trim().replace(/^\||\|$/g,'').split('|').map(c=>inline(c.trim()));
  return String(text).split(/(```[\s\S]*?```)/g).map(block=>{
    if(block.startsWith('```'))return '<pre><code>'+esc(block.replace(/^```[^\n]*\n?/, '').replace(/```$/, ''))+'</code></pre>';
    const lines=block.split('\n');let html='';
    for(let i=0;i<lines.length;i++){
      const line=lines[i];
      if(line.includes('|') && i+1<lines.length && /^\s*\|?\s*:?-{3,}/.test(lines[i+1])){
        html+='<div class="table-scroll"><table><thead><tr>'+cells(line).map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>';i++;
        while(i+1<lines.length && lines[i+1].includes('|')){i++;html+='<tr>'+cells(lines[i]).map(c=>'<td>'+c+'</td>').join('')+'</tr>';}
        html+='</tbody></table></div>';continue;
      }
      if(/^#{1,3} /.test(line)){html+='<h3>'+inline(line.replace(/^#{1,3} /,''))+'</h3>';continue;}
      if(/^[-*] /.test(line)){
        html+='<ul>';do{html+='<li>'+inline(lines[i].slice(2))+'</li>';i++;}while(i<lines.length && /^[-*] /.test(lines[i]));i--;html+='</ul>';continue;
      }
      html+=inline(line)+'<br>';
    }
    return html;
  }).join('');
}
function toast(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,4500);}
async function api(path,data){const response=await fetch(path,{method:data?'POST':'GET',headers:data?{'Content-Type':'application/json'}:{},body:data?JSON.stringify(data):undefined});const result=await response.json();if(!response.ok)throw Error(result.error||'Permintaan gagal');return result;}
function chooseRole(key){role=key;if($('roleSelect'))$('roleSelect').value=key;if($('roleTitle'))$('roleTitle').textContent=(roles.find(r=>r[0]===key)||[,'Ledger'])[1];document.querySelectorAll('[data-role]').forEach(b=>b.classList.toggle('active',b.dataset.role===key));}
function renderRoleOptions(allowedKeys=roles.map(([key])=>key)){if(!$('roleSelect'))return;const allowed=new Set(allowedKeys);$('roleSelect').innerHTML=roles.filter(([key])=>allowed.has(key)).map(([key,name])=>`<option value="${key}">${name}</option>`).join('');}
function setPhase(phaseNum){const phase=Number(phaseNum)||1;const allowedRoles=phaseRoles[phase]||phaseRoles[1];document.querySelectorAll('#thesisPipeline .step-btn').forEach(btn=>btn.classList.toggle('active',Number(btn.dataset.phase)===phase));renderRoleOptions(allowedRoles);if(!allowedRoles.includes(role))chooseRole(allowedRoles[0]);else chooseRole(role);}
if($('roles'))$('roles').innerHTML=roles.map(([key,name,glyph])=>`<button class="navitem" data-role="${key}"><span class="glyph">${glyph}</span>${name}</button>`).join('');
renderRoleOptions();
if($('roles'))$('roles').onclick=e=>{const b=e.target.closest('[data-role]');if(b)chooseRole(b.dataset.role);};if($('roleSelect'))$('roleSelect').onchange=e=>chooseRole(e.target.value);document.querySelectorAll('#thesisPipeline .step-btn').forEach(btn=>{btn.addEventListener('click',e=>{setPhase(btn.dataset.phase);if(e.target.closest('.step-gate'))tab('gates');});btn.addEventListener('dblclick',()=>tab('gates'));});setPhase(1);
function tab(name){document.querySelectorAll('.panel').forEach(p=>p.hidden=p.id!=='panel-'+name);document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===name)));if(innerWidth<=1150)$('app').classList.add('drawer-open');$('app').classList.remove('drawer-closed');}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>tab(b.dataset.tab));
$('collapse').onclick=()=>{if(innerWidth<=650)$('app').classList.toggle('mobile-nav');else $('app').classList.toggle('sidebar-closed');};
const toggleDrawer=()=>{if(innerWidth<=1150)$('app').classList.toggle('drawer-open');else $('app').classList.toggle('drawer-closed');};
if($('drawerToggle'))$('drawerToggle').onclick=toggleDrawer;
if($('drawerClose'))$('drawerClose').onclick=toggleDrawer;
window.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='j'){e.preventDefault();toggleDrawer();}});
$('newChat').onclick=()=>{if(busy)return toast('Respons asisten masih berjalan.');history=[];document.querySelectorAll('.message').forEach(m=>m.remove());$('welcome').hidden=false;$('prompt').value='';$('attachmentLabel').textContent='';attachments=[];renderAttachments();$('prompt').focus();};
function message(text,type,meta=''){ $('welcome').hidden=true;const node=document.createElement('article');node.className='message '+type;node.innerHTML=`<div class="avatar">${type==='user'?'M':'<img src="/assets/icon_transparent.png" class="avatar-logo-img" alt="ATA">'}</div><div class="message-content"><div class="message-head">${type==='user'?'Anda':esc($('roleTitle').textContent)}</div><div class="bubble">${markdown(text)}</div><div class="message-meta"><span>${esc(meta)}</span><button type="button">Salin</button></div></div>`;node.querySelector('button').onclick=async()=>{try{await navigator.clipboard.writeText(text);toast('Pesan disalin.');}catch{toast('Clipboard tidak tersedia.');}};$('thread').append(node);$('thread').scrollTop=$('thread').scrollHeight;return node;}
$('prompt').oninput=()=>{$('prompt').style.height='auto';$('prompt').style.height=Math.min($('prompt').scrollHeight,180)+'px';};
$('prompt').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();$('chatForm').requestSubmit();}};
document.querySelectorAll('[data-prompt]').forEach(b=>b.onclick=()=>{$('prompt').value=b.dataset.prompt;$('prompt').focus();$('prompt').oninput();});

function renderAttachments(){
  const container=$('attachmentPreviewContainer');
  if(!container)return;
  if(!attachments.length){container.hidden=true;container.innerHTML='';return;}
  container.hidden=false;
  container.innerHTML=attachments.map((att,idx)=>{
    let iconOrThumb='';
    if(att.type==='image'&&att.data_uri){
      iconOrThumb=`<img src="${att.data_uri}" class="attachment-chip-thumb" alt="preview">`;
    }else if(att.type==='audio'){
      iconOrThumb=`<span class="attachment-chip-icon">🎙️</span>`;
    }else{
      iconOrThumb=`<span class="attachment-chip-icon">📄</span>`;
    }
    return `<div class="attachment-chip ${att.type==='image'?'img-chip':''}">
      ${iconOrThumb}
      <span class="attachment-chip-text" title="${esc(att.filename)}">${esc(att.filename)}</span>
      <button type="button" class="attachment-chip-remove" data-idx="${idx}" title="Hapus lampiran">&times;</button>
    </div>`;
  }).join('');
  container.querySelectorAll('.attachment-chip-remove').forEach(btn=>{
    btn.onclick=()=>{attachments.splice(Number(btn.dataset.idx),1);renderAttachments();};
  });
}

$('attach').onclick=()=>$('attachment').click();
$('attachment').onchange=async e=>{
  const file=e.target.files[0];
  if(!file)return;
  if(file.size>15000000)return toast('Lampiran maksimal 15 MB.');
  const ext=file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
  const isPlain=ext==='.txt'||ext==='.md';
  if(isPlain){
    const text=await file.text();
    attachments.push({type:'text',filename:file.name,text,size:file.size});
    renderAttachments();
    toast(`File teks ditambahkan: ${file.name}`);
  }else{
    toast(`Memproses ${file.name}…`);
    try{
      const reader=new FileReader();
      reader.onload=async()=>{
        const b64=reader.result.split(',')[1];
        try{
          const res=await api('/api/parse/file',{filename:file.name,base64:b64});
          if(!res.success)throw Error(res.error||'Gagal membaca berkas');
          attachments.push({type:res.type,filename:res.filename,text:res.text,data_uri:res.data_uri,size:res.size});
          renderAttachments();
          toast(`Lampiran siap: ${file.name}`);
        }catch(err){toast(err.message);}
      };
      reader.readAsDataURL(file);
    }catch(err){toast('Gagal memuat berkas: '+err.message);}
  }
  e.target.value='';
};

$('chatForm').onsubmit=async e=>{
  e.preventDefault();
  let text=$('prompt').value.trim();
  if(!text&&!attachments.length)return;
  if(busy)return;
  if(attachments.length>0){
    const attTexts=attachments.map(a=>`\n\n---\n[LAMPIRAN: ${a.filename}]\n${a.text}\n---`).join('');
    text+=attTexts;
  }
  busy=true;
  $('send').disabled=true;
  $('newChat').disabled=true;
  message(text,'user');
  $('prompt').value='';
  $('prompt').oninput();
  $('attachmentLabel').textContent='';
  attachments=[];
  renderAttachments();
  $('modelStatus').textContent='Menghubungi OpenRouter…';
  const started=performance.now();
  try{
    const userKey=localStorage.getItem('ata_openrouter_key')||undefined;
    const result=await api('/api/agent/chat',{role,message:text,history,api_key:userKey});
    if(!result.success)throw Error(result.error||'Model belum tersedia.');
    const tokens=result.raw?.usage?.total_tokens;
    message(result.content,'assistant',`${result.model||'OpenRouter'} · ${((performance.now()-started)/1000).toFixed(1)}s · ${tokens??'—'} tokens`);
    history.push({role:'user',content:text},{role:'assistant',content:result.content});
    $('modelStatus').textContent=result.model||'OpenRouter · tersambung';
  }catch(error){
    message('Permintaan belum berhasil: '+error.message,'assistant','Koneksi gagal');
    $('prompt').value=text;
    $('modelStatus').textContent='OpenRouter · tidak tersedia';
  }finally{
    busy=false;
    $('send').disabled=false;
    $('newChat').disabled=false;
  }
};

async function loadGates(){const data=await api('/api/gates');$('gates').innerHTML=data.map(g=>`<article class="gate"><div class="gate-top"><strong>${esc(g.gate)} · ${esc(g.name)}</strong><span>${g.passed?'LOLOS':g.progress+'% · BELUM'}</span></div><progress value="${Number(g.progress)}" max="100" aria-label="${esc(g.gate)}"></progress><ul>${Object.entries(g.checks||{}).map(([k,v])=>`<li>${v?'✓':'○'} ${esc(k)}</li>`).join('')}</ul></article>`).join('');}
async function loadLedger(){const data=await api('/api/directives');$('directives').innerHTML=data.map(d=>`<article class="directive" data-id="${esc(d.id)}"><div class="directive-top"><span class="priority">${esc(d.priority)}</span><span>${esc(d.id)} · Bab ${esc(d.target_chapter)}</span></div><p>${esc(d.directive)}</p><details><summary>Kutipan arahan</summary><p>${esc(d.quote)}</p></details><input aria-label="Bukti ${esc(d.id)}" placeholder="Bukti locator: Bab / halaman / Brief" value="${esc(d.evidence_ref||'')}"><select aria-label="Status ${esc(d.id)}">${['open','addressed','clarify'].map(s=>`<option ${s===d.status?'selected':''}>${s}</option>`).join('')}</select><button>Simpan</button></article>`).join('');$('directives').querySelectorAll('article').forEach(a=>a.querySelector('button').onclick=async()=>{try{await api('/api/directives/update',{id:a.dataset.id,status:a.querySelector('select').value,evidence_ref:a.querySelector('input').value});await loadGates();toast('Status dan locator tersimpan.');}catch(e){toast(e.message);}});}
const knowledgeNames=[['00','00-Ledger'],['01','01-Profil'],['02','02-Matriks Konsistensi'],['03','03-Briefs'],['04','04-Matriks Literatur']];
async function loadKnowledge(){files=await api('/api/knowledge/files');$('fileCount').textContent=files.length;$('knowledge').innerHTML=knowledgeNames.map(([prefix,name])=>`<button class="navitem" data-prefix="${prefix}"><span class="glyph">≡</span>${name}${files.some(f=>f.name.startsWith(prefix))?'':' · —'}</button>`).join('');$('knowledge').onclick=async e=>{const b=e.target.closest('[data-prefix]');if(!b)return;const file=files.find(f=>f.name.startsWith(b.dataset.prefix));if(!file)return toast('Knowledge ini belum tersedia di disk.');try{const data=await api('/api/knowledge/file?name='+encodeURIComponent(file.name));$('knowledgeTitle').textContent=file.name;$('knowledgeContent').textContent=data.content;tab('knowledge');}catch(e){toast(e.message);}};}

async function loadInstances(){
  try{
    const list=await api('/api/instances');
    const active=await api('/api/instances/active');
    const select=$('instanceSelect');
    if(!select)return;
    select.innerHTML=list.map(inst=>`<option value="${esc(inst.id)}" ${inst.id===active.id?'selected':''}>${esc(inst.program||inst.name)} (${esc(inst.student)})</option>`).join('');
    const conf=active.config||{};
    const student=conf.mahasiswa||active.student||'Mahasiswa S2';
    const program=conf.jenjang_prodi||active.program||'Program Magister';
    const campus=conf.lembaga_kasus||'';
    const studyProgramBadge=$('study-program-badge');
    if(studyProgramBadge)studyProgramBadge.textContent=program.length>22?program.slice(0,20)+'…':program;
    const crumbRoot=document.querySelector('.crumb-root');
    if(crumbRoot)crumbRoot.textContent=program;
    const userInfoStrong=document.querySelector('.user-info strong');
    if(userInfoStrong)userInfoStrong.textContent=student;
    const userInfoP=document.querySelector('.user-info p');
    if(userInfoP)userInfoP.textContent=program+(campus?` · ${campus}`:'');
  }catch(err){console.error('Failed to load instances',err);}
}

if($('instanceSelect')){
  $('instanceSelect').onchange=async e=>{
    const newId=e.target.value;
    try{
      toast('Beralih ruang tesis…');
      const res=await api('/api/instances/switch',{id:newId});
      if(!res.success)throw Error('Gagal beralih instans');
      await loadInstances();
      await refresh();
      toast(`Aktif: ${res.active?.config?.jenjang_prodi||newId}`);
    }catch(err){toast(err.message);}
  };
}

const modal=$('newThesisModal');
if($('openNewThesisBtn')&&modal){
  $('openNewThesisBtn').onclick=()=>{
    modal.hidden=false;
    modal.setAttribute('aria-hidden','false');
    $('newStudentName')?.focus();
  };
}
const closeModal=()=>{if(modal){modal.hidden=true;modal.setAttribute('aria-hidden','true');}};
if($('closeNewThesisBtn'))$('closeNewThesisBtn').onclick=closeModal;
if($('cancelNewThesisBtn'))$('cancelNewThesisBtn').onclick=closeModal;

if($('newThesisForm')){
  $('newThesisForm').onsubmit=async e=>{
    e.preventDefault();
    const btn=$('submitNewThesisBtn');
    if(btn)btn.disabled=true;
    try{
      const data={
        student:$('newStudentName').value.trim(),
        campus:$('newCampus').value.trim(),
        program:$('newProgram').value.trim(),
        advisor:$('newAdvisor').value.trim(),
        topic:$('newTopic').value.trim(),
        domain:$('newDomain').value,
        method:$('newMethod').value
      };
      const res=await api('/api/instances/create',data);
      if(!res.success)throw Error(res.error||'Gagal membuat tesis');
      closeModal();
      $('newThesisForm').reset();
      await loadInstances();
      await refresh();
      toast(`✨ Workspace dibuat & aktif: ${data.program}`);
    }catch(err){toast(err.message);}finally{if(btn)btn.disabled=false;}
  };
}

async function refresh(){const results=await Promise.allSettled([loadLedger(),loadGates(),loadKnowledge(),loadInstances()]);results.filter(r=>r.status==='rejected').forEach(r=>toast(r.reason.message));} $('refresh').onclick=refresh;
function action(button,fn){$(button).onclick=async()=>{$(button).disabled=true;try{await fn();}catch(e){toast(e.message);}finally{$(button).disabled=false;}};}
action('scanClaims',async()=>{const data=await api('/api/audit/claims',{text:$('claimsText').value});$('claimsResult').innerHTML=`<p class="help">${data.compliance.total_sentences} kalimat · ${data.compliance.unsupported_claims} perlu sumber<br>M ${data.author_origin.student_ratio}% · M+AI ${data.author_origin.ai_expanded_ratio}% · AI ${data.author_origin.ai_suggested_ratio}%</p>`+data.sentences.map(s=>`<div class="claim"><span class="badge">${esc(s.origin)} · ${s.status==='supported'?'RUJUKAN TERCANTUM':'PERLU SUMBER'}</span><p>${esc(s.annotated_text)}</p></div>`).join('');});
action('scanSlop',async()=>{const data=await api('/api/audit/slop',{text:$('slopText').value});$('slopResult').textContent=data.clean?'Bersih dari 18 frasa terlarang.':data.found.map(p=>'⚠ '+p).join('\n');});
action('verifyDoi',async()=>{if(!$('doi').value.trim())throw Error('Masukkan DOI.');$('doiResult').textContent='Memeriksa Crossref / OpenAlex…';$('doiResult').textContent=JSON.stringify(await api('/api/verify/citation',{doi:$('doi').value.trim()}),null,2);});
action('verifyQuote',async()=>{if(!$('quote').value.trim()||!$('source').value.trim())throw Error('Isi kutipan dan teks sumber.');$('quoteResult').textContent=JSON.stringify(await api('/api/verify/quote',{quote:$('quote').value,source:$('source').value}),null,2);});
const examples={G1:{finer_scores:{Feasible:3,Interesting:3,Novel:3,Ethical:3,Relevant:3}},G4:{loading:[.7],ave:[.5],htmt:[.89],cr:[.7]},G5:{invalid_citations:0,unsupported_claims:0,open_red_critiques:0,similarity:10,similarity_threshold:20},G6:{question_scores:[3,3,3,3,null]}};
$('assessmentGate').onchange=()=>{$('assessment').placeholder=JSON.stringify(examples[$('assessmentGate').value],null,2);$('assessment').value='';};
action('saveAssessment',async()=>{const data=JSON.parse($('assessment').value);await api('/api/gates/assessment',{gate:$('assessmentGate').value,data});await loadGates();$('assessmentResult').textContent='Penilaian tersimpan. Hanya masukkan hasil nyata.';});
refresh();

async function loadModelStatus(){const data=await api('/api/model/status');const hasCustom = Boolean(localStorage.getItem('ata_openrouter_key'));
    $('modelStatus').textContent = (data.configured || hasCustom) ? ('OpenRouter · ' + (hasCustom ? 'Kunci Pribadi' : 'Free Tier · siap')) : 'OpenRouter · klik untuk set API key';}
loadModelStatus().catch(()=>{$('modelStatus').textContent='Status model tidak tersedia';});


// Modal Pengaturan API Key
const keyModal = $('apiKeyModal');
const openKeyModal = () => {
  if (keyModal) {
    keyModal.hidden = false;
    keyModal.setAttribute('aria-hidden', 'false');
    const input = $('customApiKeyInput');
    if (input) {
      input.value = localStorage.getItem('ata_openrouter_key') || '';
      input.focus();
    }
  }
};
if ($('active-model-badge')) $('active-model-badge').onclick = openKeyModal;
if ($('modelStatus')) {
  $('modelStatus').style.cursor = 'pointer';
  $('modelStatus').onclick = openKeyModal;
}
if ($('closeApiKeyBtn')) $('closeApiKeyBtn').onclick = () => { if (keyModal) { keyModal.hidden = true; keyModal.setAttribute('aria-hidden', 'true'); } };
if ($('clearApiKeyBtn')) $('clearApiKeyBtn').onclick = () => {
  localStorage.removeItem('ata_openrouter_key');
  if ($('customApiKeyInput')) $('customApiKeyInput').value = '';
  if (keyModal) { keyModal.hidden = true; keyModal.setAttribute('aria-hidden', 'true'); }
  toast('Kunci pribadi dihapus. Kembali ke kunci default server.');
  loadModelStatus();
};
if ($('apiKeyForm')) $('apiKeyForm').onsubmit = (e) => {
  e.preventDefault();
  const val = ($('customApiKeyInput')?.value || '').trim();
  if (val) {
    localStorage.setItem('ata_openrouter_key', val);
    toast('Kunci OpenRouter tersimpan di peramban!');
  } else {
    localStorage.removeItem('ata_openrouter_key');
    toast('Menggunakan kunci server bawaan.');
  }
  if (keyModal) { keyModal.hidden = true; keyModal.setAttribute('aria-hidden', 'true'); }
  loadModelStatus();
};
