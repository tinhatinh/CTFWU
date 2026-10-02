(() => {
  'use strict';
  const launch = document.querySelector('#local-edit');
  if (!launch || !['127.0.0.1', 'localhost'].includes(location.hostname)) return;
  const vi = document.body.dataset.language === 'vi';
  const text = vi ? {
    loading:'Đang đọc file gốc…', saving:'Đã lưu. Đang rebuild trang…', unchanged:'Nội dung chưa thay đổi.',
    failed:'Không thể hoàn tất thao tác.', timeout:'File đã lưu; trang vẫn đang rebuild. Tải lại trang sau.',
    discard:'Bỏ các thay đổi chưa lưu?', conflict:'File đã thay đổi hoặc đang rebuild. Giữ lại nội dung sửa, rồi nạp lại file để đối chiếu.',
    buildError:'Đã lưu nhưng rebuild thất bại. Xem _build/editor-build.log.', owner:'Phiên xác minh đã hết hạn. Đăng nhập lại.',
    verifying:'Đang xác minh tài khoản với GitHub…', denied:'Chỉ chủ repo được phép sửa. Kiểm tra tài khoản và token.'
  } : {
    loading:'Reading the original files…', saving:'Saved. Rebuilding the site…', unchanged:'No changes to save.',
    failed:'Could not complete this action.', timeout:'Source saved; the rebuild is still running. Reload later.',
    discard:'Discard unsaved changes?', conflict:'The source changed or a rebuild is running. Keep your edits, then reload to compare.',
    buildError:'Saved, but rebuild failed. See _build/editor-build.log.', owner:'Your verification session expired. Sign in again.',
    verifying:'Verifying the account with GitHub…', denied:'Only the repository owner may edit. Check the account and token.'
  };
  const dialog = document.querySelector('#writeup-editor');
  const status = document.querySelector('#editor-status');
  const form = document.querySelector('#editor-form');
  const login = document.querySelector('#editor-login');
  const select = document.querySelector('#editor-language');
  const contents = {vi:document.querySelector('#editor-content-vi'),en:document.querySelector('#editor-content-en')};
  const key = document.querySelector('[data-writeup-key]').dataset.writeupKey;
  let token, variants = {}, busy = false;
  const selected = () => select.value === 'both' ? ['vi','en'] : [select.value];
  const dirty = () => Object.entries(variants).some(([lang,data]) => contents[lang].value !== data.original);
  const setBusy = value => {
    busy = value;
    dialog.querySelectorAll('button,textarea,input,select').forEach(element => {element.disabled=value;});
    dialog.setAttribute('aria-busy',String(value));
  };
  const request = async (url, options) => {
    const response = await fetch(url,{cache:'no-store',credentials:'same-origin',...options});
    const data = await response.json();
    if (!response.ok) {
      const message = response.status === 409 ? text.conflict : response.status === 401 ? (url==='/api/login'?text.denied:text.owner) : response.status === 403 ? text.denied : (data.error || text.failed);
      throw new Error(message);
    }
    return data;
  };
  const showPanes = () => {
    dialog.querySelectorAll('.editor-pane').forEach(pane => {pane.hidden=!selected().includes(pane.dataset.language);});
    dialog.classList.toggle('editing-both',select.value==='both');
    for (const option of select.options) option.disabled = option.value === 'both' ? !variants.vi || !variants.en : !variants[option.value];
    document.querySelector('#editor-save').disabled = !selected().every(lang=>variants[lang]);
  };
  const showLogin = () => {
    login.hidden=false; form.hidden=true; token=undefined; variants={};
    Object.values(contents).forEach(element=>{element.value='';});
  };
  const read = async () => {
    status.textContent=text.loading;setBusy(true);
    try {
      const data = await request('/api/writeup?'+new URLSearchParams({key}));
      variants=data.variants;
      for (const lang of ['vi','en']) {
        if (!variants[lang]) {contents[lang].value='';continue;}
        variants[lang].original=variants[lang].content.replace(/\r\n/g,'\n');
        contents[lang].value=variants[lang].original;
        document.querySelector('#editor-path-'+lang).textContent=(lang==='vi'?'VN':'EN')+' · '+variants[lang].path;
      }
      if (!selected().every(lang=>variants[lang])) select.value=variants.vi?'vi':'en';
      status.textContent='';login.hidden=true;form.hidden=false;
    } catch(error) {status.textContent=error.message;}
    finally {setBusy(false);showPanes();}
  };
  launch.addEventListener('click',async()=>{
    dialog.showModal();status.textContent='';setBusy(true);
    try {
      const session=await request('/api/editor');
      if (session.authenticated) {token=session.token;await read();}
      else showLogin();
    } catch(error) {status.textContent=error.message;showLogin();}
    finally {setBusy(false);showPanes();}
  });
  login.addEventListener('submit',async event=>{
    event.preventDefault();if(busy)return;
    setBusy(true);status.textContent=text.verifying;
    const input=document.querySelector('#github-token');
    try {
      const session=await request('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:input.value})});
      input.value='';token=session.token;await read();
    } catch(error) {input.value='';status.textContent=error.message;}
    finally {setBusy(false);showPanes();}
  });
  select.value=document.body.dataset.language;
  select.addEventListener('change',showPanes);
  const mayClose=()=>!busy&&(!dirty()||window.confirm(text.discard));
  document.querySelector('#editor-close').addEventListener('click',()=>{if(mayClose())dialog.close();});
  dialog.addEventListener('cancel',event=>{if(!mayClose())event.preventDefault();});
  document.querySelector('#editor-reload').addEventListener('click',()=>{if(!dirty()||window.confirm(text.discard))read();});
  document.querySelector('#editor-logout').addEventListener('click',async()=>{
    if(!mayClose())return;
    setBusy(true);
    try {await request('/api/logout',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':token},body:'{}'});showLogin();status.textContent='';}
    catch(error){status.textContent=error.message;}
    finally{setBusy(false);}
  });
  window.addEventListener('beforeunload',event=>{if(dialog.open&&dirty()){event.preventDefault();event.returnValue='';}});
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(busy||!token||!selected().every(lang=>variants[lang]))return;
    const edits=selected().map(lang=>({lang,content:contents[lang].value,version:variants[lang].version}));
    setBusy(true);status.textContent=text.loading;
    try {
      const data=await request('/api/writeup',{method:'POST',headers:{'Content-Type':'application/json','X-Editor-Token':token},body:JSON.stringify({key,edits})});
      for(const edit of edits)variants[edit.lang].original=edit.content;
      if(!data.saved){status.textContent=text.unchanged;return;}
      status.textContent=text.saving;
      for(let attempt=0;attempt<180;attempt++){
        await new Promise(resolve=>setTimeout(resolve,1000));const build=await request('/api/build');
        if(build.state==='done'){
          if(dirty()){
            const latest=await request('/api/writeup?'+new URLSearchParams({key}));
            for(const edit of edits)variants[edit.lang].version=latest.variants[edit.lang].version;
            status.textContent=vi?'Đã lưu bản đã chọn. Bản còn lại vẫn có thay đổi chưa lưu.':'Selected edition saved. The other edition still has unsaved changes.';
            return;
          }
          dialog.close();location.reload();return;
        }
        if(build.state==='error')throw new Error(text.buildError);
      }
      status.textContent=text.timeout;
    }catch(error){status.textContent=error.message;}
    finally{setBusy(false);showPanes();}
  });
  request('/api/editor').then(data=>{if(data.enabled)launch.hidden=false;}).catch(()=>{});
})();
