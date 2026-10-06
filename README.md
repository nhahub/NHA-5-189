# DEPI Gap Analyzer

Graduation project for extracting skills from resumes and comparing them with job
descriptions to identify matched and missing skills. Milestones 1 and 2 contain
the original preprocessing, EDA, skill extraction, TF-IDF and evaluation work.

## Project structure

```text
depi_gapAnalyzer/
├── README.md
├── requirements.txt
├── .gitignore
├── Dockerfile
├── notebooks/
│   ├── 01_data_preprocessing_and_eda.ipynb
│   ├── 02_skill_extraction_and_similarity.ipynb
│   └── 03_embeddings_and_model_comparison.ipynb
├── src/
│   ├── preprocessing.py
│   ├── skill_extraction.py
│   ├── similarity.py
│   ├── embeddings.py
│   ├── evaluation.py
│   └── pipeline.py
├── api/
│   └── main.py
└── data/
    ├── raw/
    │   └── jobs.csv
    ├── processed/
    │   ├── final_cleaned_cv.csv
    │   └── final_cleaned_jobs.csv
    └── sample/
        ├── small_cv.csv
        ├── small_jobs.csv
        └── small_matches.csv
```

## Responsibilities

| File | Purpose |
| --- | --- |
| Notebook 01 | Loads sample data, checks quality, preprocesses text, saves processed CSVs and shows EDA. |
| Notebook 02 | Loads processed CSVs, restores skill lists, then runs the original extraction, similarity, optimization and evaluation cells. |
| Notebook 03 | Markdown placeholder for embeddings and model comparison in Milestone 3. |
| `src/preprocessing.py` | Document parsing, section extraction, text cleaning and NLP setup functions. |
| `src/skill_extraction.py` | Functions for dictionary construction, both EntityRuler setup stages and skill extraction. |
| `src/similarity.py` | Functions for skill comparison, filtering and percentages; provides the TF-IDF tools used by the pipeline. |
| `src/evaluation.py` | Callable precision, recall, F1 and comparison calculations. |
| `src/pipeline.py` | The original `analyze_match` body with explicit data and extractor arguments; prints and return value are unchanged. |
| `src/embeddings.py` | Docstring placeholder for Milestone 3. |
| `api/main.py` | Docstring placeholder for FastAPI in Milestone 3. |
| `Dockerfile` | Comment-only placeholder for cloud deployment; not yet buildable. |
| `requirements.txt` | Packages used by the existing notebooks and Jupyter environment. |
| `.gitignore` | Excludes environments, caches and local settings from Git. |

Both active notebooks have one import cell, large numbered section headings and
a descriptive label before every code cell. Notebook 01 completes preprocessing
before EDA and visualization. Notebook 02 calls imported functions for extraction,
comparison and evaluation. Function implementations live only in `src/`.

The modules accept their dependencies as arguments and do not load datasets,
download NLTK resources or evaluate models on import. The notebooks use `partial`
to attach shared inputs while retaining familiar calls such as
`extract_skills(text)` and `analyze_match(3, 3)`. Original calculations, filters,
printed metrics and chart settings are preserved. Repeated superseded function
definitions have been consolidated into their effective implementation; their
original versions remain in Git. Outputs were cleared because the cell layout
and calls changed, and the notebooks have not been rerun.

## Python environment setup

Use Python 3.11 or newer. The virtual environment is stored in `.venv`; it is
local to your computer and intentionally excluded from Git.

### Linux and macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows Command Prompt

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

After activation, open either active notebook from the project root:

```bash
jupyter lab notebooks/01_data_preprocessing_and_eda.ipynb
```

```bash
jupyter lab notebooks/02_skill_extraction_and_similarity.ipynb
```

The future milestone notebook can be opened with:

```bash
jupyter lab notebooks/03_embeddings_and_model_comparison.ipynb
```

Notebook kernels should run with `notebooks/` as their working directory so the
existing relative-path style (`../data/...`) resolves correctly. If using an
editor instead of Jupyter, set its notebook working directory accordingly.

Notebook 01 still contains the original NLTK resource downloads and CSV writes.
Running it can download resources and overwrite the two processed CSVs. Notebook
02 uses those CSVs and copies the original skill-list conversion cells into its
setup, so it does not require Notebook 01's in-memory variables. Install packages
with `requirements.txt` before execution; `%pip install` lines were removed from
the notebooks. PDF and DOCX support uses the original `PyPDF2` and `python-docx`.

To leave the environment on any operating system, run `deactivate`.

If your editor asks you to choose a Python interpreter or notebook kernel,
select the one inside `.venv`.

## Data and preservation notes

- `data/raw/jobs.csv` is the original `data/job.csv`, renamed without changing its contents.
- `data/processed/` keeps the `final_cleaned_*.csv` filenames from the requested tree.
- `data/sample/` contains the three original small datasets.
- Original full `cv.csv` and `matches.csv` were not present; no substitutes were created.
- The original helper scripts are preserved verbatim in the reference appendix below.
- The original notebook and helper scripts are preserved in Git commit
  `66c9d4776e46660307f933c9168cc98be355c670`. For example, inspect the original with
  `git show 66c9d4776e46660307f933c9168cc98be355c670:src/resume_skill_gap.ipynb`.
- The original preprocessing documentation and EDA findings remain in Notebook 01.
  Fixed printed baseline metrics are retained. Function bodies keep their original
  calculations, with data dependencies passed as arguments. Notebook outputs were
  cleared during the readability update; original outputs remain in Git.

Embeddings, the API and Docker deployment are planned for later milestones.
There is no frontend in this structure.

## Historical helper scripts

These are reference copies with their original paths, not current execution instructions.

<details>
<summary>check_data.py</summary>

```python
import pandas as pd

cv = pd.read_csv("data/cv.csv")
jobs = pd.read_csv("data/job.csv")
matches = pd.read_csv("data/matches.csv")

print("CV shape:", cv.shape)
print("Jobs shape:", jobs.shape)
print("Matches shape:", matches.shape)

print("\nCV columns:")
print(cv.columns.tolist())

print("\nJob columns:")
print(jobs.columns.tolist())

print("\nMatches columns:")
print(matches.columns.tolist())
```

</details>

<details>
<summary>inspect_text.py</summary>

```python
import pandas as pd

cv = pd.read_csv("data/small_cv.csv")
jobs = pd.read_csv("data/small_jobs.csv")

print("----- RESUME -----")
print(cv.loc[0, "resume_text"])

print("\n----- JOB DESCRIPTION -----")
print(jobs.loc[0, "job_description"])
```

</details>

<details>
<summary>make_small_dataset.py</summary>

```python
import pandas as pd

cv = pd.read_csv("data/cv.csv")
jobs = pd.read_csv("data/job.csv")
matches = pd.read_csv("data/matches.csv")

# Take a small sample
small_cv = cv.head(30)
small_jobs = jobs.head(10)

# Keep only matches related to those selected CVs and jobs
small_matches = matches[
    matches["candidate_id"].isin(small_cv["candidate_id"]) &
    matches["job_id"].isin(small_jobs["job_id"])
]

# Save them as new files
small_cv.to_csv("data/small_cv.csv", index=False)
small_jobs.to_csv("data/small_jobs.csv", index=False)
small_matches.to_csv("data/small_matches.csv", index=False)

print("Small dataset created successfully.")
print("CVs:", small_cv.shape)
print("Jobs:", small_jobs.shape)
print("Matches:", small_matches.shape)
```

</details>
