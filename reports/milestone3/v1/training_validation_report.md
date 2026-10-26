# Milestone 3: training and validation, v1

The master contains 150 pairs. Development contains 49 pairs: 12 suitable and 37 unsuitable. There are three recorded first reviews and 46 automated annotations. Independent human verification was not performed. These results measure agreement with annotations, not verified suitability or hiring probabilities.

## Splits

Seed: 42. The search uses only group integrity, sizes and labels. A useful split requires both classes and sizes within 12 percentage points of 60/20/20. Strict connected-component sizes are [5, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]. Strict separation feasible under this rule: True. Scope: Unseen resumes and jobs.

Counts (columns 0 = unsuitable, 1 = suitable):
training_label   0  1
split                
test             8  2
train           22  7
validation       7  3

Overlap counts, measured on IDs and case/whitespace-normalized text:
{
  "candidate_id": {
    "train/validation": 0,
    "train/test": 0,
    "validation/test": 0
  },
  "resume_text": {
    "train/validation": 0,
    "train/test": 0,
    "validation/test": 0
  },
  "job_id": {
    "train/validation": 0,
    "train/test": 0,
    "validation/test": 0
  },
  "job_text": {
    "train/validation": 0,
    "train/test": 0,
    "validation/test": 0
  }
}

Domain counts:
sampling_domain  BUSINESS-DEVELOPMENT  FINANCE  HR  INFORMATION-TECHNOLOGY  SALES
split                                                                            
test                                3        0   2                       3      2
train                              10        4   3                       8      4
validation                          1        3   2                       3      1

## Features and training

Feature order: tfidf_cosine, job_skill_coverage, missing_job_skill_count, no_job_skills. TF-IDF is fitted on 45 unique normalized training documents only. Validation uses transform only. The dictionary uses supplied skill lists restricted to training candidate/job IDs and the existing generic-term filter, with fixed technology aliases. The earlier spaCy extractor uses case-sensitive phrase patterns; this workflow uses punctuation-aware boundaries and longest-first matching to preserve technology distinctions. There is no supported technical/soft-skill taxonomy, so coverage is overall coverage. Extracted job skills are mentioned skills, not necessarily essential requirements. An empty job-skill set gives zero coverage, zero missing skills and indicator one: unavailable skill evidence.

Logistic Regression uses StandardScaler fitted on training rows. Random Forest uses no scaling. Both use balanced class weights and seed 42. Only the four declared features enter the models; tracing metadata stays separate. Thresholds use score >= threshold. Macro F1 selects settings and thresholds on validation. Tie-breaking favors lower C or shallower forests/larger leaves, then thresholds nearest 0.5 (then lower); Logistic Regression wins a trained-family tie. No training-plus-validation refit occurs.

## Validation results

               name                                                     settings  threshold  macro_f1  accuracy confusion_matrix  unsuitable_precision  unsuitable_recall  unsuitable_f1  unsuitable_support  suitable_precision  suitable_recall  suitable_f1  suitable_support
logistic_regression                                                  {'C': 10.0}        0.5  1.000000       1.0 [[7, 0], [0, 3]]              1.000000           1.000000       1.000000                   7                 1.0         1.000000     1.000000                 3
      random_forest {'n_estimators': 100, 'max_depth': 2, 'min_samples_leaf': 4}        0.8  0.866667       0.9 [[7, 0], [1, 2]]              0.875000           1.000000       0.933333                   7                 1.0         0.666667     0.800000                 3
           majority                                     {'training_majority': 0}        0.5  0.411765       0.7 [[7, 0], [3, 0]]              0.700000           1.000000       0.823529                   7                 0.0         0.000000     0.000000                 3
    tfidf_threshold                                                           {}        0.1  0.696970       0.7 [[4, 3], [0, 3]]              1.000000           0.571429       0.727273                   7                 0.5         1.000000     0.666667                 3
    skill_threshold                                                           {}        0.3  0.687500       0.8 [[7, 0], [2, 1]]              0.777778           1.000000       0.875000                   7                 1.0         0.333333     0.500000                 3

Selected trained model: {"model": "logistic_regression", "settings": {"C": 10.0}, "threshold": 0.5, "rule": "score >= threshold predicts suitable", "refit_on_train_plus_validation": false}. Baselines scoring strictly higher: none. The CSV comparison contains class precision, recall, F1, support, accuracy and confusion matrices, with rows actual and columns predicted in order [unsuitable, suitable].

## Limits and checks

Only 49 labeled pairs and class imbalance make validation tuning unstable. Sales has no suitable examples. All 5 suitable IT examples share the same help-desk job:
job_id      job_title                       
3899521894  Information Technology Help Desk    5

Job overlap and uneven domain coverage limit conclusions. Familiar job content and annotation patterns may dominate the comparison. A held-out test is still required. Milestone 3 remains in progress.

Checks passed: identifier and provenance validation; master/development document equality; duplicate-document audit; candidate/resume separation; both classes in every split; technology normalization and empty-skill checks; training-only TF-IDF and scaling; exact feature order; artifact reload reproducing validation features and probabilities. Test documents are used only for split integrity auditing, never feature construction, preprocessing fitting, predictions or performance metrics. No test feature tables or predictions were produced. Input file hashes were checked unchanged at the end of the run.
