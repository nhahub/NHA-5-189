Resume Skill Gap Analyzer
DEPI - AI & Data Science Track

A React application that compares a resume with a job description, identifies shared skills and skills not found in the resume, and suggests what to highlight or develop. A trained Logistic Regression classifier provides a separate resume-job assessment.

The application runs document parsing and model inference in the browser. Python supports data preparation, training, evaluation, and model export.
Features
- Paste a resume or upload TXT, DOCX, or a PDF containing selectable text.
- Review and edit extracted text before analysis.
- Enter a job description and view matched and unrecognized job skills.
- View job-skill coverage and TF-IDF text similarity separately.
- Receive a Logistic Regression assessment and conditional improvement suggestions.
- Recognize supported aliases such as JS/JavaScript.
- Use a responsive navy interface with loading, retry, and parsing-error states.
Uploads are limited to 10 MiB. Scanned PDFs need OCR or pasted text. The application does not assess resume grammar or visual layout.
Technology
Area	Technologies
Data preparation and EDA	Python, pandas, NumPy, NLTK, Matplotlib, Seaborn
Skill extraction	spaCy EntityRuler for the baseline; dictionary and alias matching for the frozen inference pipeline
Classification	Scikit-learn Logistic Regression with StandardScaler
Text matching	Training-fitted TF-IDF and cosine similarity
Frontend	React, JavaScript, Vite, CSS
Browser document parsing	PDF.js and Mammoth; local TXT reading
Website hosting target	GitHub Pages


Logistic Regression is the only active trained classifier. Majority-class, TF-IDF-threshold, and skill-coverage-threshold rules provide evaluation baselines.
Run the website locally
Install Git, Git LFS, and a Node.js version compatible with the committed frontend dependencies. The recorded frontend build used Node 24.11.0 and npm 11.6.1.
git clone https://github.com/nhahub/NHA-5-189.git
cd NHA-5-189
git lfs install
git lfs pull
cd frontend
npm ci
npm run dev
Open the exact local URL printed by Vite. In PowerShell, use npm.cmd instead of npm if execution policy blocks npm.ps1.

To check the frontend and preview its production build:
npm test
npm run build
npm run preview
The application uses the exported JSON model in frontend/public/models/milestone3/v1/assets.json. Running the website does not require Python, the raw training CSVs, or a Python API.

The repository is nhahub/NHA-5-189. This README does not assume a verified public deployment URL; confirm the current address and deployment status in the repository's Pages settings and Actions runs.
What the results mean
Result	Meaning
Resume-Job Assessment	Suitable Match or Unsuitable Match under the project's development-label rubric
Job-Skill Coverage	Unique matched skills divided by unique recognized job skills, displayed as a percentage
Text Similarity	Cosine similarity between the resume and job TF-IDF vectors
Skills to Highlight or Develop	Skills mentioned in the job description that the extractor did not find in the resume
Recommended Improvements	Conditional suggestions to add truthful evidence or practice a skill


A skill not found in the resume may still be one the candidate has. Recognized job skills are mentioned skills, not automatically essential requirements. When no job skills are recognized, displayed coverage is Unavailable.

Classification, coverage, and similarity measure different things. A Suitable Match can still have skill gaps. None of these results represents the probability of getting hired.
Data and annotation
Source: Job-Resume Matching Dataset on Hugging Face.
Dataset	Local path	Records
Resumes	data/raw/cv.csv	9,544
Job descriptions	data/raw/job.csv	1,167
Supplied candidate-job matches	data/raw/matches.csv	122,560


Initial checks found no missing values, duplicate identifiers/pairs, or unknown references in the inspected columns. The source label_strength values describe positive-strength categories; weak-positive or unrecorded pairs are not automatically unsuitable.

Milestone 3 uses a separate pair-level development dataset:
- 150 master pairs across five domains.
- 49 binary-labeled pairs: 12 suitable and 37 unsuitable.
- 46 automated annotations and 3 recorded first-review decisions.
- 101 uncertain pairs excluded from model development.
- Independent human verification was not performed.
The master preserves annotation explanations, assignments, and provenance. Assigned reviewer names do not establish that a human review was completed.

