import os, sqlite3, tempfile, unittest
from pathlib import Path

class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); os.environ['ATA_DATA_DIR']=self.tmp.name
        from core import db; db.reset_for_tests(); db.init_db()
        self.old=Path(self.tmp.name)/'old.db'
        c=sqlite3.connect(self.old)
        c.executescript('''
        CREATE TABLE supervisor_directive(id TEXT, session_id TEXT, quote TEXT, directive TEXT, priority TEXT, target_chapter TEXT, status TEXT, evidence_ref TEXT);
        CREATE TABLE source(id TEXT,type TEXT,doi TEXT,title TEXT,authors TEXT,year INTEGER,verified INTEGER,brief_json TEXT);
        CREATE TABLE consistency_row(element TEXT,content TEXT,score INTEGER,critique TEXT);
        ''')
        c.execute("INSERT INTO supervisor_directive VALUES('BH1-01','S1','q','d','MUST','I','open',NULL)")
        c.execute("INSERT INTO source VALUES('S1','journal','10.1/x','Paper','Author',2025,1,'{}')")
        c.execute("INSERT INTO consistency_row VALUES('Judul','X',3,'ok')")
        c.commit(); c.close()
    def tearDown(self): self.tmp.cleanup(); os.environ.pop('ATA_DATA_DIR',None)
    def test_migrates_old_workspace_into_one_isolated_project(self):
        from scripts.migrate_v2_to_v3 import migrate
        from core import db
        report=migrate(str(self.old),'migration-session')
        self.assertEqual(report['directives'],1)
        self.assertEqual(report['sources'],1)
        project=db.list_projects('migration-session')[0]
        self.assertEqual(len(db.get_directives(project['id'])),1)
        self.assertEqual(len(db.list_sources(project['id'])),1)

if __name__=='__main__': unittest.main()
