const API_BASE = 'http://localhost:8000';
const S = {filepath:null,filename:null,isLearning:false,isCompleted:false,totalSlides:0,currentSlide:0,progress:0,isProcessing:false};
const $ = id => document.getElementById(id);
const uploadArea=$('uploadArea'),fileInput=$('fileInput'),fileInfo=$('fileInfo'),fileName=$('fileName'),fileStatus=$('fileStatus'),removeFile=$('removeFile'),controls=$('controls'),progressFill=$('progressFill'),progressText=$('progressText'),prevBtn=$('prevBtn'),nextBtn=$('nextBtn'),quickActions=$('quickActions'),notesBtn=$('notesBtn'),quizBtn=$('quizBtn'),exportBtn=$('exportBtn'),messages=$('messages'),welcomeMessage=$('welcomeMessage'),typingIndicator=$('typingIndicator'),chatInput=$('chatInput'),sendBtn=$('sendBtn'),inputHint=$('inputHint'),headerStatus=$('headerStatus'),clearBtn=$('clearBtn'),menuBtn=$('menuBtn'),sidebar=$('sidebar');

function esc(t){return t.replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>')}
function md(t){
  if(!t)return'';
  let h=esc(t)
    .replace(/```(\w*)\n?([\s\S]*?)```/g,'<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/^### (.+)$/gm,'<h3>$1</h3>')
    .replace(/^## (.+)$/gm,'<h2>$1</h2>')
    .replace(/^# (.+)$/gm,'<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/^> (.+)$/gm,'<blockquote>$1</blockquote>')
    .replace(/^- (.+)$/gm,'<li>$1</li>')
    .replace(/^\d+\. (.+)$/gm,'<li>$1</li>')
    .replace(/^---$/gm,'<hr>')
    .replace(/\n\n/g,'</p><p>')
    .replace(/\n/g,'<br>');
  return'<p>'+h+'</p>';
}

function addBot(c,t){
  welcomeMessage.style.display='none';
  const d=document.createElement('div');d.className='message bot';
  let th=t?'<div style="font-weight:600;margin-bottom:8px;background:var(--gradient-1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:15px;">'+esc(t)+'</div>':'';
  d.innerHTML='<div class="msg-avatar"><img src="/static/images/2.png" alt="" class="msg-avatar-img"></div><div class="msg-bubble">'+th+md(c)+'</div>';
  messages.insertBefore(d,typingIndicator);scroll();return d;
}
function addUser(c){
  welcomeMessage.style.display='none';
  const d=document.createElement('div');d.className='message user';
  d.innerHTML='<div class="msg-avatar">👤</div><div class="msg-bubble">'+esc(c)+'</div>';
  messages.insertBefore(d,typingIndicator);scroll();return d;
}
function scroll(){setTimeout(()=>messages.scrollTop=messages.scrollHeight,50)}
function showTyping(){typingIndicator.classList.add('active');scroll()}
function hideTyping(){typingIndicator.classList.remove('active')}

function updProg(slide,total){
  S.currentSlide=slide;S.totalSlides=total;
  const p=total>0?Math.round(slide/total*100):0;
  S.progress=p;progressFill.style.width=p+'%';progressText.textContent=p+'%';
  prevBtn.disabled=slide<=1;
}
function setInp(e){chatInput.disabled=!e;sendBtn.disabled=!e;inputHint.textContent=e?'输入你的问题...':'上传课件后即可开始对话'}

async function apiPost(ep,data){
  const fd=new FormData();for(const[k,v]of Object.entries(data))fd.append(k,v);
  const r=await fetch(API_BASE+ep,{method:'POST',body:fd});
  if(!r.ok){const e=await r.json();throw new Error(e.detail||'请求失败')}
  return r.json();
}
async function uploadFile(file){
  const fd=new FormData();fd.append('file',file);
  const r=await fetch(API_BASE+'/upload',{method:'POST',body:fd});
  if(!r.ok){const e=await r.json();throw new Error(e.detail||'上传失败')}
  return r.json();
}

async function handleUpload(file){
  try{
    const r=await uploadFile(file);
    S.filepath=r.filepath;S.filename=r.filename;
    fileName.textContent=r.filename;fileStatus.textContent='✅ 已加载';fileStatus.className='file-status loaded';
    fileInfo.classList.add('active');uploadArea.style.display='none';
    await startLearning();
  }catch(e){addBot('❌ 上传失败: '+e.message);resetUpload()}
}
function resetUpload(){
  S.filepath=null;S.filename=null;uploadArea.style.display='block';
  fileInfo.classList.remove('active');controls.classList.remove('active');quickActions.classList.remove('active');
  setInp(false);headerStatus.innerHTML='上传课件开始上课 <span class="highlight">📤</span>';
}
async function startLearning(){
  try{
    showTyping();
    const r=await apiPost('/learn/start',{filepath:S.filepath,language:'zh'});
    hideTyping();S.isLearning=true;
    controls.classList.add('active');quickActions.classList.add('active');
    updProg(0,r.total_slides);
    headerStatus.innerHTML='📖 正在学习 <span class="highlight">'+S.filename+'</span>';
    setInp(true);addBot(r.content,r.title);await nextPage();
  }catch(e){hideTyping();addBot('❌ 开始学习失败: '+e.message)}
}
async function nextPage(){
  if(S.isProcessing)return;S.isProcessing=true;nextBtn.disabled=true;
  try{
    showTyping();const r=await apiPost('/learn/next',{filepath:S.filepath});hideTyping();
    if(r.step_type==='done'){
      S.isCompleted=true;nextBtn.disabled=true;nextBtn.textContent='✅ 已完成';
      updProg(S.totalSlides,S.totalSlides);
      headerStatus.innerHTML='🎉 学完了 <span class="highlight">'+S.filename+'</span>，可以做练习了！';
      addBot(r.content,r.title);
    }else{updProg(r.slide_number,r.total_slides);addBot(r.content,r.title)}
  }catch(e){hideTyping();addBot('❌ 加载失败: '+e.message)}
  finally{S.isProcessing=false;if(!S.isCompleted)nextBtn.disabled=false}
}
async function prevPage(){
  if(S.isProcessing)return;S.isProcessing=true;
  try{
    showTyping();const r=await apiPost('/learn/prev',{filepath:S.filepath});hideTyping();
    updProg(r.slide_number,r.total_slides);addBot(r.content,r.title);
    nextBtn.disabled=false;nextBtn.textContent='下一页 ▶';S.isCompleted=false;
  }catch(e){hideTyping();addBot('❌ '+e.message)}
  finally{S.isProcessing=false}
}
async function askQuestion(q){
  if(S.isProcessing||!q.trim())return;S.isProcessing=true;
  addUser(q);chatInput.value='';chatInput.style.height='auto';
  try{
    showTyping();const r=await apiPost('/learn/ask',{filepath:S.filepath,question:q});hideTyping();
    addBot(r.content,r.title);
  }catch(e){hideTyping();addBot('❌ 回答失败: '+e.message)}
  finally{S.isProcessing=false}
}
async function generateNotes(){
  if(S.isProcessing)return;S.isProcessing=true;
  try{
    showTyping();const r=await apiPost('/learn/notes',{filepath:S.filepath,detail:'detailed'});hideTyping();
    addBot(r.content,r.title);
  }catch(e){hideTyping();addBot('❌ 生成笔记失败: '+e.message)}
  finally{S.isProcessing=false}
}
async function generateQuiz(){
  if(S.isProcessing)return;S.isProcessing=true;
  try{
    showTyping();const r=await apiPost('/learn/quiz',{filepath:S.filepath,num_questions:'5'});hideTyping();
    addBot(r.content,r.title);
  }catch(e){hideTyping();addBot('❌ 生成练习题失败: '+e.message)}
  finally{S.isProcessing=false}
}
async function exportPdf(){
  if(S.isProcessing)return;S.isProcessing=true;
  try{
    showTyping();
    const nr=await apiPost('/learn/notes',{filepath:S.filepath,detail:'detailed'});
    const qr=await apiPost('/learn/quiz',{filepath:S.filepath,num_questions:'5'});
    const sj=nr.extra?nr.extra.summary_json:null;
    const qj=qr.extra?qr.extra.quiz_json:null;
    const fd=new FormData();fd.append('filepath',S.filepath);
    if(sj)fd.append('summary_json',JSON.stringify(sj));
    if(qj)fd.append('quiz_json',JSON.stringify(qj));
    const r=await fetch(API_BASE+'/export-pdf',{method:'POST',body:fd});
    if(!r.ok)throw new Error('导出失败');
    const result=await r.json();
    hideTyping();
    addBot('✅ PDF 报告已生成！\n\n📄 **文件**: '+result.filename+'\n\n文件保存在 `project/` 目录下。');
  }catch(e){hideTyping();addBot('❌ 导出 PDF 失败: '+e.message)}
  finally{S.isProcessing=false}
}
function clearChat(){
  const b=messages.querySelectorAll('.message');b.forEach(m=>m.remove());
  welcomeMessage.style.display='flex';
  headerStatus.innerHTML=S.filepath?'📖 已加载 <span class="highlight">'+S.filename+'</span>，继续学习':'上传课件开始上课 <span class="highlight">📤</span>';
}

// 事件绑定
uploadArea.addEventListener('click',()=>fileInput.click());
uploadArea.addEventListener('dragover',e=>{e.preventDefault();uploadArea.classList.add('dragover')});
uploadArea.addEventListener('dragleave',()=>uploadArea.classList.remove('dragover'));
uploadArea.addEventListener('drop',e=>{e.preventDefault();uploadArea.classList.remove('dragover');if(e.dataTransfer.files.length>0)handleUpload(e.dataTransfer.files[0])});
fileInput.addEventListener('change',()=>{if(fileInput.files.length>0)handleUpload(fileInput.files[0])});
removeFile.addEventListener('click',resetUpload);
nextBtn.addEventListener('click',nextPage);
prevBtn.addEventListener('click',prevPage);
notesBtn.addEventListener('click',generateNotes);
quizBtn.addEventListener('click',generateQuiz);
exportBtn.addEventListener('click',exportPdf);
clearBtn.addEventListener('click',clearChat);
menuBtn.addEventListener('click',()=>sidebar.classList.toggle('mobile-show'));
chatInput.addEventListener('input',()=>{chatInput.style.height='auto';chatInput.style.height=Math.min(chatInput.scrollHeight,120)+'px'});
chatInput.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();if(!sendBtn.disabled)askQuestion(chatInput.value)}});
sendBtn.addEventListener('click',()=>askQuestion(chatInput.value));

console.log('🎓 AI 教授已就绪！上传 PPT 开始上课吧！');
