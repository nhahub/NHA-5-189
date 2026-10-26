import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {createServer} from 'vite';
import {createInference} from '../src/inference/milestone3.mjs';
import {getSkillGuidance} from '../src/feedbackGuidance.js';
import viteConfig from '../vite.config.js';

const assets = JSON.parse(readFileSync(new URL('../public/models/milestone3/v1/assets.json', import.meta.url)));
test('results preserve unavailable coverage and keep model internals out of rendered UI', async () => {
  const server = await createServer({server: {middlewareMode: true}, appType: 'custom'});
  try {
    const {default: Results} = await server.ssrLoadModule('/src/components/AnalysisResults.jsx');
    const result = createInference(assets).analyze('Python JS', 'zzzzqqqq');
    const html = renderToStaticMarkup(createElement(Results, {result}));
    assert.ok(html.includes('Unavailable'));
    assert.ok(html.includes('No job skills detected.'));
    assert.ok(html.includes('Resume–Job Assessment'));
    assert.ok(html.includes('An automated assessment based on the information provided.'));
    for (const label of ['Job-Skill Coverage', 'Text Similarity', 'Matched Skills', 'Skills to Highlight or Develop', 'Recommended Improvements']) assert.ok(html.includes(label), label);
    assert.ok(html.includes('These skills appear in the job description but were not identified in your resume.'));
    assert.ok(!html.includes(String(result.classifier_score)));
    assert.ok(!html.includes('model_features') && !html.includes('diagnostics'));
  } finally {await server.close();}
});
test('model-loading shares one engine and permits retry after a failed fetch', async () => {
  const server = await createServer({server: {middlewareMode: true}, appType: 'custom'});
  const originalFetch = globalThis.fetch;
  let requests = 0;
  globalThis.fetch = async url => {
    assert.equal(url, `${viteConfig.base}models/milestone3/v1/assets.json`);
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

test('UI guidance is conditional, skill-specific and preserves every detected gap', async () => {
  assert.equal(getSkillGuidance('node.js').advice, 'If you have Node.js experience, highlight a relevant application or API project. Otherwise, consider developing this skill through a practical project.');
  assert.match(getSkillGuidance('sql').advice, /filtering, joins, and aggregations/);
  assert.match(getSkillGuidance('testing').advice, /tools and types of tests/);
  assert.match(getSkillGuidance('project').advice, /If you have experience with project/);
  const server = await createServer({server: {middlewareMode: true}, appType: 'custom'});
  try {
    const {default: Suggestions} = await server.ssrLoadModule('/src/components/ImprovementSuggestions.jsx');
    const result = createInference(assets).analyze('Python', 'Node.js SQL testing project');
    const unchanged = JSON.stringify(result);
    const html = renderToStaticMarkup(createElement(Suggestions, {suggestions: result.suggestions, hasJobSkills: true}));
    assert.equal((html.match(/<li\b/g) ?? []).length, result.job_skills_not_found.length);
    assert.ok(html.includes('<h4>project</h4>'), 'Generic skill stays visible');
    assert.ok(!html.includes('Mentioned in the job description; not found'), 'Avoid repeating the gap explanation per suggestion');
    assert.equal(JSON.stringify(result), unchanged, 'Presentation must not mutate engine results');
  } finally {await server.close();}
});

test('main workflow keeps methodology discreet and omits the dataset notice', async () => {
  const server = await createServer({server: {middlewareMode: true}, appType: 'custom'});
  try {
    const {default: App} = await server.ssrLoadModule('/src/App.jsx');
    const html = renderToStaticMarkup(createElement(App));
    assert.ok(html.includes('<summary>Methodology'));
    assert.ok(html.includes(`href="${viteConfig.base}methodology.html"`));
    assert.ok(!html.includes('49 development pairs'));
    assert.ok(!html.includes('automated labels') && !html.includes('independent verification'));
    const documentation = readFileSync(new URL('../public/methodology.html', import.meta.url), 'utf8');
    assert.ok(documentation.includes('46 automated annotations') && documentation.includes('three recorded first-review decisions'));
    assert.ok(documentation.includes('without independent human verification'));
  } finally {await server.close();}
});

test('reading text remains at least 14px with 16px inputs and sufficient secondary contrast', () => {
  const css = readFileSync(new URL('../src/styles.css', import.meta.url), 'utf8');
  const sizes = [...css.matchAll(/font-size\s*:\s*(\d+)px/g)].map(match => Number(match[1]));
  assert.ok(sizes.every(size => size >= 14));
  assert.match(css, /textarea\s*\{\s*font-size:\s*16px/);
  assert.match(css, /\.suggestion-list p[^{}]*\{\s*font-size:\s*16px/);
  function luminance(hex) {
    const channels = hex.match(/\w\w/g).map(value => parseInt(value, 16) / 255).map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4);
    return channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722;
  }
  const contrast = (a, b) => (Math.max(luminance(a), luminance(b)) + .05) / (Math.min(luminance(a), luminance(b)) + .05);
  assert.ok(contrast('53647b', 'ffffff') >= 4.5);
  assert.ok(contrast('c8d6ec', '142442') >= 4.5);
});
