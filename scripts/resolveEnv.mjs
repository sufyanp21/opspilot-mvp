#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const root = process.cwd();
const envFiles = [
  path.join(root, 'apps/web/.env.local'),
  path.join(root, 'apps/web/.env'),
  path.join(root, '.env.local'),
  path.join(root, '.env'),
];

const resolved = {};
for (const f of envFiles) {
  if (fs.existsSync(f)) {
    const content = fs.readFileSync(f, 'utf8');
    for (const line of content.split(/\r?\n/)) {
      const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
      if (m) {
        const [, k, v] = m;
        resolved[k] = v;
      }
    }
  }
}

// Include process env as well
for (const [k, v] of Object.entries(process.env)) {
  if (/^(VITE_|NEXT_PUBLIC_|CORS_|API_|GIT_SHA)/.test(k)) {
    if (!(k in resolved)) resolved[k] = v;
  }
}

fs.mkdirSync(path.join(root, 'diagnostics'), { recursive: true });
fs.writeFileSync(
  path.join(root, 'diagnostics', 'ENV_RESOLUTION.md'),
  `# Env Resolution (apps/web)\n\n${Object.entries(resolved)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `- ${k}: ${v}`)
    .join('\n')}\n`
);

console.log('Wrote diagnostics/ENV_RESOLUTION.md');


