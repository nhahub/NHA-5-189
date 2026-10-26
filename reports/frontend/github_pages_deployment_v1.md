# GitHub Pages deployment

The existing React website is deployed at **https://sadeentag.github.io/depi_gapAnalyzer/**.

- Repository: https://github.com/SadeenTag/depi_gapAnalyzer
- Branch and default branch: `main`
- Deployed commit: `b9cb8c7f3c5ed127c73f951cc4607e1c2379a901`
- Successful workflow: https://github.com/SadeenTag/depi_gapAnalyzer/actions/runs/40387560876
- Workflow result: build, deploy and verify-live all completed successfully.

## Configuration and release scope

The remote was inspected rather than inferred. GitHub reported no preexisting Pages site, custom domain or Actions workflows. Pages was configured to use GitHub Actions without changing repository visibility. No new repository or unrelated website was created or replaced.

The Vite default base is `/depi_gapAnalyzer/`. The workflow uses the base path returned by GitHub's configure-pages action, allowing an existing custom domain to be respected if one is configured later. Model loading, application chunks, document parsers, the PDF worker, favicon and Methodology link follow that base. The public Methodology page's return link is relative to its site directory.

`.github/workflows/pages.yml` uses pinned versions of GitHub's supported Pages actions, Node 24, `npm ci` in `frontend/`, a production build and frontend tests. Build and deploy permissions are separated; deployment uses `pages: write` and `id-token: write`. The github-pages concurrency group serializes releases. Pushes affecting frontend/workflow files on main and manual workflow dispatch are supported. Deployment jobs are restricted to main.

Only **frontend/dist** is uploaded as the Pages artifact. The production allowlist permits the main HTML, Methodology page, favicon, verified public model JSON and generated JavaScript/CSS/PDF-worker assets. Raw datasets, real resumes, private reference cases, Python source, joblib files, backups, node_modules and development browser test pages are excluded. CI checks out the frontend sparsely and does not fetch dataset LFS content.

The first release commit, `f7a22aa12d44211f99eb5aab3e2d28e196f4835b`, added the existing frontend and deployment configuration. The second commit added post-deployment verification. Neither commit includes unrelated datasets, notebooks, Python work, caches, generated backups or historical reports. Existing unrelated work remains in the working tree. Local source backups and credential-handling helper scripts were not committed. Credentials were read through Git Credential Manager in memory and were not printed or saved.

Frontend tests now use a small verified model-hash contract instead of requiring untracked root export files in CI. Binary attributes preserve synthetic PDF/DOCX fixture bytes. No model behavior, dictionary, feature calculation or threshold changed.

## Checks passed

The local production build and all **11 frontend tests** passed. Local HTTP tests served the build under the intended `/depi_gapAnalyzer/` prefix and checked application entry points, model loading, Methodology and document-parsing assets. Synthetic inference, null coverage, conditional UI copy, model retry/cache logic and TXT/DOCX behavior were tested in Node or server rendering; those are not browser interaction checks.

GitHub's runner independently performed a clean locked installation, production build and all frontend tests. The final verify-live job fetched the actual URL returned by the deploy action and confirmed:

| Live check | Result |
| --- | --- |
| Main page | HTTP 200 |
| Application JavaScript and CSS | HTTP 200 |
| Favicon | HTTP 200 |
| PDF and DOCX parsing chunks | HTTP 200 |
| Local PDF worker | HTTP 200 |
| Public model JSON | HTTP 200, 112,299 bytes, verified SHA256 |
| Methodology page | HTTP 200 |
| Three synthetic Python reference cases using downloaded model bytes | Passed in Node |
| Development browser-test page, source JSX, raw CSV and Python model URLs | HTTP 404 |

Public model SHA256:

`d406bd9d8dadc8ebed53a767b93ee0fce6bf991b960a49b87e1798a40a9fbc6a`

The exact public URLs, response sizes, exclusions and successful workflow identity are saved in `github_pages_live_verification_v1.json` beside this report. These are HTTP and Node checks from GitHub's runner. Direct requests to the Pages host from this Windows execution environment timed out, while GitHub API access worked; the successful runner checks provide the independent live-response evidence.

## Browser limitations

Actual browser interaction remains unverified because the available Chrome browser connector is unavailable. No screenshots, live upload interactions, mobile visual checks, physical keyboard tests or browser console/network observations are claimed. Browser synthetic analysis and supported TXT/DOCX/PDF uploads still need acceptance testing on the published site. Resolving static parser/worker URLs is not the same as running those parsers in a browser.

The model's existing experimental limitations and annotation provenance remain documented in the Methodology page and historical reports. Nothing was retrained, refitted or retuned for deployment.

## Files and commands

This release commits the existing frontend source, public assets, lockfile, focused tests and synthetic-only test fixtures, plus `.github/workflows/pages.yml`. Deployment-specific changes include `frontend/vite.config.js`, `frontend/tests/model-contract.json`, base-aware tests and browser fixtures, `frontend/.gitattributes`, `frontend/scripts/verify-live.mjs` and frontend startup documentation. The inference engine and public model bytes were preserved.

To build, test or preview locally:

```powershell
cd D:\Downloads\depi_gapAnalyzer\frontend
npm.cmd ci
npm.cmd run build
npm.cmd test
npm.cmd run preview -- --port 4173
```

Preview the repository path printed by Vite, using `/depi_gapAnalyzer/`. An intentional live HTTP recheck can be run from the frontend directory on a network that reaches GitHub Pages:

```powershell
node scripts/verify-live.mjs https://sadeentag.github.io/depi_gapAnalyzer/
```

The deployment configuration follows [GitHub's custom Pages workflow guidance](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) and [Vite's GitHub Pages instructions](https://vite.dev/guide/static-deploy#github-pages). The deployment is successful; actual browser acceptance is still pending.
