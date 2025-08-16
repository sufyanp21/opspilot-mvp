#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const projectRoot = process.cwd();
const ignoreDirs = new Set(['node_modules', '.git', '.idea', '.vscode', 'dist', '.next']);
const patterns = [
  /localhost:3000/gi,
  /127\.0\.0\.1:3000/gi,
  /127\.0\.0\.1:8000/gi,
  /localhost:8000/gi,
  /PUBLIC_URL/gi,
  /VITE_[A-Z0-9_]+/g,
  /next\.config\.js/gi,
  /vite\.config\.(ts|js|mjs)/gi,
  /service\s*worker|registerServiceWorker|workbox|navigator\.serviceWorker/gi,
  /legacy|old-frontend|old_ui|legacy-ui/gi,
];

const hits = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (ignoreDirs.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full);
    } else if (entry.isFile()) {
      const rel = path.relative(projectRoot, full).replace(/\\/g, '/');
      if (/\.(png|jpg|jpeg|gif|svg|webp|ico|lock|lockb|zip|gz|tgz|woff2?|eot|ttf|otf)$/i.test(rel)) continue;
      if (/^opspilot-mvp\/apps\/frontend\/node_modules\//.test(rel)) continue;
      let content = '';
      try { content = fs.readFileSync(full, 'utf8'); } catch { continue; }
      const lines = content.split(/\r?\n/);
      patterns.forEach((re) => {
        lines.forEach((line, idx) => {
          const m = line.match(re);
          if (m) hits.push({ file: rel, line: idx + 1, match: m[0], pattern: re.toString(), snippet: line.slice(0, 200) });
        });
      });
    }
  }
}

walk(projectRoot);

fs.mkdirSync(path.join(projectRoot, 'diagnostics'), { recursive: true });
const outJson = path.join(projectRoot, 'diagnostics', 'SCAN_OLD_REFS.json');
fs.writeFileSync(outJson, JSON.stringify({ when: new Date().toISOString(), hits }, null, 2));

const outMd = path.join(projectRoot, 'diagnostics', 'SCAN_OLD_REFS.md');
const table = ['| File | Line | Match | Pattern |', '|---|---:|---|---|', ...hits.map(h => `| ${h.file} | ${h.line} | ${h.match} | ${h.pattern} |`)].join('\n');
fs.writeFileSync(outMd, `# Scan Old References\n\nGenerated: ${new Date().toISOString()}\n\nTotal hits: ${hits.length}\n\n${table}\n`);

console.log(`Wrote findings to:\n- ${outJson}\n- ${outMd}`);


