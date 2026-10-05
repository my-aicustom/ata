import os
import tempfile
import unittest
from pathlib import Path


class V3FoundationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['ATA_DATA_DIR'] = self.tmp.name
        os.environ.pop('DATABASE_URL', None)

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop('ATA_DATA_DIR', None)

    def test_project_data_is_scoped_per_session(self):
        from core import db
        db.reset_for_tests()
        db.init_db()
        a = db.create_project('session-a', {'student': 'A', 'program': 'S2', 'topic': 'Topik A', 'domain': 'umum', 'method': 'survey'})
        b = db.create_project('session-b', {'student': 'B', 'program': 'S2', 'topic': 'Topik B', 'domain': 'umum', 'method': 'interview'})
        self.assertEqual([p['id'] for p in db.list_projects('session-a')], [a])
        self.assertEqual([p['id'] for p in db.list_projects('session-b')], [b])
        self.assertIsNone(db.get_project_for_session('session-a', b))

    def test_next_action_prioritizes_topic_gate_before_literature(self):
        from core.planner import next_best_action
        state = {
            'stage': 'proposal',
            'gates': {'G1': {'passed': False}, 'G2': {'passed': False}},
            'open_must': 2,
        }
        action = next_best_action(state)
        self.assertEqual(action['phase'], 1)
        self.assertEqual(action['role'], 'topic_framer')
        self.assertIn('arahan pembimbing', action['reason'].lower())

    def test_g4_uses_method_specific_criteria(self):
        from core.gates import evaluate_g4_payload
        survey = evaluate_g4_payload('survey', {'loading': [0.72], 'ave': [0.55], 'htmt': [0.82], 'cr': [0.78]})
        interview = evaluate_g4_payload('interview', {'saturation': True, 'triangulation_sources': 2, 'codebook_verified': True, 'member_check': True})
        experiment = evaluate_g4_payload('system-experiment', {'runs_per_scenario': 5, 'reproducible': True, 'raw_logs_saved': True, 'analysis_plan_followed': True})
        self.assertTrue(survey['passed'])
        self.assertTrue(interview['passed'])
        self.assertTrue(experiment['passed'])
        self.assertNotEqual(set(survey['checks']), set(interview['checks']))

    def test_source_search_result_normalization_never_marks_unverified_as_verified(self):
        from core.literature import normalize_openalex_work
        item = {
            'id': 'https://openalex.org/W1',
            'doi': 'https://doi.org/10.1000/test',
            'display_name': 'Judul',
            'publication_year': 2025,
            'authorships': [{'author': {'display_name': 'Nama'}}],
        }
        src = normalize_openalex_work(item)
        self.assertEqual(src['verification_status'], 'candidate')
        self.assertFalse(src['verified'])
        self.assertEqual(src['doi'], '10.1000/test')

    def test_artifacts_are_versioned_not_overwritten(self):
        from core import db
        db.reset_for_tests()
        db.init_db()
        project = db.create_project('session-a', {'student': 'A', 'program': 'S2', 'topic': 'T', 'domain': 'umum', 'method': 'survey'})
        v1 = db.save_artifact(project, 'chapter', 'Bab I', 'versi satu')
        v2 = db.save_artifact(project, 'chapter', 'Bab I', 'versi dua')
        self.assertEqual(v1['version'], 1)
        self.assertEqual(v2['version'], 2)
        versions = db.list_artifact_versions(project, 'chapter', 'Bab I')
        self.assertEqual([v['version'] for v in versions], [2, 1])
        self.assertEqual(versions[1]['content'], 'versi satu')


if __name__ == '__main__':
    unittest.main()
