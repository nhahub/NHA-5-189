# AI-Based Resume Skill Gap Analyzer

**DEPI — AI & Data Science Track**

## Project Overview

We are building an NLP tool that compares a candidate's resume with a target job description, identifies matched and missing skills, and reports skill coverage and text similarity. The planned final application will let users upload a resume, paste a job description, and view the results through a web interface.

The current implementation runs in Jupyter notebooks and reusable Python modules. Data preprocessing and EDA are documented, and the skill-extraction and TF-IDF matching baseline has been implemented and evaluated. The web application, contextual embeddings, cloud deployment, and monitoring remain planned work.

This README documents the implemented workflow, project structure, evaluation results, known limitations, and future improvements. It also explains how to run the existing notebooks and validation script.

## Work Completed

### Data Collection, Preprocessing, and Exploration

We loaded the full [Job-Resume Matching Dataset](https://huggingface.co/datasets/nonameee12233/job-resume-matching) from the local CSV files:

| Dataset | Local file | Records | Raw columns |
|---|---|---:|---:|
| Resumes | `data/raw/cv.csv` | 9,544 | 11 |
| Job descriptions | `data/raw/job.csv` | 1,167 | 10 |
| Candidate–job matches | `data/raw/matches.csv` | 122,560 | 13 |

We inspected schemas, missing values, duplicates, text examples, and match references. The preprocessing pipeline extracts resume sections, lowercases text, removes URLs and unwanted characters, normalizes whitespace, tokenizes, removes English stopwords, and applies WordNet lemmatization. It saves the full processed resume and job datasets for the next notebook.

The EDA examines processed resume lengths, the top ten resume and required-job skills, job-category balance, the top five required skills per domain, and supplied match-score statistics.

**Key findings:**

- No missing values or exact duplicate rows were found in the three raw datasets.
- Processed resumes have a median length of 137 words and a mean of 145.58 words.
- Python and machine learning lead the supplied resume skill labels; adaptability leads the supplied required-job labels.
- The five job categories are nearly balanced, with 220–240 postings per category.
- Match records cover 9,532 candidates and 1,164 jobs, with no unknown candidate or job references. Twelve candidates and three jobs have no match records.

**Deliverables:** [Notebook 01](notebooks/01_data_preprocessing_and_eda.ipynb), [preprocessing module](src/preprocessing.py), [processed datasets](data/processed/), and the [complete EDA report](reports/Milestone_1_EDA_Report.md). The report includes the preprocessing documentation, original charts, findings, and limitations.

### Skill Extraction, Similarity, and Gap Analysis

We built a dictionary from the supplied resume and job skill lists and used spaCy's `EntityRuler` to recognize matching skill phrases. The initial dictionary contains 8,078 unique labels. Filtering 13 generic terms reduces it to 8,065 labels for the optimized extractor.

Implemented functionality includes:

- Extracting skills from cleaned resume and job text.
- Identifying matched skills by set intersection and missing skills by subtracting resume skills from job requirements.
- Calculating skill-match percentage as matched skills divided by extracted job skills, with zero returned when no job skills are extracted.
- Representing processed text with TF-IDF and calculating cosine similarity.
- Returning the resume position, job title, matched skills, missing skills, skill-match percentage, and text-similarity percentage through `analyze_match()`.
- Comparing baseline and filtered-dictionary extraction results against the supplied resume skill labels.

The notebook pipeline fits TF-IDF to each selected resume/job pair and reports skill coverage and text similarity separately. These percentages are descriptive matching scores, not probabilities of hiring success.

**Deliverables:** [Notebook 02](notebooks/02_skill_extraction_and_similarity.ipynb), [skill extraction](src/skill_extraction.py), [similarity functions](src/similarity.py), [analysis pipeline](src/pipeline.py), [evaluation functions](src/evaluation.py), and the [model evaluation report](reports/model_evaluation/MODEL_EVALUATION_REPORT.md).

## Evaluation Results

### Skill Extraction Across All Resumes

The saved Notebook 02 outputs report the following averages of per-resume precision, recall, and F1 across all 9,544 resumes:

| Metric | Baseline dictionary | Filtered dictionary |
|---|---:|---:|
| Precision | 0.56 | 0.57 |
| Recall | 0.97 | 0.96 |
| F1-score | 0.70 | 0.70 |

Filtering generic terms slightly improves precision while reducing recall; F1 remains unchanged at the displayed precision. High recall means many reference skills are found, but lower precision indicates false positives relative to the supplied labels.

The dictionary is built from the same loaded datasets used for evaluation. These are descriptive in-dataset results, not held-out generalization estimates, and the supplied labels have not been independently audited.

### Ranking Validation on a Candidate Subset

The separate [ranking validation script](src/ranking_validation.py) uses a shared TF-IDF vector space and a fixed weighted score of **70% text similarity + 30% supplied skill overlap**. This is a separate baseline from the notebook's pairwise analysis, and it uses supplied skill lists rather than the extractor's predicted skills. The weights are illustrative, not experimentally optimized.

| Metric | Recorded result |
|---|---:|
| Valid candidate–job pairs | 348 |
| Candidates evaluated | 30 |
| Mean Spearman correlation | 0.1809 |
| Mean NDCG@5 | 0.9696 |
| Top-1 agreement | 30% (9 of 30 candidates) |

These values were checked against the saved [per-candidate metrics](reports/ranking_validation/ranking_metrics_by_candidate.csv). [Pair predictions](reports/ranking_validation/ranking_pair_predictions.csv) are also available. The ranking script defaults to the small candidate file, unlike the full-data preprocessing and extraction notebooks.

The reference match scores are precomputed proxies rather than human relevance judgments. Weak rank correlation and 30% top-1 agreement indicate substantial disagreement despite the high NDCG@5. This validation does not establish full-dataset or real-world matching accuracy.

## Challenges and Limitations

- **Parsing:** CSV-based analysis does not measure PDF/DOCX parsing accuracy. Complex layouts, nonstandard section headings, and joined words need targeted validation.
- **Skill recognition:** Generic terms cause false positives; exact dictionary matching does not reliably handle unfamiliar skills or equivalent terminology. Punctuation-sensitive names also need review.
- **Evaluation:** Held-out extraction evaluation, broader ranking validation, and independent label review remain necessary.
- **Semantic matching:** TF-IDF measures lexical overlap. Transformer-based matching and comparison with the current baseline are not implemented yet.
- **Application delivery:** There is no functioning API, frontend, cloud deployment, experiment tracking, or monitoring in the current repository.

## Future Work

- Implement sentence-transformer embeddings and compare their results with the TF-IDF baseline in Notebook 03.
- Expand validation with a suitable held-out split, domain-level results, and independently reviewed examples.
- Implement the FastAPI backend and connect document parsing, preprocessing, skill extraction, and matching.
- Build the resume-upload and job-description interface, displaying matched skills, missing skills, and scores.
- Complete Docker and cloud deployment, then add experiment tracking and monitoring.
- Test the integrated workflow and prepare screenshots, the final report, presentation, and demo.

## Project Structure

```text
depi_gapAnalyzer/
├── README.md
├── requirements.txt
├── Dockerfile                         # Deployment placeholder
├── notebooks/
│   ├── 01_data_preprocessing_and_eda.ipynb
│   ├── 02_skill_extraction_and_similarity.ipynb
│   └── 03_embeddings_and_model_comparison.ipynb  # Placeholder
├── src/
│   ├── preprocessing.py
│   ├── skill_extraction.py
│   ├── similarity.py
│   ├── pipeline.py
│   ├── evaluation.py
│   ├── ranking_validation.py
│   └── embeddings.py                  # Placeholder
├── api/
│   └── main.py                        # Placeholder
├── data/
│   ├── raw/                           # Full source CSVs
│   ├── processed/                     # Full cleaned CV/job exports
│   └── sample/                        # Small reference datasets
└── reports/
    ├── Milestone_1_EDA_Report.md
    ├── eda_figures/                    # Images used by the EDA report
    ├── model_evaluation/
    │   └── MODEL_EVALUATION_REPORT.md
    └── ranking_validation/
        ├── ranking_metrics_by_candidate.csv
        └── ranking_pair_predictions.csv
```

## Running the Existing Work

The implemented workflow uses Python, pandas, NLTK, spaCy, scikit-learn, Matplotlib, Seaborn, and JupyterLab. PDF and DOCX helpers use PyPDF2 and python-docx. The rule-based spaCy pipeline uses `spacy.blank("en")`, so it does not require downloading a pretrained spaCy model.

### Download the Full Datasets

The full raw and processed CV files are stored with Git LFS. Install Git LFS on
your machine, then run these commands from the cloned repository before opening
the notebooks:

```bash
git lfs install
git lfs pull
```

This downloads the actual CSV contents in place of Git LFS pointer files.

### Python Environment Setup

Use Python 3.11 or newer. The virtual environment is stored in `.venv`; it is
local to your computer and intentionally excluded from Git.

#### Linux and macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### Windows Command Prompt

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

Notebook kernels can run from the project root or `notebooks/`. Both notebooks
resolve their data paths from the project root.

Notebook 01 still contains the original NLTK resource downloads and CSV writes.
Running it can download resources and overwrite the two processed CSVs. Run
Notebook 01 before Notebook 02. Notebook 02 rejects old sample exports when their
candidate or job IDs do not cover the raw datasets, and restores skill lists
without requiring Notebook 01's in-memory variables. Install packages
with `requirements.txt` before execution; `%pip install` lines were removed from
the notebooks. PDF and DOCX support uses the original `PyPDF2` and `python-docx`.

To leave the environment on any operating system, run `deactivate`.

If your editor asks you to choose a Python interpreter or notebook kernel,
select the one inside `.venv`.

### Reproduce the Recorded Ranking Validation

From the project root with the environment activated:

```bash
python -m src.ranking_validation
```

By default this reads `data/sample/small_cv.csv`, `data/raw/job.csv`, and `data/raw/matches.csv`, then replaces the ranking CSVs under `reports/ranking_validation/`. Use the script's `--cv`, `--jobs`, `--matches`, and `--output` options to change the inputs or output location. Changing the candidate input changes the evaluation scope; the recorded 30-candidate results above should not be assumed to apply to a different run.

## Implementation and Data Notes

- Notebook 01 regenerates full processed data; Notebook 02 checks raw ID coverage before using those exports and restores serialized skill lists.
- Reusable functions live in `src/`. Importing these modules does not load datasets, download NLTK resources, or run evaluation.
- The active notebooks use full datasets; previews and example pairs do not restrict aggregate analysis. The separate ranking-validation script uses the candidate subset described above.
- Keep `reports/eda_figures/` alongside the EDA Markdown file so its images render correctly.
- `api/main.py` and `src/embeddings.py` contain only placeholder docstrings; the Dockerfile contains only comments and cannot build an application image yet.
- The original notebook and helper scripts are preserved in Git commit `66c9d4776e46660307f933c9168cc98be355c670`. For example: `git show 66c9d4776e46660307f933c9168cc98be355c670:src/resume_skill_gap.ipynb`.

## Historical Helper Scripts


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
