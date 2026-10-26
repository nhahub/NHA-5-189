"""Frozen-model test evaluation and rule-based skill evidence feedback."""
import ast
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src import milestone3 as m


def snapshot(root):
    fingerprints = m.capture_fingerprints(root)
    fingerprints['src/milestone3_evaluation.py'] = m.digest(root / 'src/milestone3_evaluation.py')
    for folder in ['models/milestone3/v2', 'data/processed/milestone3/v2', 'reports/milestone3/v2']:
        for path in sorted((root / folder).iterdir()):
            if path.is_file():
                fingerprints[path.relative_to(root).as_posix()] = m.digest(path)
    return fingerprints


def strict_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf8')


def load_assets(root):
    root = Path(root)
    before = snapshot(root)
    comparison, audit, selection = m.run(root)
    model = m.load_logistic_regression(root)
    folder = root / 'models/milestone3/v2'
    dictionary = json.loads((folder / 'dictionary.json').read_text(encoding='utf8'))
    definitions = json.loads((folder / 'feature_definitions.json').read_text(encoding='utf8'))
    if definitions['feature_order'] != m.FEATURES or dictionary['aliases'] != m.ALIASES:
        raise RuntimeError('Saved feature order or aliases differ from the reviewed preprocessing')
    classes = list(model.classes_)
    if sorted(classes) != [0, 1]:
        raise RuntimeError(f'Expected binary model classes [0, 1], got {classes}')
    assets = {'model': model, 'vectorizer': joblib.load(folder / 'tfidf_vectorizer.joblib'),
              'extract': m.make_extractor(dictionary['skills'], dictionary['aliases']),
              'feature_order': definitions['feature_order'], 'threshold': float(selection['threshold']),
              'positive_index': classes.index(1), 'comparison': comparison, 'audit': audit,
              'fingerprints': before, 'root': root}
    m.check_fingerprints(root, before)
    return assets


def analyze_skill_gap(resume_text, job_text, assets):
    """Coverage is displayed on a 0–1 scale; no skill evidence displays null."""
    for name, value in [('Resume', resume_text), ('Job description', job_text)]:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{name} text must be a nonempty string.')
    frame = pd.DataFrame({'resume_text': [resume_text], 'job_text': [job_text]})
    table = m.features(frame, assets['vectorizer'], assets['extract'])[assets['feature_order']]
    score = float(assets['model'].predict_proba(table)[0, assets['positive_index']])
    resume = assets['extract'](resume_text)
    job = assets['extract'](job_text)
    missing = sorted(job - resume)
    result = {'resume_skills': sorted(resume), 'job_skills': sorted(job),
              'matched_skills': sorted(resume & job), 'job_skills_not_found': missing,
              'job_skill_coverage': float(table.iloc[0].job_skill_coverage) if job else None,
              'coverage_scale': '0–1; null means insufficient extracted job-skill evidence',
              'tfidf_text_similarity': float(table.iloc[0].tfidf_cosine),
              'model_classification': 'Suitable Match' if score >= assets['threshold'] else 'Unsuitable Match',
              'classifier_score': score, 'classification_threshold': assets['threshold'],
              'score_note': 'A classifier score is not a hiring probability. Classification, skill coverage and text similarity are separate outputs.',
              'skill_evidence_note': 'These are mentioned skills, not necessarily essential requirements. A skill not found in your resume may still be one you have.' if job else 'Insufficient extracted skill evidence in the job description; this is not a confirmed mismatch.',
              'suggestions': [{'skill': skill, 'guidance': f'{skill} appears in the job description but was not found in your resume. If you have used {skill}, add truthful evidence such as a relevant project or responsibility. If you have not used {skill}, consider learning and practicing it.'} for skill in missing],
              'model_features': {name: float(table.iloc[0][name]) for name in assets['feature_order']}}
    json.dumps(result, allow_nan=False)
    return result


