# Milestone 4: local React application

The browser-only application is implemented in `frontend/`. The existing inference module, Python source, datasets, split assignments, saved models and historical reports are preserved. No training, tuning, deployment, commit or push was performed.

## What changed

Missing React/Vite project files were added around the existing inference module; the folder was not replaced by a generated template. The site uses a navy header, light input/result cards, responsive CSS, local SVG icons, keyboard focus states, labels and live status messages. The title is Resume Skill Gap Analyzer.

Users can paste a resume or choose a TXT, DOCX or selectable-text PDF up to 10 MiB. Filename, parsing status and editable extracted text are shown. The job description has a separate textarea and character count. Load example uses synthetic content only. Clear all and clear/replace-resume controls invalidate previous results and pending file reads.

Results keep the experimental model assessment, job-skill coverage and TF-IDF similarity separate. No classifier score, overall match percentage, diagnostics, token vectors or source hashes appear in the normal interface. Null coverage is rendered as Unavailable. Skill lists and conditional suggestions come from the existing engine. Expandable lists show extracted skills. Empty gap lists are not described as proof that every job requirement is met.

Model loading, parsing and analysis have independent states. The engine is loaded once and reused; a failed fetch clears its cached promise so Retry loading can succeed. A version counter prevents older file-reading operations from replacing cleared, edited or newer resume inputs. Another input version invalidates analyses when text changes.

## Dependencies and asset integrity

Node v24.11.0 and npm 11.6.1 were available. The new frontend dependencies were installed through npm, with exact versions and a retained lockfile: React/React DOM 19.3.1, Vite 8.3.5, React plugin 6.1.2, PDF.js (`pdfjs-dist`) 6.4.299 and Mammoth 1.13.0. No Python packages or unrelated project dependencies were upgraded. npm reported zero vulnerabilities during installation; this is an installation-time result, not a guarantee about future advisories.

The export's recorded SHA256 was verified before copying only `assets.json` to `frontend/public/models/milestone3/v1/assets.json`. Public and production copies match:

`d406bd9d8dadc8ebed53a767b93ee0fce6bf991b960a49b87e1798a40a9fbc6a`

The saved threshold remains 0.5 and the feature/extraction behavior is unchanged. `import.meta.env.BASE_URL` controls the model path. PDF.js's worker is included in the local build, not loaded from a CDN. PDF/DOCX modules are loaded only when needed.

Mammoth is used through [its documented plain-text browser API](https://github.com/mwilliamson/mammoth.js#api), without rendering untrusted document HTML. [Vite's documented Node requirements](https://vite.dev/guide/) are met by the installed runtime. Versions were checked against the official npm registry before installation.

## Commands

From PowerShell:

```powershell
cd D:\Downloads\depi_gapAnalyzer\frontend
npm run dev
```

Open the local URL printed by Vite, normally `http://127.0.0.1:5173/`. For a fresh checkout, run `npm ci` first. Build and verify with:

```powershell
npm run build
npm test
npm run preview -- --port 4173
```

`npm run preview` is local-only. No deployment configuration or hosting service was added.

## Checks actually performed

The production build passed with Vite 8.3.5. It emitted the app bundle, CSS, lazy PDF/DOCX chunks and a local PDF worker. The main JavaScript bundle is about 245.5 kB before gzip; PDF parsing brings an additional worker of about 1.26 MB. No external CDN is needed.

Seven focused Node/server-rendering checks passed:

| Check | Result |
| --- | --- |
| Public model bytes and recorded export hash | Passed |
| TXT extraction, empty/unsupported/type-mismatch/oversize validation and fallback messages | Passed |
| Synthetic inference, exact recognized skill lists and null-coverage behavior | Passed |
| React results render Unavailable and exclude internal model values | Passed through server rendering |
| Model promise sharing, simulated failure and successful retry | Passed through the Vite-loaded module |
| Public/build allowlist and production model hash | Passed |
| Production HTML, JS/CSS chunks, model and PDF worker served under `/repository/` | Passed via local HTTP checks |

The public directory contains only the intended model JSON and favicon. The production allowlist contains only HTML, the favicon, model JSON and generated JS/CSS/worker assets. Synthetic upload fixtures and browser test code are excluded. No real resumes, job descriptions, private reference cases, raw CSVs or joblib files were copied into public/build folders.

Source inspection confirmed no analytics, remote fonts, external AI APIs, document-content persistence or application requests transmitting resume/job text. The only application fetch loads static model JSON; parsing receives in-memory file bytes. Actual browser-network inspection has not occurred.

## Browser checks pending

Computer Use was available, but it stopped before opening the application because it could not determine Chrome's current URL with enough confidence to enforce policy. The restriction was not bypassed. Therefore **no actual browser interaction, console/network inspection, desktop/mobile screenshot review, supported upload-format run or browser-versus-Python result comparison is claimed**.

A synthetic-only browser check page is prepared at `/tests/browser.html` on the Vite dev server. It exercises initial model failure/retry, empty inputs, example/inference agreement, null coverage, editing/result invalidation, TXT/DOCX/PDF extraction, broken-file fallback, the upload limit, clearing/replacement races, model reuse and mobile overflow. It deliberately simulates failure only in the test fixture; normal application loading is unchanged. This page is not included in production builds and has not yet been executed in a browser.

Manual follow-up should inspect the normal app at desktop and mobile sizes, test keyboard navigation, run the prepared checks, review PDF/DOCX reading order and encrypted/scanned-PDF messages, inspect console/network errors, and compare rendered synthetic results with Python references. Node checks do not prove these browser behaviors.

## Status and limitations

Milestone 4 implementation tasks are complete for the local React workspace, frozen-model wiring, parser integration, result/feedback presentation, privacy-oriented data flow, error-state handling and production build. Actual browser and accessibility/visual acceptance remain pending. The site has not been deployed.

The model is experimental: 49 development pairs include 46 automated labels and three recorded first-review decisions without independent human verification. Only ten test pairs were evaluated previously. Results measure agreement with annotations, not verified hiring suitability. Skill extraction uses a fixed dictionary; absent text evidence does not establish a missing ability. The website does not assess grammar, layout or writing quality. Complex or scanned documents may need pasted text or external OCR.