Large files tracked with Git LFS require git lfs pull. If a CSV contains only a short pointer rather than dataset rows, download its LFS content before running Python workflows. Retain source attribution and review the source dataset's terms before redistributing data.
Machine learning workflow
Each example is a resume-job pair. The classifier receives four numerical features:
Feature	Definition
tfidf_cosine	Cosine similarity in the saved TF-IDF space
job_skill_coverage	Matched unique skills divided by recognized unique job skills
missing_job_skill_count	Number of recognized job skills absent from the resume
no_job_skills	1 when the extractor recognizes no job skills; otherwise 0


With no recognized job skills, internal coverage and missing count are zero and the indicator is one. The interface displays coverage as unavailable rather than treating this as confirmed skill mismatch.

TF-IDF, the dictionary derived from supplied skill lists, scaling, and classifier fitting use training records only. Explicit aliases and technology terms are fixed inputs. Identifiers, annotation rationales, source scores, label sources, and domains are not classifier features.
Split	Pairs	Suitable	Unsuitable
Training	29	7	22
Validation	10	3	7
Held-out test	10	2	8


The saved split uses seed 42 and connected groups to prevent shared candidate IDs, job IDs, or identical case/whitespace-normalized documents across partitions. This check does not establish that all near-duplicate documents are absent.

The frozen pipeline is StandardScaler followed by balanced Logistic Regression, with C=10, max_iter=2000, and classification threshold 0.5. Settings and thresholds were selected using validation data. Test results did not change them.

The saved model is models/milestone3/v2/logistic_regression.joblib. Its browser export contains coefficients, intercept, scaling statistics, TF-IDF vocabulary/IDF values, skill aliases, and normalization behavior.
Evaluation
Suitability classification
The selected Logistic Regression achieved validation macro F1 1.000 on ten validation pairs. Its held-out performance was lower:
Classifier or reference baseline	Test accuracy	Test macro F1
Logistic Regression	80%	0.762
Majority class	80%	0.444
TF-IDF threshold	90%	0.867
Skill-coverage threshold	60%	0.375


The TF-IDF baseline performed better on this test set. The previously selected Logistic Regression remains frozen; the test set was not used to select a replacement or tune settings.
Logistic Regression class	Precision	Recall	F1	Support
Unsuitable	1.000	0.750	0.857	8
Suitable	0.500	1.000	0.667	2


Confusion matrix, with actual-label rows and predicted-label columns:
Actual / Predicted	Unsuitable	Suitable
Unsuitable	6	2
Suitable	0	2


There were two false positives and no false negatives. These metrics measure agreement with the development annotations, not independently established hiring suitability.
Earlier extraction and ranking baselines
The supplied earlier README records mean per-resume extraction precision/recall/F1 of 0.56/0.97/0.70 for the baseline dictionary and 0.57/0.96/0.70 after generic-term filtering. These in-dataset measurements use supplied labels and a dictionary built from the same source data; they are separate from held-out classifier evaluation.

Earlier ranking validation covered 348 pairs across 30 candidates, with mean Spearman correlation 0.1809, mean NDCG@5 0.9696, and top-1 agreement 30%. Its references are supplied proxy scores, not independently reviewed relevance judgments. These historical results do not establish full-dataset matching accuracy.
Python-JavaScript parity
Recorded Node verification covered 23 text cases, including all ten validation pairs, and three boundary vectors. Twenty-one valid text pairs plus three boundary cases had exact classification agreement (24/24); skill sets agreed for 21/21 valid text pairs. The largest reported numerical difference was approximately 7.11e-15.

