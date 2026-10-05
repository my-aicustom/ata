"""
api/index.py - Vercel Serverless Function Handler for ATA v2
Bridges Vercel Serverless HTTP requests to the ATA backend engine.
"""
import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_DIR = os.path.join(ROOT_DIR, "core")
WEB_DIR = os.path.join(ROOT_DIR, "web")

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)

from server import ATAHandler, init_db

# Initialize SQLite database
try:
    init_db()
except Exception as e:
    print(f"DB init warning in serverless environment: {e}")

class handler(ATAHandler):
    pass
