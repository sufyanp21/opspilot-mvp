#!/usr/bin/env node
import http from 'http';
import { spawn } from 'child_process';

const mode = process.argv[2] || 'dev'; // dev|preview
let port = 5173;
const startCmd = mode === 'preview' ? ['npm', ['run', 'preview', '--', '--port', String(port)]] : ['npm', ['run', 'dev']];

function fetch(pathname = '/') {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: 'localhost', port, path: pathname, method: 'GET' }, (res) => {
      let data = '';
      res.on('data', (c) => (data += c.toString()));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
    });
    req.on('error', reject);
    req.end();
  });
}

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function run() {
  const child = spawn(startCmd[0], startCmd[1], { cwd: 'apps/web', shell: true, stdio: 'pipe' });
  let ready = false;
  child.stdout.on('data', (d) => {
    const s = String(d);
    const m = s.match(/Local:\s*https?:\/\/localhost:(\d+)/i);
    if (m) port = Number(m[1]);
    if (s.includes('Local:') || s.includes('ready in')) ready = true;
    process.stdout.write(s);
  });
  child.stderr.on('data', (d) => process.stderr.write(String(d)));

  let attempts = 0;
  while (!ready && attempts < 60) { await wait(500); attempts++; }
  await wait(1000);

  const results = [];
  try {
    const root = await fetch('/');
    const hasBeaconMeta = /name="x-git-sha"/.test(root.body) && /name="x-build-time"/.test(root.body);
    results.push({ check: 'index meta beacons', pass: hasBeaconMeta });

    const html = root.body || '';
    const assetRefs = (html.match(/\/(assets|src)\/[A-Za-z0-9_\/.\-]+/g) || []).filter(Boolean);
    const hasLegacyPort = html.includes('localhost:3000') || html.includes('127.0.0.1:3000');
    results.push({ check: 'no legacy port refs', pass: !hasLegacyPort });

    // Basic beacon presence expectation in runtime (footer) cannot be verified via static fetch; we accept meta as proxy.

    const pass = results.every(r => r.pass);
    const summary = { mode, port, results, pass };

    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const fs = await import('fs');
    const p = await import('path');
    fs.mkdirSync('diagnostics', { recursive: true });
    fs.writeFileSync(p.join('diagnostics', `VERIFY_${mode}_${ts}.md`), `# Verify New UI (${mode})\n\n${JSON.stringify(summary, null, 2)}\n`);
    console.log(JSON.stringify(summary, null, 2));
  } catch (err) {
    console.error(err);
  } finally {
    child.kill('SIGTERM');
  }
}

run();


