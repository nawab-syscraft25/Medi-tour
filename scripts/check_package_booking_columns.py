import sqlite3, json, os

db = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'meditour.db'))
print('DB path:', db)
print('Exists:', os.path.exists(db))
if not os.path.exists(db):
    raise SystemExit('DB file not found')

conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("PRAGMA table_info('package_bookings')")
rows = cur.fetchall()
print(json.dumps(rows, indent=2))
conn.close()
