import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {createServer} from 'vite';
import {createInference} from '../src/inference/milestone3.mjs';

const assets = JSON.parse(readFileSync(new URL('../public/models/milestone3/v1/assets.json', import.meta.url)));
test('results preserve unavailable coverage and keep model internals out of rendered UI', async () => {
  const server = await createServer({server: {middlewareMode: true}, appType: 'custom'});
  try {
    const {default: Results} = await server.ssrLoadModule('/src/components/AnalysisResults.jsx');
    const result = createInference(assets).analyze('Python JS', 'zzzzqqqq');
    const html = renderToStaticMarkup(createElement(Results, {result}));
    assert.ok(html.includes('Unavailable'));
    assert.ok(html.includes('No job skills detected.'));
    assert.ok(html.includes('Model assessment'));
    assert.ok(!html.includes(String(result.classifier_score)));
    assert.ok(!html.includes('model_features') && !html.includes('diagnostics'));
  } finally {await server.close();}
});
test('model-loading shares one engine and permits retry after a failed fetch', async () => {
  const server = await createServer({server: {middlewareMode: true}, appType: 'custom'});
  const originalFetch = globalThis.fetch;
  let requests = 0;
  globalThis.fetch = async url => {
    assert.equal(url, '/models/milestone3/v1/assets.json');
    requests++;
    return requests === 1 ? {ok: false, status: 503} : {ok: true, json: async () => assets};
  };
  try {
    const {loadEngine} = await server.ssrLoadModule('/src/model.js');
    const first = loadEngine();
    assert.equal(first, loadEngine());
    await assert.rejects(first, /503/);
    const loaded = await loadEngine();
    assert.equal(await loadEngine(), loaded);
    assert.equal(requests, 2);
    assert.ok(loaded.analyze('Python', 'Python').model_classification);
  } finally {globalThis.fetch = originalFetch; await server.close();}
});
