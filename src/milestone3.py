"""Reuse the saved Logistic Regression and reference baselines; test stays reserved."""
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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SEED = 42
FEATURES = ['tfidf_cosine', 'job_skill_coverage', 'missing_job_skill_count', 'no_job_skills']
ALIASES = {'js': 'javascript', 'nodejs': 'node.js', 'node js': 'node.js', 'dotnet': '.net', 'csharp': 'c#', 'c sharp': 'c#', 'cpp': 'c++'}
CLASSIFIER = 'logistic_regression'
CLASSIFICATION_THRESHOLD = 0.5
REFERENCE_NAMES = [CLASSIFIER, 'majority', 'tfidf_threshold', 'skill_threshold']
REVIEWED_V2_MARKER = '0553fa4eceda3fc00b3733bd7f3c09be5c0c30d5ac2eaae667f5c071703f2a30'


def package_versions():
    return {'python': platform.python_version(), **{p: importlib.metadata.version(p) for p in ['numpy', 'pandas', 'scikit-learn', 'scipy', 'joblib', 'spacy', 'nbclient', 'nbformat']}}


def capture_fingerprints(root):
    paths = ['data/labeled/suitability_review_master_v1.csv',
             'data/labeled/suitability_development_labels_v1.csv',
             'data/raw/cv.csv', 'data/raw/job.csv',
             'src/milestone3.py', 'src/skill_extraction.py']
    return {p: digest(root / p) for p in paths}


def check_fingerprints(root, original):
    for name, expected in original.items():
        path = root / name
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError(f'Fingerprint changed during execution: {name}; run not completed.')


def load_completed(root, version, fingerprints, versions, reviewed=False):
    marker = root / 'reports/milestone3' / version / 'completed.json'
    if not marker.is_file():
        raise RuntimeError(f'Cannot reuse {version}: missing {marker.relative_to(root)}')
    if reviewed and (version != 'v2' or digest(marker) != REVIEWED_V2_MARKER):
        raise RuntimeError(f'Cannot reuse {version}: reviewed v2 completion metadata hash mismatch')
    recorded = json.loads(marker.read_text(encoding='utf8'))
    original = {k.replace('\\', '/'): v for k, v in recorded['fingerprints'].items()}
    required = [p for p in fingerprints if p.startswith('data/')] if reviewed else list(fingerprints)
    for name in required:
        if original.get(name) != fingerprints[name]:
            raise RuntimeError(f'Cannot reuse {version}: fingerprint mismatch for {name}')
    artifacts = recorded.get('artifacts', {})
    required_artifacts = [f'reports/milestone3/{version}/{name}' for name in ['validation_comparison.csv', 'split_audit.json', 'versions.json']]
    required_artifacts.append(f'models/milestone3/{version}/selection.json')
    normalized_artifacts = {p.replace('\\', '/'): h for p, h in artifacts.items()}
    for name in required_artifacts:
        if name not in normalized_artifacts:
            raise RuntimeError(f'Cannot reuse {version}: missing recorded artifact hash for {name}')
    for name, expected in normalized_artifacts.items():
        path = root / name
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError(f'Cannot reuse {version}: artifact hash mismatch for {name}')
    reports = root / 'reports/milestone3' / version
    saved_versions = json.loads((reports / 'versions.json').read_text(encoding='utf8'))
    for name in sorted(set(saved_versions) | set(versions)):
        if saved_versions.get(name) != versions.get(name):
            raise RuntimeError(f'Cannot reuse {version}: package version mismatch for {name}: saved={saved_versions.get(name)}, current={versions.get(name)}')
    comparison = pd.read_csv(reports / 'validation_comparison.csv')
    audit = json.loads((reports / 'split_audit.json').read_text(encoding='utf8'))
    selection = json.loads((root / 'models/milestone3' / version / 'selection.json').read_text(encoding='utf8'))
    if selection != recorded['selection']:
        raise RuntimeError(f'Cannot reuse {version}: selection differs from completion metadata')
    # Recheck after loading, so a concurrent edit cannot produce a successful return.
    for name, expected in normalized_artifacts.items():
        if digest(root / name) != expected:
            raise RuntimeError(f'Cannot reuse {version}: artifact changed while loading: {name}')
    check_fingerprints(root, fingerprints)
    provenance = 'existing reviewed v2 results; original training provenance preserved' if reviewed else 'matching source and package fingerprints'
    print(f'Reused {version}: {provenance}. Current consumer-code SHA256: {fingerprints["src/milestone3.py"]}')
    return comparison, audit, selection


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


