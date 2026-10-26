const frame = document.querySelector('#app'), log = document.querySelector('#log');
document.querySelector('#desktop').onclick = () => { frame.width = '1120'; };
document.querySelector('#mobile').onclick = () => { frame.width = '390'; };
const sleep = time => new Promise(resolve => setTimeout(resolve, time));
function assert(condition, message) { if (!condition) throw new Error(message); }
async function waitFor(test, message) {
  for (let i = 0; i < 150; i++) { if (test()) return; await sleep(100); }
  throw new Error(`Timed out: ${message}`);
}
document.querySelector('#run').onclick = async () => {
  log.textContent = '';
  const say = text => {log.textContent += text + '\n';};
  try {
    const w = frame.contentWindow, d = w.document;
    const button = text => [...d.querySelectorAll('button')].find(element => element.textContent.includes(text));
    const edit = (selector, value) => {const element = d.querySelector(selector); Object.getOwnPropertyDescriptor(w.HTMLTextAreaElement.prototype, 'value').set.call(element, value); element.dispatchEvent(new w.Event('input', {bubbles: true}));};
    const choose = file => {const transfer = new w.DataTransfer(); transfer.items.add(file); const input = d.querySelector('input[type=file]'); input.files = transfer.files; input.dispatchEvent(new w.Event('change', {bubbles: true}));};
    await waitFor(() => button('Retry loading'), 'model load failure');
    button('Retry loading').click();
    await waitFor(() => d.body.textContent.includes('Analyzer ready'), 'model retry'); say('PASS model-load error and retry');
    button('Analyze resume').click();
    await waitFor(() => d.querySelector('[role=alert]'), 'empty input error'); say('PASS empty inputs rejected');
    button('Load example').click(); await sleep(50);
    const {createInference} = await import('../src/inference/milestone3.mjs');
    const assets = await w.referenceFetch('/models/milestone3/v1/assets.json').then(response => response.json());
    const engine = createInference(assets);
    const expected = engine.analyze(d.querySelector('#resume-text').value, d.querySelector('#job-text').value);
    button('Analyze resume').click();
    await waitFor(() => d.querySelector('#results-title'), 'synthetic results');
    assert(d.querySelector('.assessment h3').textContent === expected.model_classification, 'classification mismatch');
    const cards = d.querySelectorAll('.metric strong');
    assert(cards[0].textContent === `${(expected.job_skill_coverage * 100).toFixed(1)}%`, 'coverage mismatch');
    assert(cards[1].textContent === `${(expected.tfidf_text_similarity * 100).toFixed(1)}%`, 'similarity mismatch');
    assert(d.querySelectorAll('.skill-list.matched li').length === expected.matched_skills.length, 'matched skill list mismatch');
    say('PASS synthetic example matches verified inference engine');
    edit('#job-text', 'zzzzqqqq'); await sleep(60);
    assert(!d.querySelector('#results-title'), 'stale results after edit');
    button('Analyze resume').click(); await waitFor(() => d.querySelector('#results-title'), 'no skills results');
    assert(d.querySelector('.metric strong').textContent === 'Unavailable', 'null coverage not preserved');
    say('PASS input changes invalidate results; null coverage displays Unavailable');
    for (const extension of ['txt', 'docx', 'pdf']) {
      const bytes = await fetch(`./fixtures/synthetic-resume.${extension}`).then(response => response.arrayBuffer());
      const types = {txt: 'text/plain', docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', pdf: 'application/pdf'};
      choose(new w.File([bytes], `synthetic-resume.${extension}`, {type: types[extension]}));
      await waitFor(() => d.body.textContent.includes('Text extracted.'), `${extension} parsing`);
      assert(d.querySelector('#resume-text').value.includes('Python'), `${extension} text extraction`);
      if (extension === 'pdf') assert(d.querySelector('#resume-text').value.includes('\n\n'), 'PDF page separation');
      say(`PASS ${extension.toUpperCase()} extracted in browser`);
    }
    choose(new w.File(['invalid pdf'], 'broken.pdf', {type: 'application/pdf'}));
    await waitFor(() => d.querySelector('.error-text'), 'file error');
    assert(d.querySelector('.error-text').textContent.includes('paste'), 'missing pasted-text fallback');
    say('PASS damaged document error offers pasted-text fallback');
    const oversized = new w.File([new Uint8Array(10 * 1024 * 1024 + 1)], 'large.txt', {type: 'text/plain'});
    choose(oversized); await waitFor(() => d.body.textContent.includes('10 MB limit'), 'file size validation');
    say('PASS 10 MB upload limit');
    let release;
    const delayed = new w.File(['old text'], 'older.txt', {type: 'text/plain'});
    delayed.arrayBuffer = () => new Promise(resolve => {release = resolve;});
    choose(delayed); await sleep(30); button('Clear all').click(); await sleep(30);
    release(new TextEncoder().encode('OLD CONTENT MUST NOT RETURN').buffer); await sleep(80);
    assert(d.querySelector('#resume-text').value === '', 'old file replaced cleared input');
    let replaceRelease;
    const delayed2 = new w.File(['old'], 'replace-me.txt', {type: 'text/plain'});
    delayed2.arrayBuffer = () => new Promise(resolve => {replaceRelease = resolve;});
    choose(delayed2); await sleep(30);
    choose(new w.File(['NEW CONTENT Python'], 'newer.txt', {type: 'text/plain'}));
    await waitFor(() => d.querySelector('#resume-text').value.includes('NEW CONTENT'), 'replacement file');
    replaceRelease(new TextEncoder().encode('OLD CONTENT').buffer); await sleep(80);
    assert(d.querySelector('#resume-text').value === 'NEW CONTENT Python', 'old file replaced newer file');
    say('PASS clearing/replacing files prevents stale parsing results');
    assert(w.modelRequests === 2, 'model should load once after successful retry');
    assert(w.testRequests.every(request => request.method === 'GET' && request.body === null && !/^https?:\/\//.test(request.url)), 'unexpected network request or text transmission');
    assert(w.localStorage.length === 0, 'unexpected localStorage persistence');
    assert(w.testErrors.length === 0, w.testErrors.join('\n'));
    say('PASS model reused; no document POSTs/external fetches/persistence or uncaught browser errors');
    frame.width = '390'; await sleep(100);
    assert(d.documentElement.scrollWidth <= d.documentElement.clientWidth, 'horizontal overflow at 390px');
    say('PASS mobile 390px layout has no horizontal overflow');
    frame.width = '1120'; await sleep(100);
    assert(d.documentElement.scrollWidth <= d.documentElement.clientWidth, 'desktop overflow');
    button('Load example').click(); await sleep(50); button('Analyze resume').click();
    await waitFor(() => d.querySelector('#results-title'), 'final results');
    say('ALL 12 CHECK GROUPS PASSED. Inspect desktop/mobile appearance using the controls above.');
  } catch (error) {say(`FAIL: ${error.message}`); console.error(error);}
};
