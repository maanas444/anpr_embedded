#!/usr/bin/env python3
import argparse
import sys
from datetime import datetime
import mysql.connector
from mysql.connector import Error

from db_config import DB_CONFIG

SCHEMA = """
CREATE TABLE IF NOT EXISTS lp_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    node_name VARCHAR(64) NOT NULL,
    licence_plate VARCHAR(16) NOT NULL,
    seen_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS lp_counts (
    licence_plate VARCHAR(16) PRIMARY KEY,
    occurrences INT NOT NULL DEFAULT 1,
    last_seen DATETIME NOT NULL
);
"""

def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"[DB ERROR] Could not connect: {e}", file=sys.stderr)
        sys.exit(1)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    for stmt in SCHEMA.strip().split(";"):
        if stmt.strip():
            cur.execute(stmt)
    conn.commit()
    cur.close()
    conn.close()
    print("ANPR database schema ready.")

def write_entry(node_id: str, licence_plate: str, timestamp_ns:int):
    """Write an LP entry and update the occurrence-count table."""
    timestamp = datetime.fromtimestamp(int(timestamp_ns) // 1_000_000_000)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO lp_entries (node_name, licence_plate, seen_at) VALUES (%s, %s, %s)",
        (node_id, licence_plate, timestamp),
    )

    cur.execute(
        """
        INSERT INTO lp_counts (licence_plate, occurrences, last_seen)
        VALUES (%s, 1, %s)
        ON DUPLICATE KEY UPDATE
            occurrences = occurrences + 1,
            last_seen = VALUES(last_seen)
        """,
        (licence_plate, timestamp),
    )

    conn.commit()
    cur.close()
    conn.close()
    print(f"Logged: node='{node_id}' plate='{licence_plate}' at {timestamp}")

def list_entries():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, node_name, licence_plate, seen_at FROM lp_entries ORDER BY seen_at DESC")
    rows = cur.fetchall()

    print(f"\n{'ID':<5}{'Node':<15}{'Plate':<12}{'Seen At'}")
    print("-" * 50)
    for row in rows:
        print(f"{row[0]:<5}{row[1]:<15}{row[2]:<12}{row[3]}")

    cur.execute("SELECT licence_plate, occurrences, last_seen FROM lp_counts ORDER BY occurrences DESC")
    counts = cur.fetchall()
    print(f"\n{'Plate':<12}{'Count':<8}{'Last Seen'}")
    print("-" * 40)
    for row in counts:
        print(f"{row[0]:<12}{row[1]:<8}{row[2]}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANPR database manager")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create schema if not present")

    write_p = sub.add_parser("write", help="Write a new LP entry")
    write_p.add_argument("node_id", help="Identifier of the node/LNR unit")
    write_p.add_argument("licence_plate", help="Detected licence plate string")
    write_p.add_argument("timestamp_ns", help="Timestamp")

    sub.add_parser("list", help="Print DB contents")

    args = parser.parse_args()

    if args.command == "init":
        init_db()
    elif args.command == "write":
        write_entry(args.node_id, args.licence_plate, args.timestamp_ns)
    elif args.command == "list":
        list_entries()
