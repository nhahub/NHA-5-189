// Browser-only inference. Assets and text are supplied by the caller.
const escapeRegex = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const codePointCompare = (a, b) => {
  const x = Array.from(a, c => c.codePointAt(0)), y = Array.from(b, c => c.codePointAt(0));
  for (let i = 0; i < Math.min(x.length, y.length); i++) if (x[i] !== y[i]) return x[i] - y[i];
  return x.length - y.length;
};
const sorted = values => [...values].sort(codePointCompare);
const unicodeEscape = number => `\\u{${number.toString(16)}}`;

export function createInference(assets) {
  const order = ['tfidf_cosine', 'job_skill_coverage', 'missing_job_skill_count', 'no_job_skills'];
  const settings = assets.tfidf.settings;
  if (assets.schema_version !== 1 || JSON.stringify(assets.feature_order) !== JSON.stringify(order)
      || assets.classifier.type !== 'LogisticRegression' || assets.threshold !== 0.5
      || JSON.stringify(assets.classifier.classes) !== '[0,1]' || assets.classifier.positive_class !== 1
      || assets.classifier.positive_class_index !== 1 || settings.norm !== 'l2'
      || settings.binary || settings.sublinear_tf || !settings.use_idf || settings.lowercase
      || settings.analyzer !== 'word' || JSON.stringify(settings.ngram_range) !== '[1,1]') {
    throw new Error('Unsupported browser model schema, classes, feature order or analyzer settings.');
  }
  const behavior = assets.text_behavior;
  const whitespace = new Set(behavior.whitespace_codepoints);
  const word = `[${behavior.word_ranges.map(([a, b]) => a === b ? unicodeEscape(a) : `${unicodeEscape(a)}-${unicodeEscape(b)}`).join('')}]`;
  const wordPlusPunctuation = word.slice(0, -1) + '.+#]';
  const wordPlusSuffix = word.slice(0, -1) + '+#]';
  const tokenPattern = new RegExp(`(?<!${word})(?:\\.net(?!${word})|${word}+(?:[+#]+|(?:\\.${word}+)*))`, 'gu');
  const aliases = assets.dictionary.aliases;
  const terms = [...new Set([...assets.dictionary.skills, ...Object.keys(aliases)])];
  terms.sort((a, b) => Array.from(b).length - Array.from(a).length || codePointCompare(a, b));
  // After full casefold, dotless i is the remaining special IGNORECASE variant.
  const alternatives = terms.map(term => escapeRegex(term).replace(/[i\u0131]/g, '[i\u0131]')).join('|');
  const skillPattern = new RegExp(`(?<!${wordPlusPunctuation})(?:${alternatives})(?!${wordPlusSuffix}|\\.${word})`, 'gu');

  function normalize(text) {
    if (typeof text !== 'string') throw new Error('Text must be a string.');
    let folded = '';
    for (const char of text) {
      const point = char.codePointAt(0);
      if (point >= 0xd800 && point <= 0xdfff) throw new Error('Unpaired UTF-16 surrogates are unsupported.');
      folded += behavior.casefold[char] ?? char;
    }
    let result = '', pendingSpace = false;
    for (const char of folded) {
      if (whitespace.has(char.codePointAt(0))) { pendingSpace = result.length > 0; continue; }
      if (pendingSpace) result += ' ';
      result += char; pendingSpace = false;
    }
    return result;
  }

  function tokenize(text) {
    return [...normalize(text).matchAll(tokenPattern)].map(match => match[0]);
  }

  function extract(text) {
    return new Set([...normalize(text).matchAll(skillPattern)].map(match => {
      const value = normalize(match[0]);
      return aliases[value] ?? value;
    }));
  }

  function vector(text) {
    const frequencies = new Map();
    for (const token of tokenize(text)) {
      const index = Object.hasOwn(assets.tfidf.vocabulary, token) ? assets.tfidf.vocabulary[token] : undefined;
      if (index !== undefined) frequencies.set(index, (frequencies.get(index) ?? 0) + 1);
    }
    const values = [...frequencies].sort((a, b) => a[0] - b[0]).map(([index, count]) => [index, count * assets.tfidf.idf[index]]);
    const norm = Math.sqrt(values.reduce((sum, [, value]) => sum + value * value, 0));
    return Object.fromEntries(values.map(([index, value]) => [index, norm ? value / norm : 0]));
  }

  function scoreFeatures(features) {
    if (features.length !== order.length || !features.every(Number.isFinite)) throw new Error('Four finite feature values are required.');
    const scaler = assets.scaler;
    const scaled = features.map((value, index) => (value - (scaler.with_mean ? scaler.mean[index] : 0)) / (scaler.with_std ? scaler.scale[index] : 1));
    const decision = scaled.reduce((sum, value, index) => sum + value * assets.classifier.coefficients[0][index], 0) + assets.classifier.intercept[0];
    const score = decision >= 0 ? 1 / (1 + Math.exp(-decision)) : Math.exp(decision) / (1 + Math.exp(decision));
    return {scaled, decision, score, suitable: classifyScore(score)};
  }

  const classifyScore = score => score >= assets.threshold;

  function analyze(resumeText, jobText) {
    for (const [name, text] of [['Resume', resumeText], ['Job description', jobText]]) {
      if (typeof text !== 'string' || !normalize(text)) throw new Error(`${name} text must be a nonempty string.`);
    }
    const resume = extract(resumeText), job = extract(jobText);
    const matched = sorted([...job].filter(skill => resume.has(skill)));
    const missing = sorted([...job].filter(skill => !resume.has(skill)));
    const resumeVector = vector(resumeText), jobVector = vector(jobText);
    const similarity = Object.entries(resumeVector).reduce((sum, [index, value]) => sum + value * (jobVector[index] ?? 0), 0);
    const coverage = job.size ? matched.length / job.size : 0;
    const features = [similarity, coverage, missing.length, Number(job.size === 0)];
    const scored = scoreFeatures(features);
    return {
      resume_skills: sorted(resume), job_skills: sorted(job), matched_skills: matched, job_skills_not_found: missing,
      job_skill_coverage: job.size ? coverage : null,
      coverage_scale: '0–1; null means insufficient extracted job-skill evidence',
      tfidf_text_similarity: similarity,
      model_classification: scored.suitable ? 'Suitable Match' : 'Unsuitable Match',
      classifier_score: scored.score, classification_threshold: assets.threshold,
      score_note: 'A classifier score is not a hiring probability. Classification, skill coverage and text similarity are separate outputs.',
      skill_evidence_note: job.size ? 'These are mentioned skills, not necessarily essential requirements. A skill not found in your resume may still be one you have.' : 'Insufficient extracted skill evidence in the job description; this is not a confirmed mismatch.',
      suggestions: missing.map(skill => ({skill, guidance: `${skill} appears in the job description but was not found in your resume. If you have used ${skill}, add truthful evidence such as a relevant project or responsibility. If you have not used ${skill}, consider learning and practicing it.`})),
      model_features: Object.fromEntries(order.map((name, i) => [name, features[i]])),
      diagnostics: {scaled: scored.scaled, decision: scored.decision, normalized: [normalize(resumeText), normalize(jobText)],
        tokens: [tokenize(resumeText), tokenize(jobText)], vectors: [resumeVector, jobVector]},
    };
  }
  return {analyze, normalize, tokenize, extract, vector, scoreFeatures, classifyScore};
}

export async function loadBrowserAssets(baseUrl, {fetchImpl = globalThis.fetch} = {}) {
  const base = String(baseUrl).replace(/\/?$/, '/');
  const response = await fetchImpl(`${base}assets.json`);
  if (!response.ok) throw new Error(`Could not load model assets: HTTP ${response.status}`);
  return createInference(await response.json());
}
