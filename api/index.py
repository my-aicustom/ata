"""Vercel entrypoint for ATA v3."""
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0,ROOT)
from server import ATAHandler, init_db
try: init_db()
except Exception as e: print(f'ATA DB init warning: {e}')
class handler(ATAHandler):
    pass
