#!/usr/bin/env python3
"""Quick script to check PostgreSQL database contents"""
import psycopg2
import sys

# Connect to the database
conn = psycopg2.connect('postgresql://rbuser:rescue@db:5432/rescuebox')
cur = conn.cursor()

# Check what tables exist
print("=" * 60)
print("TABLES IN DATABASE:")
print("=" * 60)
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
""")
tables = cur.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\n" + "=" * 60)
print("TEXT_EMBEDDINGS TABLE:")
print("=" * 60)

# Count rows
cur.execute("SELECT COUNT(*) FROM text_embeddings")
count = cur.fetchone()[0]
print(f"Total rows: {count}")

if count > 0:
    print("\nFirst 5 rows:")
    print("-" * 60)
    cur.execute("SELECT id, path FROM text_embeddings LIMIT 5")
    rows = cur.fetchall()
    for row in rows:
        print(f"  ID: {row[0]}, Path: {row[1]}")
    
    # Check embedding dimensions (pgvector stores dimension info differently)
    cur.execute("""
        SELECT path, 
               CASE WHEN embedding IS NOT NULL THEN 'Has embedding' ELSE 'NULL' END 
        FROM text_embeddings LIMIT 1
    """)
    result = cur.fetchone()
    if result:
        print(f"\nSample embedding status: {result[1]}")
else:
    print("  (No data yet)")

# Check for indexes
print("\n" + "=" * 60)
print("INDEXES:")
print("=" * 60)
cur.execute("""
    SELECT indexname, indexdef 
    FROM pg_indexes 
    WHERE tablename = 'text_embeddings'
""")
indexes = cur.fetchall()
for idx in indexes:
    print(f"  - {idx[0]}")

# Check pgvector extension
print("\n" + "=" * 60)
print("EXTENSIONS:")
print("=" * 60)
cur.execute("SELECT extname, extversion FROM pg_extension")
extensions = cur.fetchall()
for ext in extensions:
    print(f"  - {ext[0]} (version {ext[1]})")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)

