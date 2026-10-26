"""Intentional reproduction of the archived Logistic Regression training path.

This module never runs from the inference/evaluation notebook. Importing it
does not read inputs, fit estimators or create outputs. See the reproduction
guide in reports/milestone3 for the exact command and historical selection.
"""
import argparse
import json
from pathlib import Path
import re
import shutil

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src import milestone3 as m

C_GRID = [0.1, 1.0, 10.0]
PROBABILITY_GRID = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
BASELINE_GRID = [i / 10 for i in range(11)]


def search_logistic(x, labels, validation_x, validation_labels):
    """Recovered from milestone3_pre_reuse_refactor_v1.py; one classifier."""
    trials, candidates = [], []
    for simplicity, c in enumerate(C_GRID):
        model = make_pipeline(StandardScaler(), LogisticRegression(
            C=c, class_weight='balanced', random_state=m.SEED, max_iter=2000))
        model.fit(x, labels)
        scores = model.predict_proba(validation_x)[:, list(model.classes_).index(1)]
        for threshold in PROBABILITY_GRID:
            row = {'name': m.CLASSIFIER, 'settings': {'C': c}, 'threshold': threshold,
                   **m.metrics(validation_labels, scores >= threshold)}
            trials.append(row)
            candidates.append(((-row['macro_f1'], simplicity, abs(threshold - .5), threshold), model, row, scores))
    _, model, row, scores = min(candidates, key=lambda item: item[0])
    return model, row, scores, trials


