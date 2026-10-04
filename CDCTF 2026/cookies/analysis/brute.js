const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const crypto = require('crypto');
const fs = require('fs');

const H = process.env.TOK_H || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9';
const P = process.env.TOK_P || 'eyJ1c2VyX2Nvb2tpZV9iYWxhbmNlIjowfQ';
const SIGB64 = process.env.TOK_SIG || 'tZeCDGDWQMirKqWJ3tx3r4rmxSaFTPmOqFgU-Koq8Xg';
const MSG = Buffer.from(`${H}.${P}`);
const SIG = Buffer.from(SIGB64.replace(/-/g, '+').replace(/_/g, '/'), 'base64');
const FILE = process.env.WL || 'C:/Tools/rockyou.txt';
const N = Number(process.env.WORKERS || 8);

if (isMainThread) {
  const total = fs.readFileSync(FILE, 'latin1').split('\n').length;
  console.log(`wordlist=${FILE} lines=${total} workers=${N}`);
  let found = 0, done = 0;
  const t0 = Date.now();
  const timer = setInterval(() => console.log(`  ...${((Date.now() - t0) / 1000).toFixed(0)}s`), 30000);
  const onDone = () => {
    if (++done < N) return;
    clearInterval(timer);
    console.log(`${found ? 'FOUND' : 'NONE'} after ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  };
  for (let i = 0; i < N; i++) {
    const w = new Worker(__filename, { workerData: { id: i } });
    w.on('message', (m) => {
      if (m.type === 'found') { found++; console.log(`SECRET=${JSON.stringify(m.secret)} line=${m.line}`); }
      else onDone();
    });
    w.on('error', (e) => { console.log('worker error:', e.message); onDone(); });
  }
} else {
  const { id } = workerData;
  const lines = fs.readFileSync(FILE, 'latin1').split('\n');
  for (let i = id; i < lines.length; i += N) {
    const c = lines[i].replace(/\r$/, '');
    if (!c) continue;
    const d = crypto.createHmac('sha256', c).update(MSG).digest();
    if (crypto.timingSafeEqual(d, SIG)) { parentPort.postMessage({ type: 'found', secret: c, line: i }); break; }
  }
  parentPort.postMessage({ type: 'done' });
}
