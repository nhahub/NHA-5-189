# Held-out test evaluation summary

This summary presents the saved v2 evaluation outputs. No predictions were recomputed. The original report, JSON supporting files and completion metadata remain unchanged.

## Classifier and reference baselines

| Measurement | Accuracy | Macro F1 |
| --- | --- | --- |
| Logistic Regression | 80% | 0.762 |
| Majority class | 80% | 0.444 |
| TF-IDF threshold | 90% | 0.867 |
| Skill coverage threshold | 60% | 0.375 |

The fixed TF-IDF baseline performed better than Logistic Regression on this test set. We keep the selected Logistic Regression (C=10, balanced class weights, StandardScaler, threshold 0.5); the test results do not select a replacement or change any settings.

## Logistic Regression by class

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| Unsuitable | 1.000 | 0.750 | 0.857 | 8 |
| Suitable | 0.500 | 1.000 | 0.667 | 2 |

## Confusion matrix

Rows are actual labels and columns are predictions, both ordered **[Unsuitable, Suitable]**.

| Actual / Predicted | Unsuitable | Suitable |
| --- | --- | --- |
| Unsuitable | 6 | 2 |
| Suitable | 0 | 2 |

False positives: **2**. False negatives: **0**.

## Domain coverage

| Domain | Pairs | Unsuitable | Suitable | Accuracy |
| --- | --- | --- | --- | --- |
| BUSINESS-DEVELOPMENT | 3 | 2 | 1 | 100.0% |
| FINANCE | 0 | 0 | 0 | No test examples |
| HR | 2 | 1 | 1 | 50.0% |
| INFORMATION-TECHNOLOGY | 3 | 3 | 0 | 66.7% |
| SALES | 2 | 2 | 0 | 100.0% |

Finance has no test examples, so its performance is unsupported, not zero. IT and Sales have no suitable test examples. These small domain groups do not support broad comparisons.

## False positives

### Senior Vice President Human Resources

Pair `cand_01689:3899539354` (HR) was labeled Unsuitable and predicted Suitable. The resume describes a student research assistant with data-analysis skills and 1 to 3 years of experience. The job describes an HR executive with 15+ years of HR experience and employment/labor-law knowledge. The four matching features do not explicitly compare seniority or required experience, which may help explain this false positive. Skill coverage was 0%, with TF-IDF similarity 0.059. These observations suggest possible causes; they do not prove why the classifier made this prediction.

### Information Technology Administrator

Pair `cand_02542:3901981623` (INFORMATION-TECHNOLOGY) was labeled Unsuitable and predicted Suitable. The resume describes accounting and project-administration work; the job describes IT infrastructure, POS systems, Active Directory, firewall and VPN applications. The word controller appears in an accounting context in the resume and in domain controller in the job. Shared words may inflate lexical similarity without establishing the same responsibilities; this is a possible explanation, not a proven cause. Skill coverage was 0%, with TF-IDF similarity 0.086. These observations suggest possible causes; they do not prove why the classifier made this prediction.

## Limitations and remaining work

The test set contains ten pairs and only two suitable examples, with no Finance coverage. The development labels comprise 46 automated annotations and three recorded first-review decisions, without independent human verification. Metrics measure agreement with those annotations, not independently established hiring suitability.

Sales has no suitable development examples. All five suitable IT development examples share one help-desk job. Validation tuning on 49 imbalanced pairs may be unstable; perfect validation performance did not carry over to test.

The machine-readable metrics, domain results and error analysis remain supporting files beside this summary. Skill-gap feedback reports mentioned skills not found in a resume and gives conditional guidance; it does not establish that the candidate lacks them or estimate hiring probability. Browser export and React integration remain future work. Milestone 3 is still in progress.
