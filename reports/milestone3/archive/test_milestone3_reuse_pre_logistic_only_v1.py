"""Small read-only checks for saved-result reuse and fingerprint guards."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import milestone3 as m
from sklearn.pipeline import Pipeline


class SavedRunChecks(unittest.TestCase):
    def test_reviewed_v2_without_processing_or_fitting(self):
        with ExitStack() as stack:
            for owner, name in [(m, 'validate'), (m, 'split_data'), (m, 'features'), (m, 'build_dictionary'),
                                (m, 'train_models'), (Pipeline, 'fit'), (m.LogisticRegression, 'fit'),
                                (m.RandomForestClassifier, 'fit'), (m.TfidfVectorizer, 'fit'),
                                (m.StandardScaler, 'fit')]:
                stack.enter_context(patch.object(owner, name, side_effect=AssertionError(f'{name} must not run')))
            comparison, audit, selection = m.run(ROOT)
        m.pd.testing.assert_frame_equal(comparison, m.pd.read_csv(ROOT / 'reports/milestone3/v2/validation_comparison.csv'))
        self.assertEqual(audit, json.loads((ROOT / 'reports/milestone3/v2/split_audit.json').read_text()))
        self.assertEqual(selection, json.loads((ROOT / 'models/milestone3/v2/selection.json').read_text()))

    def test_changed_temporary_input_blocks_successful_reuse(self):
        with tempfile.TemporaryDirectory() as folder:
            temporary_input = Path(folder) / 'input.csv'
            temporary_input.write_text('original')
            fingerprints = m.capture_fingerprints(ROOT)
            fingerprints[str(temporary_input)] = m.digest(temporary_input)
            read_csv = m.pd.read_csv
            def change_after_read(*args, **kwargs):
                result = read_csv(*args, **kwargs)
                temporary_input.write_text('changed')
                return result
            with patch.object(m, 'capture_fingerprints', return_value=fingerprints), patch.object(m.pd, 'read_csv', side_effect=change_after_read):
                with self.assertRaisesRegex(RuntimeError, 'Fingerprint changed during execution:.*input.csv'):
                    m.run(ROOT)

    def test_dataset_mismatch_is_explicit_and_never_retrains(self):
        fingerprints = m.capture_fingerprints(ROOT)
        fingerprints['data/raw/cv.csv'] = 'temporary simulated mismatch'
        with patch.object(m, 'capture_fingerprints', return_value=fingerprints), patch.object(m, 'train_models', side_effect=AssertionError('training forbidden')):
            with self.assertRaisesRegex(RuntimeError, 'fingerprint mismatch for data/raw/cv.csv'):
                m.run(ROOT)

    def test_training_requires_explicit_opt_in(self):
        with self.assertRaisesRegex(RuntimeError, 'training is disabled'):
            m.run(ROOT, reuse_version=None)


if __name__ == '__main__':
    unittest.main()
