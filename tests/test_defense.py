import os
import tempfile
import unittest

from core import db
from core.defense import parse_defense_evaluation, summarize_defense_history


class DefenseTests(unittest.TestCase):
    def test_parse_json_even_when_wrapped_in_markdown_fence(self):
        text='```json\n{"score":2,"feedback":"Metode belum dijelaskan","ideal_answer":"Jelaskan alasan sampling","weakness":"sampling"}\n```'
        out=parse_defense_evaluation(text)
        self.assertEqual(out['score'],2)
        self.assertEqual(out['weakness'],'sampling')

    def test_history_summary_prioritizes_low_scores(self):
        rows=[
            {'question':'Q1','score':2,'feedback':'f','weakness':'metode'},
            {'question':'Q2','score':4,'feedback':'f','weakness':'teori'},
            {'question':'Q3','score':1,'feedback':'f','weakness':'metode'},
        ]
        out=summarize_defense_history(rows)
        self.assertEqual(out['attempts'],3)
        self.assertAlmostEqual(out['average_score'], 7/3, places=2)
        self.assertEqual(out['priority_weaknesses'][0]['name'],'metode')

    def test_defense_score_can_be_persisted(self):
        tmp=tempfile.TemporaryDirectory(); old=os.environ.get('ATA_DATA_DIR'); os.environ['ATA_DATA_DIR']=tmp.name
        try:
            db.reset_for_tests(); db.init_db(); pid=db.create_project('s',{'student':'A','program':'S2','topic':'T'})
            db.save_defense_score(pid,'Mengapa metode ini?','Karena...',2,'Kurang kuat','metode')
            rows=db.list_defense_scores(pid)
            self.assertEqual(rows[0]['score'],2)
            self.assertEqual(rows[0]['weakness'],'metode')
        finally:
            if old is None: os.environ.pop('ATA_DATA_DIR',None)
            else: os.environ['ATA_DATA_DIR']=old
            tmp.cleanup()


if __name__ == '__main__': unittest.main()
