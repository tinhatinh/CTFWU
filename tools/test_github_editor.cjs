// Mocked GitHub API: tests never create a real commit or send a credential.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const code = fs.readFileSync('site/assets/js/github-editor.js','utf8');
function fixture({nonOwner=false,race=false,directory='Example CTF/sample'}={}) {
  const calls=[];
  const files={vi:{content:'# VN\nNội dung.\n',sha:'old-vn'},en:{content:'# EN\nOriginal.\n',sha:'old-en'}};
  let committed, tree;
  const context={window:{},document:{querySelector:()=>({dataset:{sourceDirectory:directory}})},
    TextDecoder,TextEncoder,Uint8Array,URLSearchParams,Date,atob,
    fetch:async(url,options)=>{
      const path=new URL(url).pathname;
      const body=options.body?JSON.parse(options.body):null;
      calls.push({path,method:options.method,body});
      let data,status=200;
      if(path==='/user')data={id:nonOwner?99:1,login:nonOwner?'other':'tinhatinh'};
      else if(path==='/repos/tinhatinh/CTFWU')data={full_name:'tinhatinh/CTFWU',owner:{id:1}};
      else if(path.endsWith('/git/ref/heads/main'))data={object:{sha:'a'.repeat(40)}};
      else if(path.includes('/contents/')){
        const lang=path.endsWith('writeup.en.md')?'en':'vi';
        data={type:'file',sha:files[lang].sha,encoding:'base64',content:Buffer.from(files[lang].content).toString('base64')};
      }else if(path.endsWith('/git/commits/'+'a'.repeat(40)))data={tree:{sha:'base-tree'}};
      else if(path.endsWith('/git/trees')){tree=body;data={sha:'new-tree'};}
      else if(path.endsWith('/git/commits')){committed=body;data={sha:'b'.repeat(40)};}
      else if(path.endsWith('/git/refs/heads/main')){
        if(race){status=422;data={message:'Not fast forward'};}
        else{for(const entry of tree.tree){const lang=entry.path.endsWith('writeup.en.md')?'en':'vi';files[lang]={content:entry.content,sha:'new-'+lang};}data={object:{sha:body.sha}};}
      }else throw new Error('Unexpected API path '+path);
      return {ok:status===200,status,json:async()=>data};
    }};
  vm.createContext(context);vm.runInContext(code,context);
  return {request:context.window.createGithubEditor(),calls,files,get tree(){return tree;},get committed(){return committed;}};
}
async function login(instance){return instance.request('/api/login',{method:'POST',body:JSON.stringify({token:'test-only-token'})});}
async function save(instance,edits){return instance.request('/api/writeup',{method:'POST',body:JSON.stringify({edits})});}
(async()=>{
  const outsider=fixture({nonOwner:true});
  await assert.rejects(()=>login(outsider),/Only the repository owner/);
  assert.equal(outsider.calls.filter(call=>call.method!=='GET').length,0);
  const instance=fixture();
  await assert.rejects(()=>instance.request('/api/writeup'),/session expired/);
  await login(instance);
  const source=await instance.request('/api/writeup');
  assert.equal(source.variants.vi.content,'# VN\nNội dung.\n');
  await assert.rejects(()=>save(instance,[{lang:'vi',version:'stale',content:'# Change'}]),/Source changed/);
  assert.equal(instance.calls.filter(call=>call.method!=='GET').length,0);
  const result=await save(instance,[{lang:'vi',version:'old-vn',content:'# VN revised\n'},{lang:'en',version:'old-en',content:'# EN revised\n'}]);
  assert.equal(result.published,true);assert.equal(instance.tree.base_tree,'base-tree');
  assert.equal(instance.tree.tree.length,2);assert.equal(instance.committed.parents[0],'a'.repeat(40));
  assert.equal(instance.calls.filter(call=>call.method==='PATCH').length,1);
  assert.equal(instance.calls.find(call=>call.method==='PATCH').body.force,false);
  assert.equal(instance.files.en.content,'# EN revised\n');
  await instance.request('/api/logout');
  await assert.rejects(()=>save(instance,[{lang:'vi',version:'new-vi',content:'# VN'}]),/session expired/);
  const concurrent=fixture({race:true});await login(concurrent);
  await assert.rejects(()=>save(concurrent,[{lang:'vi',version:'old-vn',content:'# Changed'}]),/GitHub changed/);
  assert.equal(concurrent.files.vi.sha,'old-vn');
  const wave=fixture({directory:'Example CTF/Wave 2/sample'});await login(wave);
  await save(wave,[{lang:'vi',version:'old-vn',content:'# Wave VN\n'}]);
  assert.equal(wave.tree.tree[0].path,'Example CTF/Wave 2/sample/writeup.md');
  assert(wave.calls.some(call=>call.path.includes('/contents/Example%20CTF/Wave%202/sample/writeup.md')));
  assert.throws(()=>fixture({directory:'Example CTF/Wave 2/../sample'}),/Invalid source directory/);
  assert.throws(()=>fixture({directory:'Example CTF/arbitrary/sample'}),/Invalid source directory/);
  console.log('GitHub editor checks passed: owner, UTF-8, conflict, bilingual commit, logout, concurrent push');
})().catch(error=>{console.error(error);process.exitCode=1;});
