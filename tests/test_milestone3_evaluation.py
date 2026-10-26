"""Frozen inference, feedback and saved test-evaluation checks."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import milestone3 as m
from src import milestone3_evaluation as e


class FrozenEvaluationChecks(unittest.TestCase):
    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        for cls in [m.Pipeline, m.LogisticRegression, m.StandardScaler, m.TfidfVectorizer]:
            for method in ['fit', 'fit_transform']:
                if hasattr(cls, method):
                    self.guards.enter_context(patch.object(cls, method, side_effect=AssertionError('Fitting forbidden')))
        for name in ['split_data', 'build_dictionary']:
            self.guards.enter_context(patch.object(m, name, side_effect=AssertionError('Rebuilding forbidden')))
        self.assets = e.load_assets(ROOT)

    def test_feedback_aliases_gaps_and_empty_evidence(self):
        m.check_skills()
        result = e.analyze_skill_gap('I use JS and Python.', 'JavaScript, Python, SQL and Node.js.', self.assets)
        self.assertIn('javascript', result['matched_skills'])
        self.assertEqual([s['skill'] for s in result['suggestions']], result['job_skills_not_found'])
        self.assertEqual(result['job_skills_not_found'], ['node.js', 'sql'])
        for suggestion in result['suggestions']:
            self.assertIn('not found in your resume', suggestion['guidance'])
        empty = e.analyze_skill_gap('Python', 'zzzzqqqq', self.assets)
        self.assertIsNone(empty['job_skill_coverage'])
        self.assertEqual([empty['model_features'][k] for k in m.FEATURES[1:]], [0, 0, 1])
        json.dumps(result, allow_nan=False)
        json.dumps(empty, allow_nan=False)
        for resume, job in [('', 'Python'), ('Python', '  '), (None, 'SQL')]:
            with self.assertRaisesRegex(ValueError, 'nonempty string'):
                e.analyze_skill_gap(resume, job, self.assets)

    def test_metrics_and_completed_reuse_without_predictions(self):
        folder, comparison = e.evaluate_test(ROOT)
        predictions = m.pd.read_csv(folder / 'test_predictions.csv')
        for _, row in comparison.iterrows():
            measured = m.metrics(predictions.training_label, predictions[row['name'] + '_prediction'])
            self.assertAlmostEqual(measured['macro_f1'], row.macro_f1)
            self.assertAlmostEqual(measured['accuracy'], row.accuracy)
        with patch.object(m.Pipeline, 'predict_proba', side_effect=AssertionError('No recomputation on reuse')), patch.object(m, 'features', side_effect=AssertionError('No feature recomputation on reuse')):
            reused_folder, reused = e.evaluate_test(ROOT)
        self.assertEqual(folder, reused_folder)
        expected = m.pd.read_csv(folder / 'test_comparison.csv')
        m.pd.testing.assert_frame_equal(reused, expected)
        domains = json.loads((folder / 'domain_results.json').read_text())
        finance = next(d for d in domains if d['domain'] == 'FINANCE')
        self.assertEqual(finance['pairs'], 0)
        self.assertIsNone(finance['metrics'])


if __name__ == '__main__':
    unittest.main()