def make_extractor(dictionary, aliases=None):
    aliases = ALIASES if aliases is None else aliases
    # Longest alternatives prevent C matching the prefix of C++ or C#.
    terms = set(dictionary) | set(aliases)
    pattern = re.compile(r'(?<![\w.+#])(?:' + '|'.join(re.escape(s) for s in sorted(terms, key=lambda s: (-len(s), s))) + r')(?![\w+#]|\.\w)', re.IGNORECASE)
    def extract(text):
        return {aliases.get(normalized(m.group()), normalized(m.group())) for m in pattern.finditer(normalized(text))}
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


def run(root, *, reuse_version='v2', allow_training=False):
    """Reuse one trained classifier and three saved baseline measurements."""
    root = Path(root)
    fingerprints = capture_fingerprints(root)
    versions = package_versions()
    if allow_training or reuse_version is None:
        raise RuntimeError('Training is disabled; load an existing Logistic Regression run.')
    if not re.fullmatch(r'v[1-9][0-9]*', reuse_version):
        raise ValueError('reuse_version must be a numbered version such as v2')
    comparison, audit, selection = load_completed(
        root, reuse_version, fingerprints, versions, reviewed=reuse_version == 'v2')
    if (selection['model'] != CLASSIFIER or selection['settings'] != {'C': 10.0}
            or selection['threshold'] != CLASSIFICATION_THRESHOLD):
        raise RuntimeError('Saved selection must be Logistic Regression with C=10 and threshold 0.5')
    active = comparison[comparison['name'].isin(REFERENCE_NAMES)].copy().reset_index(drop=True)
    if sorted(active['name']) != sorted(REFERENCE_NAMES):
        raise RuntimeError('Saved results must contain Logistic Regression and all three reference baselines')
    active.attrs['source_version'] = reuse_version
    active.attrs['classifier'] = CLASSIFIER
    check_fingerprints(root, fingerprints)
    return active, audit, selection


def load_logistic_regression(root, *, reuse_version='v2'):
    """Return the verified classifier for future exports and inference."""
    root = Path(root)
    fingerprints = capture_fingerprints(root)
    run(root, reuse_version=reuse_version)
    path = root / 'models/milestone3' / reuse_version / 'logistic_regression.joblib'
    recorded = json.loads((root / 'reports/milestone3' / reuse_version / 'completed.json').read_text(encoding='utf8'))
    hashes = {name.replace('\\', '/'): value for name, value in recorded['artifacts'].items()}
    expected = hashes[path.relative_to(root).as_posix()]
    if digest(path) != expected:
        raise RuntimeError('Logistic Regression artifact hash mismatch before loading')
    model = joblib.load(path)
    if (not isinstance(model, Pipeline) or len(model.steps) != 2
            or not isinstance(model[0], StandardScaler)
            or not isinstance(model[1], LogisticRegression)
            or model[1].C != 10.0 or model[1].class_weight != 'balanced'
            or list(model.feature_names_in_) != FEATURES):
        raise RuntimeError('Saved pipeline must be StandardScaler and balanced Logistic Regression with C=10 in the declared feature order')
    if digest(path) != expected:
        raise RuntimeError('Logistic Regression artifact changed while loading')
    check_fingerprints(root, fingerprints)
    return model
