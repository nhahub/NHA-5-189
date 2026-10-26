# Held-out test evaluation v2

The frozen Logistic Regression correctly classified 8 of ten test pairs. Test macro F1 is 0.7619, compared with 1.0000 on validation. We retained C=10, StandardScaler, balanced class weights and threshold 0.5. No training, refitting, tuning or split regeneration occurred. Scores at least 0.5 predict Suitable Match; the positive class index was read from classes_.

## Results and reference baselines

               name  macro_f1  accuracy confusion_matrix  unsuitable_precision  unsuitable_recall  unsuitable_f1  unsuitable_support  suitable_precision  suitable_recall  suitable_f1  suitable_support
logistic_regression  0.761905       0.8 [[6, 2], [0, 2]]                  1.00              0.750       0.857143                   8            0.500000              1.0     0.666667                 2
           majority  0.444444       0.8 [[8, 0], [2, 0]]                  0.80              1.000       0.888889                   8            0.000000              0.0     0.000000                 2
    tfidf_threshold  0.866667       0.9 [[7, 1], [0, 2]]                  1.00              0.875       0.933333                   8            0.666667              1.0     0.800000                 2
    skill_threshold  0.375000       0.6 [[6, 2], [2, 0]]                  0.75              0.750       0.750000                   8            0.000000              0.0     0.000000                 2

Baseline settings were loaded from the previous validation comparison: {"majority": {"settings": {"training_majority": 0}, "threshold": 0.5}, "tfidf_threshold": {"settings": {}, "threshold": 0.1}, "skill_threshold": {"settings": {}, "threshold": 0.3}}. They were not selected using the test set. Confusion-matrix rows are actual labels and columns are predictions, ordered [Unsuitable, Suitable]. See confusion_matrix.png.

The TF-IDF threshold baseline scores higher than Logistic Regression on this test set. We retain the previously selected Logistic Regression; test results do not select a replacement or change any settings.

## Errors

False positives: 2. False negatives: 0. The error table records pair IDs, titles, domains, labels, predictions and features. The accompanying analysis compares mentioned skills in the corresponding resume and job documents. Possible explanations remain hypotheses; labels and model settings were not changed.

[
  {
    "pair_id": "cand_01689:3899539354",
    "error_type": "false_positive",
    "job_title": "Senior Vice President Human Resources",
    "domain": "HR",
    "supplied_label": 0,
    "prediction": 1,
    "features": {
      "tfidf_cosine": 0.05869178985465682,
      "job_skill_coverage": 0.0,
      "missing_job_skill_count": 3.0,
      "no_job_skills": 0.0
    },
    "matched_mentioned_skills": [],
    "mentioned_job_skills_not_found": [
      "focus",
      "organizational",
      "strategic planning"
    ],
    "hypothesis": "The classifier uses lexical similarity and mentioned-skill evidence. This may not capture the role responsibilities, experience or context described in these documents. Missing dictionary matches and unverified annotation decisions are other possible explanations; these are hypotheses, not proven causes.",
    "document_observation_and_hypothesis": "The resume describes a student research assistant with data-analysis skills and 1\u20133 years of experience. The job describes an HR executive with 15+ years of HR experience and employment/labor-law knowledge. The four matching features do not explicitly compare seniority or required experience, which may help explain this false positive."
  },
  {
    "pair_id": "cand_02542:3901981623",
    "error_type": "false_positive",
    "job_title": "Information Technology Administrator",
    "domain": "INFORMATION-TECHNOLOGY",
    "supplied_label": 0,
    "prediction": 1,
    "features": {
      "tfidf_cosine": 0.08643488567050456,
      "job_skill_coverage": 0.0,
      "missing_job_skill_count": 5.0,
      "no_job_skills": 0.0
    },
    "matched_mentioned_skills": [],
    "mentioned_job_skills_not_found": [
      "active directory",
      "functional",
      "information technology",
      "network infrastructure",
      "vpn"
    ],
    "hypothesis": "The classifier uses lexical similarity and mentioned-skill evidence. This may not capture the role responsibilities, experience or context described in these documents. Missing dictionary matches and unverified annotation decisions are other possible explanations; these are hypotheses, not proven causes.",
    "document_observation_and_hypothesis": "The resume describes accounting and project-administration work; the job describes IT infrastructure, POS systems, Active Directory, firewall and VPN applications. The word controller appears in an accounting context in the resume and in domain controller in the job. Shared words may inflate lexical similarity without establishing the same responsibilities; this is a possible explanation, not a proven cause."
  }
]

