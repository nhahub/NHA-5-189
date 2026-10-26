"""Explicit frozen-model export; private parity references travel over stdout only."""
import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import platform
import sys
import unicodedata

import numpy as np
import pandas as pd

from src import milestone3 as m
from src import milestone3_evaluation as e


def unicode_behavior():
    ranges, start, end = [], None, None
    fold, whitespace = {}, []
    for number in range(sys.maxunicode + 1):
        char = chr(number)
        if char.casefold() != char:
            fold[char] = char.casefold()
        if char.isspace():
            whitespace.append(number)
        word = char.isalnum() or char == '_'
        if word:
            if start is None:
                start = number
            end = number
        elif start is not None:
            ranges.append([start, end]); start = None
    if start is not None:
        ranges.append([start, end])
    return {'unicode_version': unicodedata.unidata_version, 'casefold': fold,
            'whitespace_codepoints': whitespace, 'word_ranges': ranges,
            'normalization': 'Python casefold followed by whitespace splitting and single-space joining; punctuation preserved; no NFC/NFKC',
            'extraction': 'Longest-first escaped skill/alias alternatives; Python word boundaries; Unicode IGNORECASE after casefold; matched substrings normalized then aliased',
            'unsupported': ['Unpaired UTF-16 surrogates are rejected. Inputs must be strings, not byte buffers.']}


def export(root):
    root = Path(root).resolve()
    before = e.snapshot(root)
    before['src/milestone3_export.py'] = m.digest(Path(__file__))
    assets = e.load_assets(root)
    model = assets['model']; scaler, classifier = model[0], model[1]
    vectorizer = assets['vectorizer']
    params = vectorizer.get_params()
    settings = {key: value for key, value in params.items() if key not in ['dtype', 'vocabulary']}
    settings['dtype'] = np.dtype(params['dtype']).name
    dictionary = json.loads((root / 'models/milestone3/v2/dictionary.json').read_text(encoding='utf8'))
    payload = {'schema_version': 1, 'model_version': 'milestone3/v2',
               'source_artifact_hashes': before, 'runtime_versions': {**m.package_versions(), 'unicode': unicodedata.unidata_version},
               'feature_order': assets['feature_order'], 'threshold': assets['threshold'],
               'classifier': {'type': 'LogisticRegression', 'C': float(classifier.C), 'class_weight': classifier.class_weight,
                              'coefficients': classifier.coef_.tolist(), 'intercept': classifier.intercept_.tolist(),
                              'classes': [int(v) for v in model.classes_], 'positive_class': 1,
                              'positive_class_index': assets['positive_index']},
               'scaler': {'mean': scaler.mean_.tolist(), 'scale': scaler.scale_.tolist(), 'with_mean': scaler.with_mean, 'with_std': scaler.with_std},
               'tfidf': {'vocabulary': {k: int(v) for k, v in vectorizer.vocabulary_.items()}, 'idf': vectorizer.idf_.tolist(), 'settings': settings},
               'dictionary': dictionary, 'text_behavior': unicode_behavior()}
    # Verify the exported analyzer contract rather than silently approximating it.
    expected_pattern = r'(?u)(?<!\w)(?:\.net\b|[\w]+(?:[+#]+|(?:\.[\w]+)*))'
    if (settings['token_pattern'] != expected_pattern or settings['ngram_range'] != (1, 1)
            or settings['analyzer'] != 'word' or settings['lowercase'] or settings['strip_accents'] is not None
            or settings['stop_words'] is not None or settings['norm'] != 'l2'
            or not settings['use_idf'] or settings['binary'] or settings['sublinear_tf']):
        raise RuntimeError('Saved TF-IDF analyzer is not supported by this export schema')
    encoded = json.dumps(payload, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(',', ':')).encode('utf8')
    base = root / 'models/browser'; version = 1
    while (base / f'v{version}').exists():
        folder = base / f'v{version}'
        path = folder / 'assets.json'; marker = folder / 'completed.json'
        if marker.is_file():
            saved = json.loads(marker.read_text(encoding='utf8'))
            if saved['source_fingerprints'] == before and saved['runtime_versions'] == payload['runtime_versions']:
                if not path.is_file() or m.digest(path) != saved['assets_sha256']:
                    raise RuntimeError(f'Existing browser export hash mismatch: {path}')
                if path.read_bytes() != encoded:
                    raise RuntimeError('Matching export fingerprints produced different JSON')
                m.check_fingerprints(root, before)
                print(f'Reused verified browser export v{version}')
                return folder
        version += 1
    folder = base / f'v{version}'; folder.mkdir(parents=True, exist_ok=False)
    (folder / 'assets.json').write_bytes(encoded)
    m.check_fingerprints(root, before)
    e.strict_json(folder / 'completed.json', {'source_fingerprints': before, 'runtime_versions': payload['runtime_versions'], 'assets_sha256': m.digest(folder / 'assets.json')})
    print(f'Exported browser assets v{version}: {len(encoded)} bytes')
    return folder


