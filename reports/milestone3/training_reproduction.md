# Intentional Logistic Regression reproduction

The implementation is `src/milestone3_training.py`, recovered from `reports/milestone3/archive/milestone3_pre_reuse_refactor_v1.py`. Only the Logistic Regression path was restored. The saved trained pipeline remains `models/milestone3/v2/logistic_regression.joblib`; evaluation and feedback remain in `src/milestone3_evaluation.py`.

Importing the training module does not train or write files. Normal notebook execution loads the frozen model and reuses completed test results. No training command was executed during this cleanup.

## Explicit command

From the project root in PowerShell, intentionally run:

```powershell
& 'D:\Downloads\NHA-5-189\.runtime\python\python.exe' -m src.milestone3_training --root 'D:\Downloads\depi_gapAnalyzer' --output-version v3
```

Use an unused numbered version. The command refuses to overwrite any existing output folder under `data/processed/milestone3/`, `models/milestone3/` or `reports/milestone3/`. A direct function call is also explicit: `train(project_root, output_version="v3")`.

## What is reproduced

The command verifies the reviewed v2 inputs and artifact hashes, then reads the existing split manifest without regenerating assignments. Only training pairs contribute to the supplied-skill-list dictionary and unique normalized documents used to fit TF-IDF. It reuses the project dictionary filter, aliases, punctuation-aware extraction and the four saved features in their original order.

The pipeline is StandardScaler followed by Logistic Regression, with balanced class weights, seed 42 and max_iter=2000. The recovered validation search uses C in [0.1, 1, 10] and thresholds [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]. Selection uses validation macro F1, then lower C, then the threshold closest to 0.5, then the lower threshold. Scores greater than or equal to the threshold predict suitable.

The majority baseline comes from training labels. TF-IDF and skill-coverage baseline thresholds use [0, 0.1, ..., 1] and validation macro F1, followed by distance to 0.5 and lower threshold. These are reference rules, not additional trained classifiers.

No test documents reach feature construction or fitting, and no test metrics enter selection. There is no refit on training plus validation. New outputs record sources, input fingerprints, package versions, search trials, validation predictions and the selected model; the historical v2 files remain untouched.

## Why the frozen model uses C=10 and threshold 0.5

The saved v2 `search.json` records C=10 and threshold 0.5 as the only Logistic Regression combination with validation macro F1=1.000 and accuracy=1.000. This is evidence from the historical search, not a new training run. The test result is weaker, and the TF-IDF baseline performs better on test; neither finding changes the frozen classifier or justifies tuning on test.
