# Resume Skill Gap Analyzer frontend

A local React + JavaScript application using Vite and CSS. The existing frozen browser inference module is unchanged. No backend, account, analytics, external fonts or document persistence is included.

## Start locally

Use Node 24 or newer. From PowerShell:

```powershell
cd D:\Downloads\depi_gapAnalyzer\frontend
npm run dev
```

Open the URL printed by Vite, normally `http://127.0.0.1:5173/`. Dependencies are already installed in this workspace. On a fresh checkout, first run `npm ci`; keep `package-lock.json`.

```powershell
npm run build
npm test
npm run preview -- --port 4173
```

The tests include checks of production files, so run the build first. Preview serves the production build locally; it does not deploy anything. `base: './'` makes build asset paths relative. Model loading uses `import.meta.env.BASE_URL`, including when a repository-prefixed base is configured.

## Files and behavior

- `src/App.jsx` coordinates independent model, parsing and analysis states.
- `src/components/` contains the focused input, result, skill-list and suggestion components.
- `src/parsing/documents.js` validates uploads and extracts plain text locally.
- `src/model.js` loads and reuses the existing inference engine, resetting a failed load so users can retry.
- `src/inference/milestone3.mjs` is the unchanged verified Milestone 3 inference module.
- `public/models/milestone3/v1/assets.json` is a byte-identical, hash-verified copy of the public export. No other model artifacts are copied.

TXT accepts UTF-8 and BOM-marked UTF-16. DOCX uses Mammoth's plain-text extraction, never HTML rendering. Selectable-text PDF parsing uses PDF.js and a locally bundled worker. Uploads are limited to 10 MiB (10 × 1024 × 1024 bytes), labeled 10 MB in the interface. Scanned PDFs need OCR outside this app; unreadable or protected documents offer a pasted-text fallback. Extracted text remains editable. Complex layouts, unusual encodings and reading order can require manual correction.

Only static application/model assets are requested by application code. Resume and job texts stay in React/browser memory; there are no document POSTs, localStorage writes or external AI services. This architecture was inspected in source. Actual browser network observation remains pending.

## Verification limits

The production build and seven Node/React server-rendering checks passed. They do not establish actual browser execution. Computer Use stopped before opening the app because it could not confidently determine Chrome's current URL for policy enforcement.

Actual desktop/mobile visual checks, PDF/DOCX uploads, interactive result invalidation and stale-file races still need browser execution. A local, synthetic-only check page is prepared at `http://127.0.0.1:5173/tests/browser.html`. Open it with the dev server running and select **Run browser checks** once. It deliberately fails the fixture's first model load to exercise retry, then checks the example, empty inputs, unavailable coverage, file parsing, size validation, stale reads and mobile overflow. The fixture and synthetic documents are outside `public/` and excluded from the production build. This test page has not been run in a browser yet.

See `reports/frontend/milestone4_implementation_v1.md` for measured checks and remaining work. Nothing has been deployed.
