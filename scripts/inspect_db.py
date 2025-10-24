import sqlite3
import os
p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'meditour.db')
print('db path:', p)
conn = sqlite3.connect(p)
cur = conn.cursor()
print('tables:', [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")])
print('assoc_exists:', [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='treatment_doctor_association'")])
try:
    rows = list(cur.execute('SELECT * FROM alembic_version'))
    print('alembic_version rows:', rows)
except Exception as e:
    print('alembic_version error:', e)
conn.close()
