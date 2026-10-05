import json
import tempfile
import unittest
from pathlib import Path
from datetime import date
from core import gates, db

class GateBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.old = gates.DB_PATH
        gates.DB_PATH = str(Path(self.temp.name) / 'test.db')
        db.init_db(gates.DB_PATH)
        gates._assessment('G1')

    def tearDown(self):
        gates.DB_PATH = self.old
        self.temp.cleanup()

    def assessment(self, gate, data):
        with gates.get_db() as conn:
            conn.execute('INSERT OR REPLACE INTO gate_assessment VALUES (?, ?)', (gate, json.dumps(data)))

    def test_finer_requires_measurements_and_must(self):
        with gates.get_db() as conn:
            conn.execute("UPDATE supervisor_directive SET status='addressed'")
        self.assertFalse(gates.evaluate_g1()['passed'])
        self.assessment('G1', {'finer_scores': {k:3 for k in ['Feasible','Interesting','Novel','Ethical','Relevant']}})
        self.assertTrue(gates.evaluate_g1()['passed'])
        with gates.get_db() as conn:
            conn.execute("UPDATE supervisor_directive SET status='clarify' WHERE id='BH1-01'")
        self.assertFalse(gates.evaluate_g1()['passed'])

    def test_source_all_quotas_and_verified_only(self):
        with gates.get_db() as conn:
            for i in range(30):
                kind='book' if i<5 else 'journal'
                meta={'core_book':i<5,'international':5<=i<15,'sinta':15<=i<20}
                conn.execute('INSERT INTO source(id,type,title,authors,year,verified,brief_json) VALUES(?,?,?,?,?,?,?)',
                             (str(i),kind,'Title','Author',date.today().year if i<18 else date.today().year-11,1,json.dumps(meta)))
        self.assertTrue(gates.evaluate_g2()['passed'])
        with gates.get_db() as conn:
            conn.execute("UPDATE source SET verified=0 WHERE id='0'")
        self.assertFalse(gates.evaluate_g2()['passed'])

    def test_matrix_every_row(self):
        self.assertFalse(gates.evaluate_g3()['passed'])
        with gates.get_db() as conn:
            conn.execute('UPDATE consistency_row SET score=3')
        self.assertTrue(gates.evaluate_g3()['passed'])

    def test_statistics_boundaries(self):
        data={'loading':[.7,.8],'ave':.5,'htmt':.899,'cr':.7}
        self.assessment('G4',data)
        self.assertTrue(gates.evaluate_g4()['passed'])
        for key,value in [('htmt',.9),('loading',[]),('ave',None),('cr',True)]:
            self.assessment('G4',dict(data,**{key:value}))
            self.assertFalse(gates.evaluate_g4()['passed'],key)

    def test_final_missing_zero_not_success(self):
        data={'invalid_citations':0,'unsupported_claims':0,'open_red_critiques':0,'similarity':19,'similarity_threshold':20}
        self.assessment('G5',data)
        self.assertTrue(gates.evaluate_g5()['passed'])
        for key,value in [('similarity',20),('unsupported_claims',1),('invalid_citations',None)]:
            self.assessment('G5',dict(data,**{key:value}))
            self.assertFalse(gates.evaluate_g5()['passed'])

    def test_defense_denominator_includes_unanswered(self):
        self.assessment('G6',{'question_scores':[3,4,3,3,None]})
        self.assertTrue(gates.evaluate_g6()['passed'])
        self.assessment('G6',{'question_scores':[3,4,3,None,None]})
        self.assertFalse(gates.evaluate_g6()['passed'])

if __name__=='__main__': unittest.main()