## Domain coverage

[
  {
    "domain": "BUSINESS-DEVELOPMENT",
    "pairs": 3,
    "suitable": 1,
    "unsuitable": 2,
    "metrics": {
      "macro_f1": 1.0,
      "accuracy": 1.0,
      "confusion_matrix": [
        [
          2,
          0
        ],
        [
          0,
          1
        ]
      ],
      "unsuitable_precision": 1.0,
      "unsuitable_recall": 1.0,
      "unsuitable_f1": 1.0,
      "unsuitable_support": 2,
      "suitable_precision": 1.0,
      "suitable_recall": 1.0,
      "suitable_f1": 1.0,
      "suitable_support": 1
    },
    "note": "Descriptive only; absent classes: []. Class metrics with zero support are undefined, represented by zero under zero_division=0."
  },
  {
    "domain": "FINANCE",
    "pairs": 0,
    "suitable": 0,
    "unsuitable": 0,
    "metrics": null,
    "note": "Unsupported: no test examples"
  },
  {
    "domain": "HR",
    "pairs": 2,
    "suitable": 1,
    "unsuitable": 1,
    "metrics": {
      "macro_f1": 0.3333333333333333,
      "accuracy": 0.5,
      "confusion_matrix": [
        [
          0,
          1
        ],
        [
          0,
          1
        ]
      ],
      "unsuitable_precision": 0.0,
      "unsuitable_recall": 0.0,
      "unsuitable_f1": 0.0,
      "unsuitable_support": 1,
      "suitable_precision": 0.5,
      "suitable_recall": 1.0,
      "suitable_f1": 0.6666666666666666,
      "suitable_support": 1
    },
    "note": "Descriptive only; absent classes: []. Class metrics with zero support are undefined, represented by zero under zero_division=0."
  },
  {
    "domain": "INFORMATION-TECHNOLOGY",
    "pairs": 3,
    "suitable": 0,
    "unsuitable": 3,
    "metrics": {
      "macro_f1": 0.4,
      "accuracy": 0.6666666666666666,
      "confusion_matrix": [
        [
          2,
          1
        ],
        [
          0,
          0
        ]
      ],
      "unsuitable_precision": 1.0,
      "unsuitable_recall": 0.6666666666666666,
      "unsuitable_f1": 0.8,
      "unsuitable_support": 3,
      "suitable_precision": null,
      "suitable_recall": null,
      "suitable_f1": null,
      "suitable_support": 0
    },
    "note": "Descriptive only; absent classes: ['suitable']. Their class metrics are null (unsupported). Macro F1 uses the fixed two-class convention with zero_division=0."
  },
  {
    "domain": "SALES",
    "pairs": 2,
    "suitable": 0,
    "unsuitable": 2,
    "metrics": {
      "macro_f1": 0.5,
      "accuracy": 1.0,
      "confusion_matrix": [
        [
          2,
          0
        ],
        [
          0,
          0
        ]
      ],
      "unsuitable_precision": 1.0,
      "unsuitable_recall": 1.0,
      "unsuitable_f1": 1.0,
      "unsuitable_support": 2,
      "suitable_precision": null,
      "suitable_recall": null,
      "suitable_f1": null,
      "suitable_support": 0
    },
    "note": "Descriptive only; absent classes: ['suitable']. Their class metrics are null (unsupported). Macro F1 uses the fixed two-class convention with zero_division=0."
  }
]

Finance has no test examples, so its performance is unsupported rather than zero. Metrics for absent classes cannot estimate class performance. Per-domain figures are descriptive because each domain has very few pairs.

## Limits and remaining work

There are only ten test pairs, including two suitable examples. The development dataset has 49 pairs: 46 automated annotations and three recorded first reviews, without independent human verification. Metrics measure agreement with these annotations, not independently established hiring suitability. Sales has no suitable development examples. All five suitable IT development examples share the same help-desk job. Domain coverage is uneven. These results provide only preliminary evidence; the historical validation comparison is preserved unchanged.

Skill-gap feedback uses explicit rules and the same saved preprocessing as evaluation. Coverage is shown on a 0–1 scale, or null when no job skills are recognized. Internally the model still receives coverage 0, missing count 0 and no_job_skills 1. Suggestions refer to mentioned skills not found in the resume and do not establish that the candidate lacks them. Classification and descriptive matching evidence stay separate.

Browser export and React integration remain future work. Milestone 3 is not marked complete. Current evaluation-code fingerprints are recorded separately from the original training fingerprints.