def evaluate_test(root):
    root = Path(root)
    before = snapshot(root)
    versions = m.package_versions()
    versions['matplotlib'] = m.importlib.metadata.version('matplotlib')
    base = root / 'reports/milestone3/test_evaluation'
    version = 1
    while (base / f'v{version}').exists():
        folder = base / f'v{version}'
        marker = folder / 'completed.json'
        if marker.is_file():
            saved = json.loads(marker.read_text(encoding='utf8'))
            if saved['fingerprints'] == before and saved['versions'] == versions:
                for name, value in saved['artifacts'].items():
                    if not (folder / name).is_file() or m.digest(folder / name) != value:
                        raise RuntimeError(f'Evaluation artifact hash mismatch: {folder / name}')
                comparison = pd.read_csv(folder / 'test_comparison.csv')
                m.check_fingerprints(root, before)
                print(f'Reused completed test evaluation v{version}; no predictions recomputed.')
                return folder, comparison
        version += 1
    assets = load_assets(root)
    _, development, _, summary = m.validate(root)
    manifest = pd.read_csv(root / 'data/processed/milestone3/v2/split_manifest.csv', dtype=str, keep_default_na=False)
    if not manifest.pair_id.is_unique or set(manifest.pair_id) != set(development.pair_id):
        raise RuntimeError('Saved split manifest does not cover the development pairs exactly once')
    expected = development.set_index('pair_id').loc[manifest.pair_id]
    for column in ['training_label', 'label_source', 'sampling_domain']:
        if expected[column].astype(str).tolist() != manifest[column].tolist():
            raise RuntimeError(f'Manifest metadata mismatch: {column}')
    if set(manifest.split) != {'train', 'validation', 'test'}:
        raise RuntimeError('Unexpected saved split names')
    test = development.set_index('pair_id').loc[manifest.loc[manifest.split.eq('test'), 'pair_id']].reset_index()
    counts = test.training_label.value_counts().to_dict()
    if len(test) != 10 or counts != {0: 8, 1: 2}:
        raise RuntimeError(f'Reserved test counts differ from reviewed expectations: {len(test)}, {counts}')
    x = m.features(test, assets['vectorizer'], assets['extract'])[assets['feature_order']]
    scores = assets['model'].predict_proba(x)[:, assets['positive_index']]
    predictions = test[['pair_id', 'job_title', 'sampling_domain', 'training_label', 'label_source']].copy()
    predictions['logistic_regression_score'] = scores
    predictions['logistic_regression_prediction'] = (scores >= assets['threshold']).astype(int)
    settings = {}
    reference = assets['comparison'].set_index('name')
    for name, feature in [('majority', None), ('tfidf_threshold', 'tfidf_cosine'), ('skill_threshold', 'job_skill_coverage')]:
        row = reference.loc[name]
        config = ast.literal_eval(row['settings'])
        threshold = float(row['threshold'])
        baseline_scores = np.full(len(test), config['training_majority']) if feature is None else x[feature].to_numpy()
        predictions[name + '_prediction'] = (baseline_scores >= threshold).astype(int)
        settings[name] = {'settings': config, 'threshold': threshold}
    results = [{'name': name, **m.metrics(test.training_label, predictions[name + '_prediction'])} for name in m.REFERENCE_NAMES]
    comparison = pd.DataFrame(results)
    errors = predictions[predictions.training_label.ne(predictions.logistic_regression_prediction)].join(x)
    analyses = []
    for _, row in errors.iterrows():
        document = test.set_index('pair_id').loc[row.pair_id]
        feedback = analyze_skill_gap(document.resume_text, document.job_text, assets)
        analyses.append({'pair_id': row.pair_id, 'error_type': 'false_positive' if row.logistic_regression_prediction else 'false_negative',
                         'job_title': row.job_title, 'domain': row.sampling_domain,
                         'supplied_label': int(row.training_label), 'prediction': int(row.logistic_regression_prediction),
                         'features': {name: float(row[name]) for name in m.FEATURES},
                         'matched_mentioned_skills': feedback['matched_skills'], 'mentioned_job_skills_not_found': feedback['job_skills_not_found'],
                         'hypothesis': 'The classifier uses lexical similarity and mentioned-skill evidence. This may not capture the role responsibilities, experience or context described in these documents. Missing dictionary matches and unverified annotation decisions are other possible explanations; these are hypotheses, not proven causes.'})
        # These observations come from reading the two misclassified documents.
        observations = {
            'cand_01689:3899539354': 'The resume describes a student research assistant with data-analysis skills and 1–3 years of experience. The job describes an HR executive with 15+ years of HR experience and employment/labor-law knowledge. The four matching features do not explicitly compare seniority or required experience, which may help explain this false positive.',
            'cand_02542:3901981623': 'The resume describes accounting and project-administration work; the job describes IT infrastructure, POS systems, Active Directory, firewall and VPN applications. The word controller appears in an accounting context in the resume and in domain controller in the job. Shared words may inflate lexical similarity without establishing the same responsibilities; this is a possible explanation, not a proven cause.',
        }
        analyses[-1]['document_observation_and_hypothesis'] = observations.get(row.pair_id, 'See the mentioned-skill comparison; further manual document review is needed before assigning a specific cause.')
    domains = []
    for domain in sorted(development.sampling_domain.unique()):
        mask = test.sampling_domain.eq(domain)
        if not mask.any():
            domains.append({'domain': domain, 'pairs': 0, 'suitable': 0, 'unsuitable': 0, 'metrics': None, 'note': 'Unsupported: no test examples'})
        else:
            labels = test.loc[mask, 'training_label']
            absent = [name for value, name in [(0, 'unsuitable'), (1, 'suitable')] if not labels.eq(value).any()]
            domains.append({'domain': domain, 'pairs': int(mask.sum()), 'suitable': int(labels.sum()), 'unsuitable': int((labels == 0).sum()),
                            'metrics': m.metrics(labels, predictions.loc[mask, 'logistic_regression_prediction']),
                            'note': f'Descriptive only; absent classes: {absent}. Class metrics with zero support are undefined, represented by zero under zero_division=0.'})
            if absent:
                for label in absent:
                    for metric in ['precision', 'recall', 'f1']:
                        domains[-1]['metrics'][f'{label}_{metric}'] = None
                domains[-1]['note'] = f'Descriptive only; absent classes: {absent}. Their class metrics are null (unsupported). Macro F1 uses the fixed two-class convention with zero_division=0.'
    # The same inference path must reproduce evaluation features and decisions.
    for i, row in test.iterrows():
        feedback = analyze_skill_gap(row.resume_text, row.job_text, assets)
        np.testing.assert_allclose(list(feedback['model_features'].values()), x.iloc[i].to_numpy(), atol=1e-14)
        np.testing.assert_allclose(feedback['classifier_score'], scores[i], atol=1e-14)
    folder = base / f'v{version}'
    folder.mkdir(parents=True, exist_ok=False)
    pd.concat([test[['pair_id', 'training_label']].reset_index(drop=True), x], axis=1).to_csv(folder / 'test_features.csv', index=False)
    predictions.to_csv(folder / 'test_predictions.csv', index=False)
    comparison.to_csv(folder / 'test_comparison.csv', index=False)
    errors.to_csv(folder / 'test_errors.csv', index=False)
    strict_json(folder / 'error_analysis.json', analyses)
    strict_json(folder / 'domain_results.json', domains)
    strict_json(folder / 'metrics.json', results)
    strict_json(folder / 'baseline_settings.json', settings)
    strict_json(folder / 'evaluation_fingerprints.json', {'current_evaluation_inputs_models_sources': before, 'historical_training': json.loads((root / 'reports/milestone3/v2/completed.json').read_text())['fingerprints'], 'model_reference': 'models/milestone3/v2/logistic_regression.joblib', 'threshold': assets['threshold'], 'positive_class_index': assets['positive_index'], 'versions': versions})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matrix = results[0]['confusion_matrix']
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.imshow(matrix, cmap='Blues', vmin=0)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(matrix[i][j]), ha='center', va='center')
    ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=['Unsuitable', 'Suitable'], yticklabels=['Unsuitable', 'Suitable'], xlabel='Predicted label', ylabel='Actual label', title='Held-out test: Logistic Regression')
    fig.tight_layout(); fig.savefig(folder / 'confusion_matrix.png', dpi=150); plt.close(fig)
    correct = int((predictions.training_label == predictions.logistic_regression_prediction).sum())
    fp, fn = matrix[0][1], matrix[1][0]
    validation_f1 = float(reference.loc['logistic_regression', 'macro_f1'])
    report = f'''# Held-out test evaluation v{version}

The frozen Logistic Regression correctly classified {correct} of ten test pairs. Test macro F1 is {results[0]['macro_f1']:.4f}, compared with {validation_f1:.4f} on validation. We retained C=10, StandardScaler, balanced class weights and threshold 0.5. No training, refitting, tuning or split regeneration occurred. Scores at least 0.5 predict Suitable Match; the positive class index was read from classes_.

## Results and reference baselines

{comparison.to_string(index=False)}

Baseline settings were loaded from the previous validation comparison: {json.dumps(settings)}. They were not selected using the test set. Confusion-matrix rows are actual labels and columns are predictions, ordered [Unsuitable, Suitable]. See confusion_matrix.png.

The TF-IDF threshold baseline scores higher than Logistic Regression on this test set. We retain the previously selected Logistic Regression; test results do not select a replacement or change any settings.

## Errors

False positives: {fp}. False negatives: {fn}. {'No misclassified examples were found.' if not analyses else 'The error table records pair IDs, titles, domains, labels, predictions and features. The accompanying analysis compares mentioned skills in the corresponding resume and job documents. Possible explanations remain hypotheses; labels and model settings were not changed.'}

{json.dumps(analyses, indent=2)}

## Domain coverage

{json.dumps(domains, indent=2)}

Finance has no test examples, so its performance is unsupported rather than zero. Metrics for absent classes cannot estimate class performance. Per-domain figures are descriptive because each domain has very few pairs.

## Limits and remaining work

There are only ten test pairs, including two suitable examples. The development dataset has 49 pairs: 46 automated annotations and three recorded first reviews, without independent human verification. Metrics measure agreement with these annotations, not independently established hiring suitability. Sales has no suitable development examples. All five suitable IT development examples share the same help-desk job. Domain coverage is uneven. These results provide only preliminary evidence; the historical validation comparison is preserved unchanged.

Skill-gap feedback uses explicit rules and the same saved preprocessing as evaluation. Coverage is shown on a 0–1 scale, or null when no job skills are recognized. Internally the model still receives coverage 0, missing count 0 and no_job_skills 1. Suggestions refer to mentioned skills not found in the resume and do not establish that the candidate lacks them. Classification and descriptive matching evidence stay separate.

Browser export and React integration remain future work. Milestone 3 is not marked complete. Current evaluation-code fingerprints are recorded separately from the original training fingerprints.
'''
    (folder / 'test_evaluation_report.md').write_text(report, encoding='utf8')
    m.check_fingerprints(root, before)
    hashes = {p.name: m.digest(p) for p in folder.iterdir() if p.is_file()}
    strict_json(folder / 'completed.json', {'fingerprints': before, 'versions': versions, 'artifacts': hashes})
    print(f'Saved held-out test evaluation v{version}; {correct}/10 correct, {fp} false positives, {fn} false negatives.')
    return folder, comparison