def train(root, *, output_version):
    """Fit only when explicitly called; reserve a fresh numbered output version."""
    root = Path(root).resolve()
    if not re.fullmatch(r'v[1-9][0-9]*', output_version):
        raise ValueError('output_version must be a numbered version such as v3')
    destinations = [root / folder / 'milestone3' / output_version for folder in ['data/processed', 'models', 'reports']]
    if any(folder.exists() for folder in destinations):
        raise FileExistsError(f'Refusing to overwrite output version {output_version}')
    fingerprints = m.capture_fingerprints(root)
    fingerprints['src/milestone3_training.py'] = m.digest(Path(__file__))
    marker = root / 'reports/milestone3/v2/completed.json'
    recorded = json.loads(marker.read_text(encoding='utf8'))
    for name in list(recorded['artifacts']) + ['reports/milestone3/v2/completed.json']:
        fingerprints[name.replace('\\', '/')] = m.digest(root / name)
    versions = m.package_versions()
    m.run(root)  # Verify the reviewed inputs and every historical artifact.
    _, data, _, _ = m.validate(root)
    source_manifest = root / 'data/processed/milestone3/v2/split_manifest.csv'
    manifest = pd.read_csv(source_manifest, dtype=str, keep_default_na=False)
    if not manifest.pair_id.is_unique or set(manifest.pair_id) != set(data.pair_id):
        raise ValueError('Saved manifest must cover every development pair exactly once')
    aligned = data.set_index('pair_id').loc[manifest.pair_id]
    for column in ['training_label', 'label_source', 'sampling_domain']:
        if aligned[column].astype(str).tolist() != manifest[column].tolist():
            raise ValueError(f'Saved manifest metadata mismatch: {column}')
    if set(manifest.split) != {'train', 'validation', 'test'}:
        raise ValueError('Unexpected split names in saved manifest')
    # Test rows never reach feature construction, fitting or model selection.
    train_data = aligned.loc[manifest.loc[manifest.split.eq('train'), 'pair_id']].reset_index()
    validation = aligned.loc[manifest.loc[manifest.split.eq('validation'), 'pair_id']].reset_index()
    dictionary = m.build_dictionary(root, train_data)
    extract = m.make_extractor(dictionary)
    documents = sorted(set(train_data.resume_text.map(m.normalized)) | set(train_data.job_text.map(m.normalized)))
    vectorizer = TfidfVectorizer(token_pattern=r'(?u)(?<!\w)(?:\.net\b|[\w]+(?:[+#]+|(?:\.[\w]+)*))', lowercase=False)
    vectorizer.fit(documents)
    x = m.features(train_data, vectorizer, extract)[m.FEATURES]
    xv = m.features(validation, vectorizer, extract)[m.FEATURES]
    model, selected, scores, trials = search_logistic(x, train_data.training_label, xv, validation.training_label)
    rows = [selected]
    predictions = validation[['pair_id', 'training_label', 'label_source', 'sampling_domain']].copy()
    predictions['logistic_regression_score'] = scores
    predictions['logistic_regression_prediction'] = (scores >= selected['threshold']).astype(int)
    majority = int(train_data.training_label.value_counts().sort_index().idxmax())
    baseline_scores = {'majority': np.full(len(validation), majority), 'tfidf_threshold': xv.tfidf_cosine.to_numpy(), 'skill_threshold': xv.job_skill_coverage.to_numpy()}
    for name, values in baseline_scores.items():
        candidates = [{'name': name, 'settings': {'training_majority': majority} if name == 'majority' else {}, 'threshold': threshold,
                       **m.metrics(validation.training_label, values >= threshold)}
                      for threshold in ([.5] if name == 'majority' else BASELINE_GRID)]
        trials.extend(candidates)
        row = min(candidates, key=lambda item: (-item['macro_f1'], abs(item['threshold'] - .5), item['threshold']))
        rows.append(row)
        predictions[name + '_prediction'] = (values >= row['threshold']).astype(int)
    m.check_fingerprints(root, fingerprints)
    # Reserve all folders exclusively before writing any model artifacts.
    for folder in destinations:
        folder.mkdir(parents=True, exist_ok=False)
    processed, models, reports = destinations
    shutil.copyfile(source_manifest, processed / 'split_manifest.csv')
    for name, frame, table in [('train', train_data, x), ('validation', validation, xv)]:
        pd.concat([frame[['pair_id', 'training_label']], table], axis=1).to_csv(processed / f'{name}_features.csv', index=False)
    m.write_json(processed / 'input_fingerprints.json', fingerprints)
    joblib.dump(vectorizer, models / 'tfidf_vectorizer.joblib')
    joblib.dump(model, models / 'logistic_regression.joblib')
    m.write_json(models / 'dictionary.json', {'skills': dictionary, 'aliases': m.ALIASES, 'origin': 'Supplied raw skill lists restricted to training IDs, project generic-term filter and fixed technology aliases'})
    definitions = json.loads((root / 'models/milestone3/v2/feature_definitions.json').read_text(encoding='utf8'))
    definitions['training_unique_documents'] = len(documents)
    m.write_json(models / 'feature_definitions.json', definitions)
    selection = {'model': m.CLASSIFIER, 'settings': selected['settings'], 'threshold': selected['threshold'], 'rule': 'score >= threshold predicts suitable', 'refit_on_train_plus_validation': False}
    m.write_json(models / 'selection.json', selection)
    pd.DataFrame(rows).to_csv(reports / 'validation_comparison.csv', index=False)
    predictions.to_csv(reports / 'validation_predictions.csv', index=False)
    m.write_json(reports / 'search.json', {'seed': m.SEED, 'C_grid': C_GRID, 'probability_grid': PROBABILITY_GRID, 'baseline_grid': BASELINE_GRID, 'tie_breaking': 'Validation macro F1, lower C, threshold closest to .5, then lower threshold; baselines use macro F1, distance to .5, then lower threshold', 'trials': trials})
    m.write_json(reports / 'versions.json', versions)
    shutil.copyfile(root / 'reports/milestone3/v2/split_audit.json', reports / 'split_audit.json')
    loaded = joblib.load(models / 'logistic_regression.joblib')
    np.testing.assert_allclose(loaded.predict_proba(xv)[:, list(loaded.classes_).index(1)], scores, rtol=0, atol=0)
    m.check_fingerprints(root, fingerprints)
    hashes = {path.relative_to(root).as_posix(): m.digest(path) for folder in destinations for path in folder.iterdir() if path.is_file()}
    m.write_json(reports / 'completed.json', {'fingerprints': fingerprints, 'artifacts': hashes, 'selection': selection})
    return selection


def main():
    parser = argparse.ArgumentParser(description='Intentionally reproduce Logistic Regression training using the reviewed v2 assignments. Never evaluates test.')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output-version', required=True, help='Unused numbered version; existing folders are refused')
    args = parser.parse_args()
    print(json.dumps(train(args.root, output_version=args.output_version), indent=2))


if __name__ == '__main__':
    main()
