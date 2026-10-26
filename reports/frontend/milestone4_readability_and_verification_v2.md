# Milestone 4: readability and feedback cleanup

The navy design and existing application behavior are preserved. This batch improves reading sizes, contrast and the presentation of skill-specific suggestions. It does not change the inference engine, dictionary, model assets, skill counts, coverage denominator or classification.

## Changes

`frontend/src/styles.css` now uses 16px body/input text and at least 14px secondary text and skill badges. Suggestion paragraphs use 16px text with comfortable line spacing, larger numbered markers and more space between items. Muted text on white is darker; secondary copy on navy is lighter. Mobile result cards stack so long values such as Unavailable have room. Upload controls, helper text and the header can wrap. Programmatically focused results also retain a visible keyboard focus style.

`frontend/src/feedbackGuidance.js` provides a small UI-only mapping for Node.js, SQL, testing, Python, JavaScript and Git. Unknown skills use a conditional generic fallback. `ImprovementSuggestions.jsx` displays a short “not found in your resume” context line followed by the advice, instead of repeating the engine's longer paragraph. The engine's returned data is neither modified nor filtered. Generic terms such as project remain visible and count toward the same lists as before.

For example, SQL guidance asks users who have used it to describe querying or analyzing data; otherwise it suggests practicing filtering, joins and aggregations. Node.js guidance refers conditionally to an API/application or a small practice project. No experience, qualifications, metrics or essential requirements are inferred from the gap list.

Backups of modified files are under `reports/frontend/archive/`:

- `styles_pre_readability_v1.css`
- `ImprovementSuggestions_pre_readability_v1.jsx`
- `interface.test_pre_readability_v1.mjs`
- `browser-checks_pre_readability_v1.js`

Earlier reports remain unchanged.

## Commands and runtimes

Node v24.11.0, npm 11.6.1, React 19.3.1 and Vite 8.3.5 were used. No new dependencies were installed in this batch. From PowerShell:

```powershell
cd D:\Downloads\depi_gapAnalyzer\frontend
npm.cmd run build
npm.cmd test
npm.cmd run dev -- --port 5174 --strictPort
```

Port 5173 was already occupied, so this batch started a separate instance. Vite printed the exact local address `http://127.0.0.1:5174/`. The attempted browser target was that same address. The prepared check page is `http://127.0.0.1:5174/tests/browser.html` while the dev server is running. Nothing was deployed.

## Checks actually run

The production build passed. All ten focused Node/server-rendering tests passed:

| Check | Result |
| --- | --- |
| Public model bytes match the recorded export hash | Passed |
| Synthetic TXT extraction and file type/size/empty validation | Passed in Node |
| Synthetic inference and null skill-coverage behavior | Passed in Node |
| React result markup shows Unavailable and excludes model internals | Passed through server rendering |
| Cached model promise, failure and retry | Passed through Vite's module loader in Node |
| Conditional mapped/fallback suggestions, including visible project gap | Passed through server rendering |
| Suggestion rendering leaves engine results and list counts unchanged | Passed |
| Explicit font sizes at least 14px, inputs/suggestions 16px; selected secondary colors meet 4.5:1 contrast | Passed by source/color checks |
| Production/public allowlist and repository-prefixed HTML, chunks, worker and model requests | Passed through local HTTP checks |
| Synthetic DOCX plain-text extraction through Mammoth's browser distribution | Passed in Node |

The prepared browser test script also passed `node --check`. These checks do not establish actual browser rendering or interaction. Font declarations and color calculations are not a substitute for visual review at normal zoom.

One synthetic TXT fixture and one synthetic DOCX fixture were successfully extracted in Node. No browser parsing success count or end-to-end processing time is reported, because neither was measured in a browser. PDF parsing was not executed in this batch.

## Browser access and pending checks

The supported browser tool returned **“Browser is not available: chrome”** when asked to open `http://127.0.0.1:5174/`. No browser state, page, console, network trace or screenshot was obtained. The earlier native Windows URL-confidence restriction was not bypassed. Browser version could not be measured in this batch.

**No actual browser checks are marked passed.** The following still need browser access:

- Normal-zoom desktop/mobile appearance, computed typography, clipping and horizontal overflow.
- Physical keyboard navigation, labels, focus visibility and announced status messages.
- Load example and Analyze, rendered results against the engine and the three synthetic Python references.
- Separate coverage/similarity outputs, Unavailable coverage, input edits invalidating results and Clear all.
- Actual model-load failure/retry and model reuse in the browser.
- TXT, DOCX and selectable-text PDF uploads and editing of extracted text.
- Empty, broken, unsupported, oversized, image-only/scanned and encrypted document handling.
- Clearing/replacing a file while reading and editing the resume during extraction.
- Model/worker requests staying local, no external transmission of document contents, and browser console/network errors.

The prepared `/tests/browser.html` page was expanded to cover three synthetic Python references, both input edits, visible labels/live status, font sizes, empty/unsupported files and the encrypted/image-only PDF fallbacks. It retains retry, ordinary uploads, stale-file, model reuse and mobile-overflow checks. A parsing-status wait now also checks the current filename so an earlier document's status cannot satisfy a later file's check.

New synthetic-only supporting files are outside public/build folders:

- `frontend/tests/fixtures/encrypted-synthetic.pdf`
- `frontend/tests/fixtures/image-only-synthetic.pdf`
- `frontend/tests/fixtures/synthetic-python-references.json`

The encrypted fixture uses a synthetic test password, not user credentials. The image-only fixture contains a raster image without selectable text and exercises the scanned-document fallback; it is not an OCR test. Python references were generated with fitting disabled and contain only invented texts. Preparing fixtures does not count as running their browser checks.

**Screenshots: none captured.** No screenshot files or paths are claimed.

## Preservation and task status

The public model JSON and verified inference module remain byte-for-byte unchanged. The integrity check compares preexisting data, model, split, Python, notebook, frontend and report files against the pre-edit snapshot. Only the intended CSS, suggestion component and focused test files changed. Historical reports and Milestones 1–3 remain untouched.

The following implementation tasks can be marked Finished: readability styling, stronger secondary contrast, UI-specific conditional guidance with a fallback, preservation of all recognized skill results, expanded synthetic verification fixtures, and production-build/non-browser regression checks.

Actual browser functional verification, supported-format browser acceptance, normal-zoom desktop/mobile visual review, keyboard/accessibility acceptance, browser privacy/network review and screenshots remain pending. Do not mark those tasks or all of Milestone 4 Finished.

The existing model limitations still apply: 49 development pairs, including 46 automated annotations and three recorded first-review decisions without independent human verification. This UI cleanup does not improve measured model quality, establish hiring suitability, or assess grammar or CV layout. There was no retraining, retuning, installation of unrelated packages, commit, push or deployment.
