/* GitHub Pages editor: credentials stay in tab memory; GitHub authorizes writes. */
(() => {
  'use strict';
  const repo = 'tinhatinh/CTFWU';
  const prefix = '/repos/' + repo;
  window.createGithubEditor = () => {
    const directory = document.querySelector('[data-source-directory]').dataset.sourceDirectory;
    const parts = directory.split('/');
    if (![2,3].includes(parts.length) || (parts.length===3 && !/^Wave [1-9]\d*$/.test(parts[1])) || parts.some(part=>!part || part==='.' || part==='..' || /[\\\u0000-\u001f]/.test(part))) throw new Error('Invalid source directory');
    let credential, owner, expires = 0;
    const normalize = value=>value.replace(/\r\n/g,'\n').replace(/\r/g,'\n');
    const auth = () => {
      if (!credential || Date.now() >= expires) {credential=undefined;throw new Error('Owner session expired. Sign in again.');}
    };
    const github = async (path, method='GET', body, token=credential) => {
      const response = await fetch('https://api.github.com'+path, {
        method, redirect:'error', cache:'no-store', headers:{
          Accept:'application/vnd.github+json', Authorization:'Bearer '+token,
          'X-GitHub-Api-Version':'2026-03-10', ...(body?{'Content-Type':'application/json'}:{})
        }, ...(body?{body:JSON.stringify(body)}:{})
      });
      const data = await response.json();
      if (!response.ok) {
        const error = new Error(response.status===403 ? 'Token cần quyền Contents: Read and write cho CTFWU. / Token requires Contents: Read and write.' : response.status===409 || response.status===422 ? 'GitHub đã thay đổi. Nạp lại file trước khi lưu. / GitHub changed; reload before saving.' : 'GitHub: '+(data.message||response.status));
        error.status=response.status;throw error;
      }
      return data;
    };
    const verify = async token => {
      const user = await github('/user','GET',undefined,token);
      const repository = await github(prefix,'GET',undefined,token);
      if (repository.full_name.toLowerCase()!==repo.toLowerCase() || !user.id || user.id!==repository.owner.id) throw new Error('Chỉ chủ repo được phép sửa. / Only the repository owner may edit.');
      return user.login;
    };
    const head = async ()=> (await github(prefix+'/git/ref/heads/main')).object.sha;
    const source = async (lang, ref) => {
      const path=directory+'/'+(lang==='vi'?'writeup.md':'writeup.en.md');
      const encoded=path.split('/').map(encodeURIComponent).join('/');
      const data=await github(prefix+'/contents/'+encoded+'?ref='+encodeURIComponent(ref));
      if (data.type!=='file') throw new Error('Source is not a file');
      const blob=data.encoding==='base64'?data:await github(prefix+'/git/blobs/'+data.sha);
      const bytes=Uint8Array.from(atob(blob.content.replace(/\s/g,'')),c=>c.charCodeAt(0));
      return {path,version:data.sha,content:new TextDecoder().decode(bytes)};
    };
    const read = async suppliedRef => {
      auth();const ref=/^[a-f0-9]{40}$/.test(suppliedRef||'')?suppliedRef:await head();const variants={};
      for (const lang of ['vi','en']) {
        try {variants[lang]=await source(lang,ref);}
        catch(error){if(error.status!==404)throw error;}
      }
      return {variants};
    };
    const save = async data => {
      auth();await verify(credential);
      if (!Array.isArray(data.edits)||!data.edits.length||data.edits.length>2) throw new Error('Invalid editions');
      const languages=data.edits.map(edit=>edit.lang);
      if (new Set(languages).size!==languages.length || languages.some(lang=>!['vi','en'].includes(lang))) throw new Error('Invalid editions');
      const ref=await head();const entries=[];
      for(const edit of data.edits){
        const current=await source(edit.lang,ref);
        if(current.version!==edit.version)throw new Error('File đã thay đổi. Nạp lại để đối chiếu. / Source changed; reload to compare.');
        if(typeof edit.content!=='string'||!edit.content.trim()||edit.content.includes('\0')||new TextEncoder().encode(edit.content).length>2*1024*1024)throw new Error('Invalid Markdown content');
        if(normalize(edit.content)===normalize(current.content))continue;
        let content=normalize(edit.content);
        if(current.content.split('\n',1)[0].endsWith('\r'))content=content.replace(/\n/g,'\r\n');
        entries.push({path:current.path,mode:'100644',type:'blob',content});
      }
      if(!entries.length)return {saved:false};
      const base=await github(prefix+'/git/commits/'+ref);
      const tree=await github(prefix+'/git/trees','POST',{base_tree:base.tree.sha,tree:entries});
      const commit=await github(prefix+'/git/commits','POST',{
        message:'Edit writeup: '+directory+' ('+languages.map(lang=>lang==='vi'?'VN':'EN').join(' + ')+')',
        tree:tree.sha,parents:[ref]
      });
      // Never force: a concurrent push must fail rather than replace newer work.
      await github(prefix+'/git/refs/heads/main','PATCH',{sha:commit.sha,force:false});
      return {saved:true,published:true,commit_sha:commit.sha,commit_url:'https://github.com/'+repo+'/commit/'+commit.sha};
    };
    return async (url, options={}) => {
      const route=url.split('?')[0];
      const data=options.body?JSON.parse(options.body):{};
      if(route==='/api/editor')return {enabled:true,authenticated:!!credential&&Date.now()<expires,token:'github-session',owner};
      if(route==='/api/login'){
        const token=typeof data.token==='string'?data.token.trim():'';
        if(!token||token.length>512||/[^\x21-\x7e]/.test(token))throw new Error('Invalid GitHub token');
        const login=await verify(token);
        credential=token;owner=login;expires=Date.now()+8*60*60*1000;
        return {authenticated:true,token:'github-session',owner};
      }
      if(route==='/api/logout'){credential=undefined;expires=0;return {authenticated:false};}
      if(route==='/api/writeup')return options.method==='POST'?save(data):read(new URLSearchParams(url.split('?')[1]||'').get('ref'));
      throw new Error('Unsupported editor request');
    };
  };
})();
