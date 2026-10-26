import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile, readdir} from 'node:fs/promises';
import {createServer} from 'node:http';
import {resolve, dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
async function files(directory, prefix = '') {
  const result = [];
  for (const entry of await readdir(directory, {withFileTypes: true})) {
    const name = `${prefix}${entry.name}`;
    if (entry.isDirectory()) result.push(...await files(join(directory, entry.name), `${name}/`));
    else result.push(name);
  }
  return result;
}
test('production/public allowlist contains only intended model and static assets', async () => {
  assert.deepEqual((await files(join(root, 'public'))).sort(), ['favicon.svg', 'models/milestone3/v1/assets.json']);
  const output = await files(join(root, 'dist'));
  assert.ok(output.every(name => name === 'index.html' || name === 'favicon.svg' || name === 'models/milestone3/v1/assets.json' || /^assets\/[^/]+\.(js|mjs|css)$/.test(name)), output.join('\n'));
  const marker = JSON.parse(await readFile(join(root, '../models/browser/v1/completed.json'), 'utf8'));
  const hash = createHash('sha256').update(await readFile(join(root, 'dist/models/milestone3/v1/assets.json'))).digest('hex');
  assert.equal(hash, marker.assets_sha256);
  const html = await readFile(join(root, 'dist/index.html'), 'utf8');
  assert.ok(!/https?:\/\//.test(html), 'No external HTML assets');
  assert.ok(html.includes('./assets/'), 'Relative production entry path');
});
test('production entry, chunks, worker and model resolve under repository prefix', async () => {
  const server = createServer(async (req, res) => {
    if (!req.url.startsWith('/repository/')) {res.writeHead(404).end(); return;}
    const name = decodeURIComponent(req.url.slice('/repository/'.length)) || 'index.html';
    if (name.includes('..')) {res.writeHead(400).end(); return;}
    try {res.writeHead(200); res.end(await readFile(join(root, 'dist', name)));}
    catch {res.writeHead(404).end();}
  });
  await new Promise(resolveReady => server.listen(0, '127.0.0.1', resolveReady));
  try {
    const base = `http://127.0.0.1:${server.address().port}/repository/`;
    const html = await fetch(base).then(response => response.text());
    for (const match of html.matchAll(/(?:src|href)="(\.\/[^"#]+)"/g)) {
      const response = await fetch(new URL(match[1], base));
      assert.equal(response.status, 200, match[1]);
    }
    const response = await fetch(new URL('models/milestone3/v1/assets.json', base));
    assert.equal(response.status, 200);
    assert.equal((await response.json()).threshold, .5);
    const output = await files(join(root, 'dist'));
    for (const name of output.filter(name => name.startsWith('assets/'))) assert.equal((await fetch(new URL(name, base))).status, 200, name);
    assert.ok(output.some(name => /pdf\.worker.*\.mjs$/.test(name)), 'Worker is bundled locally');
  } finally { await new Promise(resolveClosed => server.close(resolveClosed)); }
});
