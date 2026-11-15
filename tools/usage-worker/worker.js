// ----------------------------------------------------------------------------------------------------------------------
// Roster-5 Satellite Live Viewer
// worker.js - usage relay: receives a start-up ping from the viewer and appends one line to a text file on GitHub
//
// Author:        Chad Burge
// Created:       2026-11-15
// Repository:    github.com/chadburge/nro-orbit-watch (this file lives in tools/usage-worker)
// Ownership:     Copyright (c) 2026 Chad Burge. All rights reserved.
//
// Why a relay: the viewer runs in other people's browsers and on other people's machines, so it cannot carry a GitHub
// token. This Cloudflare Worker holds the token as a secret, sees the caller's public IP address and location from the
// request, and does the GitHub write. Deploy with `wrangler deploy`; see README.md beside this file.
// ----------------------------------------------------------------------------------------------------------------------
export default {
  async fetch(req, env) {
    const cors = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' };
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
    if (req.method !== 'POST') return new Response('viewer usage relay: POST a JSON ping', { headers: cors });
    let body = {};
    try { const text = await req.text(); if (text.length < 4000) body = JSON.parse(text); } catch (e) {}
    const c = req.cf || {}, ip = req.headers.get('cf-connecting-ip') || '';
    const line = [new Date().toISOString().slice(0, 19) + 'Z', ip, [c.city, c.region, c.country].filter(Boolean).join(', '),
      s(body.mode), s(body.host), s(body.build), s(body.id), s(body.screen), s(body.ua).slice(0, 90)].join(' | ');
    try { await append(env, line); } catch (e) { return new Response('log failed: ' + e.message, { status: 500, headers: cors }); }
    return new Response('ok', { headers: cors });
  }
};
const s = (v) => String(v ?? '').replace(/[|\r\n]/g, ' ').trim().slice(0, 120);
const dec = (b64) => new TextDecoder().decode(Uint8Array.from(atob(b64.replace(/\n/g, '')), ch => ch.charCodeAt(0)));
const enc = (str) => { const bytes = new TextEncoder().encode(str); let bin = ''; for (const b of bytes) bin += String.fromCharCode(b); return btoa(bin); };
// read-modify-write of the log file through the GitHub contents API; a concurrent write makes GitHub reject the stale
// sha, so retry a few times with the fresh content
async function append(env, line) {
  const url = `https://api.github.com/repos/${env.REPO}/contents/${env.FILE}`;
  const h = { 'Authorization': `Bearer ${env.GITHUB_TOKEN}`, 'User-Agent': 'r5-viewer-usage', 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json' };
  for (let k = 0; k < 4; k++) {
    let sha, text = '';
    const g = await fetch(url + '?t=' + Date.now(), { headers: h });
    if (g.ok) { const j = await g.json(); sha = j.sha; text = dec(j.content); } else if (g.status !== 404) throw new Error('read ' + g.status);
    if (text && !text.endsWith('\n')) text += '\n';
    const put = await fetch(url, { method: 'PUT', headers: h, body: JSON.stringify({ message: 'usage ' + line.slice(0, 20), content: enc(text + line + '\n'), sha }) });
    if (put.ok) return;
    if (put.status !== 409 && put.status !== 422) throw new Error('write ' + put.status);
    await new Promise(r => setTimeout(r, 300 + 400 * k));
  }
  throw new Error('conflict');
}
