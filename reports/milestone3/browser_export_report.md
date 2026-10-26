# Browser export and Python–JavaScript parity

The frozen Logistic Regression from `models/milestone3/v2/logistic_regression.joblib` is exported in `models/browser/v1/assets.json`. It retains StandardScaler, balanced Logistic Regression with C=10, the four saved features and threshold 0.5. No training, refitting, tuning, test evaluation or split changes were performed.

## Export contents

The public inference file, `assets.json`, is 112,299 bytes. It contains coefficients, intercept, classes and positive-class identity, threshold, feature order, saved scaler statistics, vocabulary indices, IDF values, actual TF-IDF settings, dictionary, aliases and Python Unicode behavior tables. The companion `completed.json` is 3,286 bytes and records export integrity and source provenance. The export folder totals 115,585 bytes; browsers need only `assets.json`.

Strict JSON serialization rejects NaN and Infinity. No source documents, pair IDs, label rows, annotation rationales or joblib files are included. Source file paths and hashes identify provenance without copying source contents.

## Verification

Python 3.12.10 and Node v24.11.0 were used. References came through the verified frozen-model loader with fitting methods disabled. Real validation documents passed directly from Python to Node in process memory; no private reference files were written. The report contains aggregate measurements only.

We checked 23 text cases: ten existing validation pairs and thirteen synthetic cases. Twenty-one valid pairs were analyzed; two empty-input pairs were rejected with matching validation messages. Three synthetic feature vectors covered the region around decision value zero. The exact score 0.5 was also checked through the same classification comparison and classified Suitable; a lower score classified Unsuitable. No intermediate values were rounded.

| Comparison | Maximum absolute difference |
| --- | ---: |
| TF-IDF vector values | 0 |
| Unscaled features | 1.1102230246251565e-16 |
| Scaled features | 1.7763568394002505e-15 |
| Decision values | 7.105427357601002e-15 |
| Classifier scores | 3.885780586188048e-16 |

The acceptance rule was absolute difference <= 1e-8 + 1e-7 × absolute Python reference value. All comparisons passed. Classifications agreed exactly for 24/24 valid text/boundary cases. Extracted, matched and missing skill lists agreed exactly for 21/21 text cases. Conditional suggestions and feedback structure agreed, including null displayed coverage when no job skills were extracted. Internal coverage, missing count and no-evidence indicator remain 0, 0 and 1.

Checks covered aliases, C/C++/C#, Java/JavaScript, .NET and Node.js, mixed case, repeated terms and whitespace, casefold expansions, dotless i, non-Latin letters, Unicode numbers, combining marks, unknown vocabulary and zero vectors. We compared token lists, normalized text, sparse TF-IDF vectors, features, scaled values, decisions and scores. The asset loader was checked with a repository-prefixed URL. Aggregate measurements and implementation hashes are in `browser_parity_v2.json`.

## Commands

From the project root, the available embedded Python runtime needs the current directory added to its import path:

```powershell
& 'D:\Downloads\NHA-5-189\.runtime\python\python.exe' -c "import sys,os,runpy;sys.path.insert(0,os.getcwd());runpy.run_module('src.milestone3_export',run_name='__main__')"
node tests/verify_browser_parity.mjs 'D:\Downloads\depi_gapAnalyzer' 'D:\Downloads\NHA-5-189\.runtime\python\python.exe' v1
```

With a conventional project interpreter, use `python -m src.milestone3_export --root .`. Export requires an explicit command or function call. Compatible existing outputs are hash-verified and reused; different exports receive new numbered folders. The verifier never changes the model to improve agreement.

## Later React integration

There was no frontend application to extend. Only `frontend/src/inference/milestone3.mjs` was created; it has no Node imports. Node filesystem and process access stay in `tests/verify_browser_parity.mjs`.

There is no `frontend/public/` folder yet. Later, copy only the verified `assets.json` into a versioned public model folder such as `frontend/public/models/milestone3/v1/`. Keep reference documents and Python artifacts out of it. A future caller can use:

```javascript
import {loadBrowserAssets} from './inference/milestone3.mjs';
const engine = await loadBrowserAssets('/repository-name/models/milestone3/v1/');
const result = engine.analyze(resumeText, jobText);
```

Use the actual hosting base path; the helper does not assume domain-root deployment. For already loaded JSON, use `createInference(assets)`. Diagnostics contain verification intermediates and can be omitted from UI display. No React application or deployment was created.

## Scope and limits

The implementation uses exported Python casefold mappings, whitespace code points and word-character ranges instead of assuming JavaScript lowercasing and regex boundaries are equivalent. It preserves punctuation and performs no NFC/NFKC normalization, just as Python does. Skill extraction preserves the original longest-alternative behavior and its dictionary-matching limitations.

Inputs must be strings. Byte buffers and unpaired UTF-16 surrogates are unsupported and rejected. Modern ES modules, Unicode regex code-point escapes, lookbehind, fetch and Object.hasOwn are required. Node verification passed; browser-engine execution and legacy-browser compatibility have not been tested. The saved analyzer is supported; changes to tokenization, n-grams, weighting or normalization require a reviewed schema/implementation update.

Small floating-point differences remain possible, especially arbitrarily close to the threshold. A mathematically centered feature vector can produce a score a few floating-point units from 0.5; the verifier compares that result with Python rather than assuming it is exactly 0.5. The direct threshold check confirms the >= convention.

A classifier score is not a hiring probability. “Not found in your resume” does not establish that the candidate lacks a skill. Suggestions remain conditional and do not invent experience. Original data limitations remain: 46 automated annotations and three recorded first-review decisions, without independent human verification, only 49 development pairs and a small imbalanced held-out test. This export does not improve or re-estimate model quality. React UI and deployment remain outside this batch.