def references(root):
    """Return private validation documents in memory; never write reference files."""
    root = Path(root).resolve(); assets = e.load_assets(root)
    cases = [
        ('normal', 'Python and JS applications.', 'Python, JavaScript, SQL and Node.js.'),
        ('technologies', 'C C++ C# Java JavaScript .NET Node.js', 'C C++ C# Java JavaScript .NET Node.js SQL'),
        ('aliases', 'JS nodejs dotnet csharp cpp', 'JavaScript Node.js .NET C# C++'),
        ('mixed', '  PYTHON\tJS\nSQL  ', ' python \r\n JavaScript SQL '),
        ('unicode', 'Straße İ ı K ſ PYTHON\u00a0JS\u001c.NET', 'STRASSE i ı K s Python\u2003JavaScript .NET'),
        ('unicode_words', 'café العربية 中文 ² Ⅳ \U0001f680 e\u0301 SQL', 'CAFÉ العربية 中文 ² Ⅳ e\u0301 Python'),
        ('dotless_i', 'ınformatıon technology', 'information technology'),
        ('repeated', 'python python python sql', 'python sql sql sql'),
        ('unknown', 'zzzzqqqq', 'qqqqzzzz'),
        ('no_job_skills', 'Python', 'zzzzqqqq'),
        ('boundaries', 'scar c++17 javaScripted node.json .network c#x', 'C, C++, C#, Java, JavaScript, .NET, Node.js.'),
        ('empty_resume', ' \t\n', 'Python'), ('empty_job', 'Python', '\u00a0\u001c'),
    ]
    data = pd.read_csv(root / 'data/labeled/suitability_development_labels_v1.csv', dtype=str, keep_default_na=False).set_index('pair_id')
    manifest = pd.read_csv(root / 'data/processed/milestone3/v2/split_manifest.csv', dtype=str)
    for i, pair in enumerate(manifest.loc[manifest.split.eq('validation'), 'pair_id']):
        row = data.loc[pair]; cases.append((f'validation_{i+1}', row.resume_text, row.job_text))
    result = []
    vectorizer = assets['vectorizer']; inverse = vectorizer.get_feature_names_out()
    for name, resume, job in cases:
        row = {'name': name, 'resume': resume, 'job': job}
        try:
            feedback = e.analyze_skill_gap(resume, job, assets)
            x = pd.DataFrame([feedback['model_features']], columns=m.FEATURES)
            sparse = vectorizer.transform([m.normalized(resume), m.normalized(job)])
            row.update({'feedback': feedback, 'normalized': [m.normalized(resume), m.normalized(job)],
                        'tokens': [vectorizer.build_analyzer()(m.normalized(t)) for t in [resume, job]],
                        'vectors': [{str(int(i)): float(v) for i, v in zip(sparse[k].indices, sparse[k].data)} for k in [0, 1]],
                        'scaled': assets['model'][0].transform(x).tolist()[0], 'decision': float(assets['model'].decision_function(x)[0])})
        except ValueError as error:
            row['error'] = str(error)
        result.append(row)
    scaler, classifier = assets['model'][0], assets['model'][1]
    boundary = []
    for decision in [-1e-9, 0., 1e-9]:
        scaled = np.zeros(4); scaled[0] = (decision - classifier.intercept_[0]) / classifier.coef_[0, 0]
        raw = scaled * scaler.scale_ + scaler.mean_
        x = pd.DataFrame([raw], columns=m.FEATURES)
        actual = float(assets['model'].decision_function(x)[0]); score = float(assets['model'].predict_proba(x)[0, assets['positive_index']])
        boundary.append({'features': raw.tolist(), 'scaled': scaler.transform(x)[0].tolist(), 'decision': actual, 'score': score, 'suitable': score >= .5})
    m.check_fingerprints(root, assets['fingerprints'])
    return {'cases': result, 'boundary': boundary, 'python': platform.python_version()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--references', action='store_true', help='Private references to stdout for the Node verifier only')
    args = parser.parse_args()
    if args.references:
        with redirect_stdout(io.StringIO()):
            values = references(args.root)
        print(json.dumps(values, ensure_ascii=True, allow_nan=False))
    else:
        export(args.root)


if __name__ == '__main__':
    main()