Node parity, production builds, and frontend tests passed in the recorded checks. A user screenshot also shows results rendered in a browser. Complete desktop/mobile acceptance, upload-format testing, console/network inspection, and browser-engine parity remain unverified in the reports reviewed for this README.
Project structure
The main working paths are:
Path	Purpose
frontend/	React application, document parsing, styling, and frontend tests
frontend/src/inference/milestone3.mjs	Browser inference engine
frontend/public/models/milestone3/v1/assets.json	Public model and preprocessing JSON
notebooks/01_data_preprocessing_and_eda.ipynb	Data preparation and EDA
notebooks/02_skill_extraction_and_similarity.ipynb	Baseline extraction and similarity
notebooks/03_model_training_and_comparison.ipynb	Frozen-model results, evaluation, and feedback
src/milestone3.py	Verified frozen-model loading and shared feature logic
src/milestone3_training.py	Explicit Logistic Regression reproduction workflow
src/milestone3_evaluation.py	Held-out evaluation and skill-gap feedback
src/milestone3_export.py	Explicit browser export and Python reference generation
data/labeled/	Master review and development-label datasets
data/processed/milestone3/v2/	Saved splits and train/validation features
models/milestone3/v2/	Frozen Python model and preprocessing artifacts
models/browser/v1/	Versioned browser export and integrity metadata
reports/milestone3/	Training, evaluation, reproduction, and export reports
reports/frontend/	Frontend implementation and verification records
tests/	Python checks and Node parity verifier


Older API, Docker, embedding, or comparison artifacts may remain as historical files. They are not required for the current browser-only application.
Python setup and reproduction
The recorded Python workflows used Python 3.12. Create an environment from the repository root:
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m jupyter lab
Select that environment as the notebook kernel. The frozen-model loader checks recorded package versions and artifact hashes. If it reports incompatibility, inspect reports/milestone3/v2/versions.json and the reproduction guide rather than bypassing its checks.

Notebook 01 may download NLTK resources and overwrite processed exports. Preserve existing outputs before rerunning preprocessing. Ordinary execution of the current Milestone 3 notebook loads frozen results; it does not retrain the classifier.
Intentional training reproduction
Read [the reproduction guide](reports/milestone3/training_reproduction.md) first. From the project root, use an unused output version:
.\.venv\Scripts\python.exe -m src.milestone3_training --root . --output-version v3
This explicitly trains a new reproduction version using the saved split assignments and validation procedure. It refuses to overwrite existing version folders. Do not run it merely to start the website.
Export and parity verification
.\.venv\Scripts\python.exe -m src.milestone3_export --root .
node tests/verify_browser_parity.mjs . .\.venv\Scripts\python.exe v1
Use the compatible recorded Python environment. Export reads frozen assets without training; the parity verifier compares JavaScript against Python without fitting models.
Reports
- [Training and validation](reports/milestone3/v2/training_validation_report.md)
- [Readable held-out test summary](reports/milestone3/test_evaluation/v2/test_evaluation_summary.md)
- [Detailed held-out test evaluation](reports/milestone3/test_evaluation/v2/test_evaluation_report.md)
- [Training reproduction](reports/milestone3/training_reproduction.md)
- [Browser export and parity](reports/milestone3/browser_export_report.md)
- [Initial frontend implementation](reports/frontend/milestone4_implementation_v1.md)
- [Frontend readability and verification](reports/frontend/milestone4_readability_and_verification_v2.md)
These reports describe the versions tested at the time. Later UI copy changes do not change historical model metrics.
Limitations and next steps
- The development dataset is small and most labels are automated.
- The held-out test has ten pairs, only two suitable examples, and no Finance examples.
- Sales has no suitable development examples; five suitable IT examples share one help-desk job.
- Exact dictionary matching may miss unfamiliar skills and include generic terms. Similarity does not establish equivalent responsibilities or experience.
- The current features do not explicitly compare education, seniority, or years of experience.
- Complex PDF layouts, scanned documents, and unusual DOCX formatting need additional parsing checks.
- Complete browser acceptance and the published deployment need their own verification evidence.
Future work includes broader independently reviewed data, improved skill dictionaries, validated education/experience features, semantic embeddings, OCR, and curated learning resources. These are extensions rather than requirements for local browser inference.
Team
Mariam, Sadin, Rowan, Khalfawy, Belal, and Omar.
