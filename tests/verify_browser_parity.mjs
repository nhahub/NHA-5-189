// Real validation text stays in process memory; the saved report contains aggregates only.
import {readFileSync, writeFileSync, existsSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {resolve, relative} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {createInference, loadBrowserAssets} from '../frontend/src/inference/milestone3.mjs';

const root = resolve(process.argv[2] ?? '.');
const python = process.argv[3];
if (!python) throw new Error('Usage: node tests/verify_browser_parity.mjs ROOT PYTHON [EXPORT_VERSION]');
const exportVersion = process.argv[4] ?? 'v1';
const directory = resolve(root, 'models/browser', exportVersion);
const bytes = readFileSync(resolve(directory, 'assets.json'));
const marker = JSON.parse(readFileSync(resolve(directory, 'completed.json'), 'utf8'));
const sha = value => createHash('sha256').update(value).digest('hex');
assert.equal(sha(bytes), marker.assets_sha256, 'Export hash');
for (const [name, hash] of Object.entries(marker.source_fingerprints)) assert.equal(sha(readFileSync(resolve(root, name))), hash, `Source changed: ${name}`);
const assets = JSON.parse(bytes);
const engine = createInference(assets);
const code = `import sys,os,io,json\nfrom contextlib import redirect_stdout,ExitStack\nfrom unittest.mock import patch\nsys.path.insert(0,os.getcwd())\nfrom src import milestone3 as m\nfrom src.milestone3_export import references\nwith ExitStack() as stack:\n for cls in [m.Pipeline,m.LogisticRegression,m.StandardScaler,m.TfidfVectorizer]:\n  for name in ['fit','fit_transform']:\n   if hasattr(cls,name):stack.enter_context(patch.object(cls,name,side_effect=AssertionError('Fitting forbidden')))\n with redirect_stdout(io.StringIO()):result=references(os.getcwd())\nprint(json.dumps(result,ensure_ascii=True,allow_nan=False))`;
const refs = JSON.parse(execFileSync(python, ['-c', code], {cwd: root, encoding: 'utf8', maxBuffer: 20 * 1024 * 1024}));
const absoluteTolerance = 1e-8, relativeTolerance = 1e-7;
const differences = {vectors: 0, features: 0, scaled: 0, decision: 0, score: 0};
function near(actual, expected, type) {
  assert.ok(Number.isFinite(actual) && Number.isFinite(expected));
  const difference = Math.abs(actual - expected);
  differences[type] = Math.max(differences[type], difference);
  assert.ok(difference <= absoluteTolerance + relativeTolerance * Math.abs(expected), `${type}: ${actual} vs ${expected}`);
}
let valid = 0, rejected = 0;
for (const ref of refs.cases) {
  if (ref.error) {
    assert.throws(() => engine.analyze(ref.resume, ref.job), {message: ref.error}); rejected++; continue;
  }
  const actual = engine.analyze(ref.resume, ref.job), expected = ref.feedback;
  for (const name of ['resume_skills', 'job_skills', 'matched_skills', 'job_skills_not_found', 'model_classification', 'suggestions', 'skill_evidence_note', 'score_note', 'classification_threshold']) {
    assert.deepEqual(actual[name], expected[name], `${ref.name}: ${name}`);
  }
  assert.deepEqual(Object.keys(actual).filter(key => key !== 'diagnostics').sort(), Object.keys(expected).sort());
  assert.deepEqual(actual.diagnostics.normalized, ref.normalized, `${ref.name}: normalization`);
  assert.deepEqual(actual.diagnostics.tokens, ref.tokens, `${ref.name}: tokens`);
  for (let i = 0; i < 2; i++) {
    const keys = new Set([...Object.keys(actual.diagnostics.vectors[i]), ...Object.keys(ref.vectors[i])]);
    for (const key of keys) near(actual.diagnostics.vectors[i][key] ?? 0, ref.vectors[i][key] ?? 0, 'vectors');
  }
  if (expected.job_skill_coverage === null) assert.equal(actual.job_skill_coverage, null);
  else near(actual.job_skill_coverage, expected.job_skill_coverage, 'features');
  for (const name of assets.feature_order) near(actual.model_features[name], expected.model_features[name], 'features');
  actual.diagnostics.scaled.forEach((value, i) => near(value, ref.scaled[i], 'scaled'));
  near(actual.diagnostics.decision, ref.decision, 'decision');
  near(actual.classifier_score, expected.classifier_score, 'score');
  JSON.parse(JSON.stringify(actual)); valid++;
}
for (const ref of refs.boundary) {
  const actual = engine.scoreFeatures(ref.features);
  actual.scaled.forEach((value, i) => near(value, ref.scaled[i], 'scaled'));
  near(actual.decision, ref.decision, 'decision'); near(actual.score, ref.score, 'score');
  assert.equal(actual.suitable, ref.suitable, 'Boundary classification');
}
assert.equal(engine.classifyScore(.5), true, 'Score .5 is suitable');
assert.equal(engine.classifyScore(.5 - Number.EPSILON), false, 'Score below .5 is unsuitable');
assert.throws(() => engine.analyze('\ud800', 'Python'), /surrogates/);
let requestedUrl;
await loadBrowserAssets('/repository/models/v1/', {fetchImpl: async url => {requestedUrl = url; return {ok: true, json: async () => assets};}});
assert.equal(requestedUrl, '/repository/models/v1/assets.json');
for (const [name, hash] of Object.entries(marker.source_fingerprints)) assert.equal(sha(readFileSync(resolve(root, name))), hash, `Source changed during verification: ${name}`);
const result = {schema_version: 1, export_version: exportVersion, assets_bytes: bytes.length, assets_sha256: sha(bytes),
  python: refs.python, node: process.version, reference_cases: refs.cases.length, valid_text_pairs: valid, rejected_empty_pairs: rejected,
  validation_pairs: refs.cases.filter(row => row.name.startsWith('validation_')).length, boundary_cases: refs.boundary.length,
  absolute_tolerance: absoluteTolerance, relative_tolerance: relativeTolerance, maximum_absolute_differences: differences,
  exact_classification_agreement: `${valid + refs.boundary.length}/${valid + refs.boundary.length}`,
  exact_skill_set_agreement: `${valid}/${valid}`, exact_feedback_suggestions: true,
  no_training_or_tuning: true, real_reference_documents_saved: false,
  implementation_hashes: Object.fromEntries(['frontend/src/inference/milestone3.mjs', 'tests/verify_browser_parity.mjs'].map(name => [name, sha(readFileSync(resolve(root, name)))]))};
let report = resolve(root, 'reports/milestone3/browser_parity_v1.json'), number = 1;
while (existsSync(report)) {
  if (readFileSync(report, 'utf8') === JSON.stringify(result, null, 2)) break;
  report = resolve(root, `reports/milestone3/browser_parity_v${++number}.json`);
}
if (!existsSync(report)) writeFileSync(report, JSON.stringify(result, null, 2), {flag: 'wx'});
console.log(JSON.stringify(result, null, 2));
console.log(`Saved aggregate report: ${relative(root, report)}`);
