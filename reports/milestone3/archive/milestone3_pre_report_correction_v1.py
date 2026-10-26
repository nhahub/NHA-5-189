"""Reproducible preliminary training; the test partition is reserved."""
from pathlib import Path
import hashlib
import importlib.metadata
import itertools
import json
import platform
import re

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 42
FEATURES = ['tfidf_cosine', 'job_skill_coverage', 'missing_job_skill_count', 'no_job_skills']
ALIASES = {'js': 'javascript', 'nodejs': 'node.js', 'node js': 'node.js', 'dotnet': '.net', 'csharp': 'c#', 'c sharp': 'c#', 'cpp': 'c++'}
PROB_GRID = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
BASE_GRID = [i / 10 for i in range(11)]


def normalized(text):
    return ' '.join(str(text).casefold().split())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf8')


def validate(root):
    paths = [root / 'data/labeled' / f'suitability_{name}_v1.csv' for name in ['review_master', 'development_labels']]
    master, data = [pd.read_csv(p, dtype=str, keep_default_na=False) for p in paths]
    shared = ['pair_id', 'candidate_id', 'job_id', 'resume_text', 'job_title', 'job_text', 'sampling_domain']
    for name, frame in [('master', master), ('development', data)]:
        required = shared + (['training_label', 'label_source'] if name == 'development' else ['label_1', 'final_label', 'suggested_label'])
        if set(required) - set(frame):
            raise ValueError(f'Missing columns in {name}: {set(required) - set(frame)}')
        if frame[shared].apply(lambda c: c.str.strip().eq('').any()).any():
            raise ValueError(f'Empty identifier, text or metadata in {name}')
        if frame.pair_id.duplicated().any() or frame.duplicated(['candidate_id', 'job_id']).any():
            raise ValueError(f'Duplicate pairs in {name}')
        if not frame.pair_id.eq(frame.candidate_id + ':' + frame.job_id).all():
            raise ValueError(f'Inconsistent pair IDs in {name}')
        for ident, text in [('candidate_id', 'resume_text'), ('job_id', 'job_text')]:
            if frame.assign(document=frame[text].map(normalized)).groupby(ident).document.nunique().gt(1).any():
                raise ValueError(f'Conflicting documents for {ident}')
    if not data.training_label.isin(['0', '1']).all():
        raise ValueError('Nonbinary development labels')
    recognized = ['existing_final_label', 'recorded_first_review', 'automated_annotation']
    if not data.label_source.isin(recognized).all():
        raise ValueError('Unrecognized label source')
    expected = master.set_index('pair_id').loc[data.pair_id]
    if not data.set_index('pair_id')[shared[1:]].equals(expected[shared[1:]]):
        raise ValueError('Development documents or metadata differ from master')
    for source, column in zip(recognized, ['final_label', 'label_1', 'suggested_label']):
        subset = data.label_source.eq(source).to_numpy()
        if not np.array_equal(data.training_label.to_numpy()[subset], expected[column].to_numpy()[subset]):
            raise ValueError(f'Labels conflict with master provenance: {source}')
    data['training_label'] = data.training_label.astype(int)
    summary = {'master_pairs': len(master), 'development_pairs': len(data), 'labels': data.training_label.value_counts().to_dict(), 'label_sources': data.label_source.value_counts().to_dict()}
    summary['duplicate_documents_under_multiple_ids'] = {}
    for ident, text in [('candidate_id', 'resume_text'), ('job_id', 'job_text')]:
        summary['duplicate_documents_under_multiple_ids'][ident] = int(master.assign(document=master[text].map(normalized)).groupby('document')[ident].nunique().gt(1).sum())
    print(json.dumps(summary, indent=2))
    return master, data, paths, summary


