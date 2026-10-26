import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {File} from 'node:buffer';
import {parseResume} from '../src/parsing/documents.js';

test('synthetic DOCX plain-text extraction through the browser-distribution module in Node', async () => {
  const bytes = readFileSync(new URL('./fixtures/synthetic-resume.docx', import.meta.url));
  const text = await parseResume(new File([bytes], 'synthetic-resume.docx', {type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}));
  assert.ok(text.includes('Python, JavaScript and SQL.'));
  assert.ok(text.includes('Git and Node.js.'));
  assert.ok(!text.includes('<w:') && !text.includes('<html'));
});
