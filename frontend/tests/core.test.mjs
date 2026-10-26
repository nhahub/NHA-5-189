import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {File} from 'node:buffer';
import {validateFile, parseResume, MAX_FILE_BYTES} from '../src/parsing/documents.js';
import {createInference} from '../src/inference/milestone3.mjs';

test('public model matches the verified export hash', () => {
  const publicBytes = readFileSync(new URL('../public/models/milestone3/v1/assets.json', import.meta.url));
  const marker = JSON.parse(readFileSync(new URL('./model-contract.json', import.meta.url)));
  assert.equal(createHash('sha256').update(publicBytes).digest('hex'), marker.assets_sha256);
});
test('TXT extraction, empty/type/size validation and fallback messages', async () => {
  assert.equal(await parseResume(new File(['Python SQL'], 'resume.txt', {type: 'text/plain'})), 'Python SQL');
  assert.throws(() => validateFile({name:'resume.txt', size: MAX_FILE_BYTES + 1}), /10 MB/);
  assert.throws(() => validateFile(new File(['x'], 'resume.exe')), /paste/);
  assert.throws(() => validateFile(new File([], 'resume.txt')), /empty/);
  assert.throws(() => validateFile(new File(['x'], 'resume.pdf', {type:'image/png'})), /does not match/);
  await assert.rejects(parseResume(new File(['   '], 'empty.txt')), /paste/);
});
test('frozen inference handles synthetic content and unavailable evidence', () => {
  const assets = JSON.parse(readFileSync(new URL('../public/models/milestone3/v1/assets.json', import.meta.url)));
  const engine = createInference(assets);
  const result = engine.analyze('Python JS', 'JavaScript SQL Node.js');
  assert.deepEqual(result.matched_skills, ['javascript']);
  assert.deepEqual(result.job_skills_not_found, ['node.js', 'sql']);
  assert.equal(result.job_skill_coverage, 1/3);
  assert.equal(engine.analyze('Python', 'zzzzqqqq').job_skill_coverage, null);
  assert.throws(() => engine.analyze(' ', 'Python'), /nonempty/);
});