def components(data, strict):
    parent = list(range(len(data)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    columns = ['candidate_id', 'resume_text'] + (['job_id', 'job_text'] if strict else [])
    for col in columns:
        seen = {}
        for i, value in enumerate(data[col]):
            key = normalized(value) if col.endswith('text') else value
            if key in seen:
                parent[find(i)] = find(seen[key])
            seen[key] = i
    return np.array([find(i) for i in range(len(data))])


def choose_split(data, groups):
    """Search uses only group size and class balance, never features or models."""
    unique = np.unique(groups)
    if len(unique) < 3:
        return None
    rng = np.random.RandomState(SEED)
    target = np.array([.6, .2, .2])
    best = None
    y = data.training_label.to_numpy()
    for _ in range(20000):
        assignment = rng.choice(3, len(unique), p=target)
        split = assignment[np.searchsorted(unique, groups)]
        counts = np.array([[np.sum((split == s) & (y == c)) for c in [0, 1]] for s in range(3)])
        sizes = counts.sum(axis=1)
        if (counts == 0).any() or np.any(np.abs(sizes / len(data) - target) > .12):
            continue
        loss = np.sum((sizes / len(data) - target) ** 2) + np.sum((counts / np.bincount(y) - target[:, None]) ** 2)
        if best is None or loss < best[0]:
            best = (loss, split.copy())
    return None if best is None else best[1]


def split_data(data):
    strict_groups = components(data, True)
    split = choose_split(data, strict_groups)
    strict = split is not None
    if split is None:
        split = choose_split(data, components(data, False))
    if split is None:
        raise ValueError('No useful candidate/resume-disjoint split with both classes')
    data = data.copy()
    data['split'] = np.array(['train', 'validation', 'test'])[split]
    audit = {'seed': SEED, 'strict_component_sizes': pd.Series(strict_groups).value_counts().tolist(), 'strict_separation_used': strict,
             'selection_rule': '20000 seeded group allocations; both classes; size deviation <= 12 percentage points; minimize squared size and class-allocation deviations',
             'scope': 'Unseen resumes and jobs' if strict else 'Unseen candidates against potentially familiar jobs; full document separation is not achieved',
             'counts': pd.crosstab(data.split, data.training_label).to_dict(orient='index'),
             'domains': pd.crosstab(data.split, data.sampling_domain).to_dict(orient='index'), 'overlap': {}}
    for col in ['candidate_id', 'resume_text', 'job_id', 'job_text']:
        sets = {s: set(data.loc[data.split.eq(s), col].map(normalized) if col.endswith('text') else data.loc[data.split.eq(s), col]) for s in ['train', 'validation', 'test']}
        audit['overlap'][col] = {f'{a}/{b}': len(sets[a] & sets[b]) for a, b in itertools.combinations(sets, 2)}
    assert not any(audit['overlap'][c][k] for c in ['candidate_id', 'resume_text'] for k in audit['overlap'][c])
    assert data.pair_id.is_unique
    return data, audit


def build_dictionary(root, train):
    """Reuse supplied skill lists, restricted to training document identities."""
    from src.skill_extraction import optimize_skill_dictionary
    skills = set()
    for filename, ident in [('cv.csv', 'candidate_id'), ('job.csv', 'job_id')]:
        raw = pd.read_csv(root / 'data/raw' / filename, usecols=[ident, 'clean_skills'], dtype=str, keep_default_na=False)
        for value in raw.loc[raw[ident].isin(train[ident]), 'clean_skills']:
            import ast
            parsed = ast.literal_eval(value)
            if not isinstance(parsed, list) or not all(isinstance(s, str) for s in parsed):
                raise ValueError('Expected serialized skill lists')
            skills.update(normalized(s) for s in parsed if s.strip())
    skills = optimize_skill_dictionary(sorted(skills))
    return sorted({ALIASES.get(s, s) for s in skills} | {'c', 'c++', 'c#', 'java', 'javascript', '.net', 'node.js'})


def make_extractor(dictionary):
    # Longest alternatives prevent C matching the prefix of C++ or C#.
    terms = set(dictionary) | set(ALIASES)
    pattern = re.compile(r'(?<![\w.+#])(?:' + '|'.join(re.escape(s) for s in sorted(terms, key=lambda s: (-len(s), s))) + r')(?![\w+#]|\.\w)', re.IGNORECASE)
    def extract(text):
        return {ALIASES.get(normalized(m.group()), normalized(m.group())) for m in pattern.finditer(normalized(text))}
    return extract


def skill_features(resume, job):
    return [len(resume & job) / len(job) if job else 0., len(job - resume), int(not job)]


def check_skills():
    extract = make_extractor(['c', 'c++', 'c#', 'java', 'javascript', '.net', 'node.js'])
    assert extract('JS JavaScript') == {'javascript'}
    for term in ['c', 'c++', 'c#', 'java', 'javascript', '.net', 'node.js']:
        assert extract(term) == {term}, term
    assert extract('JavaScript') == {'javascript'}
    assert extract('scar javascripted node.json') == set()
    assert skill_features({'python'}, set()) == [0., 0, 1]


def features(frame, vectorizer, extract):
    resumes = frame.resume_text.map(normalized)
    jobs = frame.job_text.map(normalized)
    similarity = np.asarray(vectorizer.transform(resumes).multiply(vectorizer.transform(jobs)).sum(axis=1)).ravel()
    rows = [[score] + skill_features(extract(r), extract(j)) for score, r, j in zip(similarity, resumes, jobs)]
    return pd.DataFrame(rows, columns=FEATURES, index=frame.index)


def metrics(y, pred):
    p, r, f, support = precision_recall_fscore_support(y, pred, labels=[0, 1], zero_division=0)
    result = {'macro_f1': float(np.mean(f)), 'accuracy': float(accuracy_score(y, pred)), 'confusion_matrix': confusion_matrix(y, pred, labels=[0, 1]).tolist()}
    for i, label in enumerate(['unsuitable', 'suitable']):
        result.update({f'{label}_{name}': float(values[i]) if name != 'support' else int(values[i]) for name, values in [('precision', p), ('recall', r), ('f1', f), ('support', support)]})
    return result


def train_models(x, y, xv, yv):
    selected, search = {}, []
    families = {
        'logistic_regression': [{'C': c} for c in [.1, 1., 10.]],
        'random_forest': [{'n_estimators': 100, 'max_depth': depth, 'min_samples_leaf': leaf} for depth in [2, 4] for leaf in [4, 2]],
    }
    for family, configs in families.items():
        candidates = []
        for simplicity, config in enumerate(configs):
            estimator = LogisticRegression(**config, class_weight='balanced', random_state=SEED, max_iter=2000) if family == 'logistic_regression' else RandomForestClassifier(**config, class_weight='balanced', random_state=SEED, n_jobs=1)
            model = make_pipeline(StandardScaler(), estimator) if family == 'logistic_regression' else make_pipeline(estimator)
            model.fit(x, y)
            scores = model.predict_proba(xv)[:, 1]
            for threshold in PROB_GRID:
                row = {'name': family, 'settings': config, 'threshold': threshold, **metrics(yv, scores >= threshold)}
                search.append(row)
                candidates.append(((-row['macro_f1'], simplicity, abs(threshold - .5), threshold), model, row, scores))
        _, model, row, scores = min(candidates, key=lambda c: c[0])
        selected[family] = (model, row, scores)
    return selected, search


def run(root):
    root = Path(root)
    master, data, inputs, summary = validate(root)
    check_skills()
    data, audit = split_data(data)
    print(json.dumps(audit, indent=2))
    train = data[data.split.eq('train')]
    validation = data[data.split.eq('validation')]
    dictionary = build_dictionary(root, train)
    extract = make_extractor(dictionary)
    documents = sorted(set(train.resume_text.map(normalized)) | set(train.job_text.map(normalized)))
    vectorizer = TfidfVectorizer(token_pattern=r'(?u)(?<!\w)(?:\.net\b|[\w]+(?:[+#]+|(?:\.[\w]+)*))', lowercase=False)
    vectorizer.fit(documents)
    x, xv = features(train, vectorizer, extract), features(validation, vectorizer, extract)
    selected, search = train_models(x, train.training_label, xv, validation.training_label)
    rows = [value[1] for value in selected.values()]
    majority = int(train.training_label.value_counts().sort_index().idxmax())
    baseline_scores = {'majority': np.full(len(validation), majority), 'tfidf_threshold': xv.tfidf_cosine.to_numpy(), 'skill_threshold': xv.job_skill_coverage.to_numpy()}
    predictions = validation[['pair_id', 'training_label', 'label_source', 'sampling_domain']].copy()
    for name, (_, row, scores) in selected.items():
        predictions[name + '_score'] = scores
        predictions[name + '_prediction'] = (scores >= row['threshold']).astype(int)
    for name, scores in baseline_scores.items():
        candidates = [{'name': name, 'settings': {'training_majority': majority} if name == 'majority' else {}, 'threshold': t, **metrics(validation.training_label, scores >= t)} for t in ([.5] if name == 'majority' else BASE_GRID)]
        search.extend(candidates)
        row = min(candidates, key=lambda r: (-r['macro_f1'], abs(r['threshold'] - .5), r['threshold']))
        rows.append(row)
        predictions[name + '_prediction'] = (scores >= row['threshold']).astype(int)
    winner = min(selected, key=lambda name: (-selected[name][1]['macro_f1'], name != 'logistic_regression'))
    fingerprints = {str(p.relative_to(root)): digest(p) for p in inputs}
    fingerprints.update({f'data/raw/{name}': digest(root / 'data/raw' / name) for name in ['cv.csv', 'job.csv']})
    fingerprints['implementation'] = digest(Path(__file__))
    # Reuse only a complete, byte-identical run; never replace an earlier version.
    bases = [root / p / 'milestone3' for p in ['data/processed', 'models', 'reports']]
    version = 1
    while any((b / f'v{version}').exists() for b in bases):
        marker = bases[2] / f'v{version}' / 'completed.json'
        if marker.exists() and json.loads(marker.read_text())['fingerprints'] == fingerprints:
            recorded = json.loads(marker.read_text())
            if all((root / p).is_file() and digest(root / p) == h for p, h in recorded['artifacts'].items()):
                print(f'Reusing verified identical artifacts v{version}')
                return pd.DataFrame(rows), audit, recorded['selection']
        version += 1
    processed, models, reports = [b / f'v{version}' for b in bases]
    for directory in [processed, models, reports]:
        directory.mkdir(parents=True, exist_ok=False)
    manifest = data[['pair_id', 'split', 'training_label', 'label_source', 'sampling_domain']]
    manifest.to_csv(processed / 'split_manifest.csv', index=False)
    write_json(processed / 'input_fingerprints.json', fingerprints)
    write_json(reports / 'split_audit.json', audit)
    for name, frame, table in [('train', train, x), ('validation', validation, xv)]:
        pd.concat([frame[['pair_id', 'training_label']].reset_index(drop=True), table.reset_index(drop=True)], axis=1).to_csv(processed / f'{name}_features.csv', index=False)
    joblib.dump(vectorizer, models / 'tfidf_vectorizer.joblib')
    write_json(models / 'dictionary.json', {'skills': dictionary, 'aliases': ALIASES, 'origin': 'Supplied raw clean_skills lists for training IDs only; existing project generic-term filter; explicit fixed technology terms and aliases. No genuine technical/soft category taxonomy is supplied.'})
    definitions = {'feature_order': FEATURES, 'definitions': {'tfidf_cosine': 'Cosine in L2-normalized training-only TF-IDF space', 'job_skill_coverage': 'Matched unique normalized skills / unique mentioned job skills; zero if empty', 'missing_job_skill_count': 'Unique mentioned job skills absent from resume', 'no_job_skills': '1 for unavailable skill evidence, not a confirmed zero match'}, 'training_unique_documents': len(documents), 'normalization': 'Casefold and whitespace only; punctuation retained', 'artifact_status': {'vectorizer': 'derived from unique training documents', 'dictionary': 'derived from supplied training-ID skill lists with fixed aliases/filter', 'models_and_scaler': 'trained on training pairs only', 'thresholds_and_hyperparameters': 'selected on validation only', 'split': 'derived from group structure and labels only', 'aliases_and_feature_definitions': 'fixed in advance'}}
    write_json(models / 'feature_definitions.json', definitions)
    for name, (model, row, scores) in selected.items():
        joblib.dump(model, models / f'{name}.joblib')
        loaded = joblib.load(models / f'{name}.joblib')
        assert list(loaded.feature_names_in_) == FEATURES
        np.testing.assert_allclose(loaded.predict_proba(xv)[:, 1], scores, rtol=0, atol=0)
    loaded_vectorizer = joblib.load(models / 'tfidf_vectorizer.joblib')
    loaded_dictionary = json.loads((models / 'dictionary.json').read_text())
    pd.testing.assert_frame_equal(features(validation, loaded_vectorizer, make_extractor(loaded_dictionary['skills'])), xv)
    assert selected['logistic_regression'][0][0].n_samples_seen_ == len(train)
    assert set(vectorizer.vocabulary_) == set(TfidfVectorizer(**vectorizer.get_params()).fit(documents).vocabulary_)
    comparison = pd.DataFrame(rows)
    comparison.to_csv(reports / 'validation_comparison.csv', index=False)
    predictions.to_csv(reports / 'validation_predictions.csv', index=False)
    selection = {'model': winner, 'settings': selected[winner][1]['settings'], 'threshold': selected[winner][1]['threshold'], 'rule': 'score >= threshold predicts suitable', 'refit_on_train_plus_validation': False}
    write_json(models / 'selection.json', selection)
    write_json(reports / 'search.json', {'seed': SEED, 'probability_grid': PROB_GRID, 'baseline_grid': BASE_GRID, 'tie_breaking': 'Macro F1, simpler settings (lower C; shallower forest then larger leaf), threshold nearest .5 then lower threshold; Logistic Regression wins family ties', 'trials': search})
    write_json(reports / 'versions.json', {'python': platform.python_version(), **{p: importlib.metadata.version(p) for p in ['numpy', 'pandas', 'scikit-learn', 'scipy', 'joblib', 'spacy', 'nbclient', 'nbformat']}})
    it = data[(data.sampling_domain == 'INFORMATION-TECHNOLOGY') & data.training_label.eq(1)]
    concentration = it.groupby(['job_id', 'job_title']).size().to_string()
    better = comparison.loc[comparison.macro_f1 > selected[winner][1]['macro_f1'], 'name'].tolist()
    report = f'''# Milestone 3: training and validation, v{version}

The master contains {len(master)} pairs. Development contains {len(data)} pairs: {int(data.training_label.sum())} suitable and {int((data.training_label == 0).sum())} unsuitable. There are three recorded first reviews and 46 automated annotations. Independent human verification was not performed. These results measure agreement with annotations, not verified suitability or hiring probabilities.

## Splits

Seed: {SEED}. The search uses only group integrity, sizes and labels. A useful split requires both classes and sizes within 12 percentage points of 60/20/20. Strict connected-component sizes are {audit['strict_component_sizes']}. Strict separation feasible under this rule: {audit['strict_separation_used']}. Scope: {audit['scope']}.

Counts (columns 0 = unsuitable, 1 = suitable):
{pd.crosstab(data.split, data.training_label).to_string()}

Overlap counts, measured on IDs and case/whitespace-normalized text:
{json.dumps(audit['overlap'], indent=2)}

Domain counts:
{pd.crosstab(data.split, data.sampling_domain).to_string()}

## Features and training

Feature order: {', '.join(FEATURES)}. TF-IDF is fitted on {len(documents)} unique normalized training documents only. Validation uses transform only. The dictionary uses supplied skill lists restricted to training candidate/job IDs and the existing generic-term filter, with fixed technology aliases. The earlier spaCy extractor uses case-sensitive phrase patterns; this workflow uses punctuation-aware boundaries and longest-first matching to preserve technology distinctions. There is no supported technical/soft-skill taxonomy, so coverage is overall coverage. Extracted job skills are mentioned skills, not necessarily essential requirements. An empty job-skill set gives zero coverage, zero missing skills and indicator one: unavailable skill evidence.

Logistic Regression uses StandardScaler fitted on training rows. Random Forest uses no scaling. Both use balanced class weights and seed {SEED}. Only the four declared features enter the models; tracing metadata stays separate. Thresholds use score >= threshold. Macro F1 selects settings and thresholds on validation. Tie-breaking favors lower C or shallower forests/larger leaves, then thresholds nearest 0.5 (then lower); Logistic Regression wins a trained-family tie. No training-plus-validation refit occurs.

## Validation results

{comparison.to_string(index=False)}

Selected trained model: {json.dumps(selection)}. Baselines scoring strictly higher: {better or 'none'}. The CSV comparison contains class precision, recall, F1, support, accuracy and confusion matrices, with rows actual and columns predicted in order [unsuitable, suitable].

## Limits and checks

Only 49 labeled pairs and class imbalance make validation tuning unstable. Sales has no suitable examples. All {len(it)} suitable IT examples share the same help-desk job:
{concentration}

Job overlap and uneven domain coverage limit conclusions. Familiar job content and annotation patterns may dominate the comparison. A held-out test is still required. Milestone 3 remains in progress.

Checks passed: identifier and provenance validation; master/development document equality; duplicate-document audit; candidate/resume separation; both classes in every split; technology normalization and empty-skill checks; training-only TF-IDF and scaling; exact feature order; artifact reload reproducing validation features and probabilities. Test documents are used only for split integrity auditing, never feature construction, preprocessing fitting, predictions or performance metrics. No test feature tables or predictions were produced. Input file hashes were checked unchanged at the end of the run.
'''
    (reports / 'training_validation_report.md').write_text(report, encoding='utf8')
    for p in inputs:
        assert digest(p) == fingerprints[str(p.relative_to(root))]
    for name in ['cv.csv', 'job.csv']:
        assert digest(root / 'data/raw' / name) == fingerprints[f'data/raw/{name}']
    artifacts = {str(p.relative_to(root)): digest(p) for folder in [processed, models, reports] for p in folder.iterdir() if p.is_file()}
    write_json(reports / 'completed.json', {'fingerprints': fingerprints, 'artifacts': artifacts, 'selection': selection})
    print(f'Artifacts saved as v{version}; reload checks passed; test remains reserved.')
    return comparison, audit, selection
