#!/usr/bin/env python3
"""
Check database schema
"""

import sqlite3
import os

db_file = 'test_seeding.db'

if os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f'Tables: {tables}')
    
    for table in tables:
        if table != 'sqlite_sequence':
            print(f'\n{table.upper()} columns:')
            cursor.execute(f"PRAGMA table_info({table})")
            for row in cursor.fetchall():
                print(f'  {row[1]} {row[2]}')
    
    conn.close()
else:
    print(f"Database file {db_file} not found") 