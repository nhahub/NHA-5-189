import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {createInference} from '../src/inference/milestone3.mjs';

const base = new URL(process.env.PAGE_URL ?? process.argv[2]);
assert.equal(base.protocol, 'https:');
const checks = [];
async function get(url) {
  let last;
  for (let attempt = 0; attempt < 5; attempt++) {
    try {
      const response = await fetch(url, {cache: 'no-store', signal: AbortSignal.timeout(15000)});
      assert.equal(response.status, 200, String(url));
      const bytes = Buffer.from(await response.arrayBuffer());
      checks.push({url: String(url), status: response.status, bytes: bytes.length});
      return bytes;
    } catch (error) {
      last = error;
      if (attempt < 4) await new Promise(resolve => setTimeout(resolve, 15000));
    }
  }
  throw last;
}

const html = (await get(base)).toString('utf8');
assert.ok(html.includes('Resume Skill Gap Analyzer'));
const queue = [...html.matchAll(/(?:src|href)="([^"#]+)"/g)].map(match => new URL(match[1], base));
const seen = new Set();
let pdfWorker = false, pdf = false, docx = false;
while (queue.length) {
  const url = queue.shift();
  if (seen.has(String(url))) continue;
  seen.add(String(url));
  assert.equal(url.origin, base.origin);
  assert.ok(url.pathname.startsWith(base.pathname));
  const bytes = await get(url);
  pdfWorker ||= /pdf\.worker.*\.mjs$/.test(url.pathname);
  pdf ||= /\/pdf-[^.]+\.js$/.test(url.pathname);
  docx ||= /mammoth\.browser/.test(url.pathname);
  if (/\.(?:m?js)$/.test(url.pathname)) {
    for (const match of bytes.toString('utf8').matchAll(/(?:assets\/|\.\/)[A-Za-z0-9._-]+\.(?:mjs|js|css)/g)) {
      if (!/-[A-Za-z0-9_-]{8}\.(?:mjs|js|css)$/.test(match[0])) continue;
      queue.push(new URL(match[0], match[0].startsWith('assets/') ? base : url));
    }
  }
}
assert.ok(pdfWorker && pdf && docx, 'Local PDF worker and document-parsing chunks must resolve');
const model = await get(new URL('models/milestone3/v1/assets.json', base));
const contract = JSON.parse(readFileSync(new URL('../tests/model-contract.json', import.meta.url), 'utf8'));
const modelHash = createHash('sha256').update(model).digest('hex');
assert.equal(modelHash, contract.assets_sha256);
assert.ok((await get(new URL('methodology.html', base))).toString('utf8').includes('Methodology and limitations'));

// Use live model bytes in Node; this is not a browser interaction check.
const engine = createInference(JSON.parse(model));
const references = JSON.parse(readFileSync(new URL('../tests/fixtures/synthetic-python-references.json', import.meta.url), 'utf8'));
for (const reference of references) {
  const result = engine.analyze(reference.resume, reference.job);
  assert.equal(result.model_classification, reference.expected.model_classification);
  for (const key of ['resume_skills', 'job_skills', 'matched_skills', 'job_skills_not_found']) assert.deepEqual(result[key], reference.expected[key]);
  for (const [key, expected] of Object.entries(reference.expected.model_features)) {
    assert.ok(Math.abs(result.model_features[key] - expected) <= 1e-8 + 1e-7 * Math.abs(expected));
  }
}
const excluded = [];
for (const path of ['tests/browser.html', 'src/main.jsx', 'data/raw/cv.csv', 'models/milestone3/v2/logistic_regression.joblib']) {
  const response = await fetch(new URL(path, base), {signal: AbortSignal.timeout(15000)});
  excluded.push({path, status: response.status});
  assert.equal(response.status, 404, path);
}
console.log(JSON.stringify({site_url: String(base), checks, model_sha256: modelHash,
  parsing_assets_resolved: {pdfWorker, pdf, docx}, synthetic_reference_cases_passed_in_node: references.length,
  excluded_paths: excluded, browser_interactions: 'not tested'}, null, 2));
