import os
import sqlite3
import re

try:
    import mysql.connector
except ImportError:
    mysql = None


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "cyberguardian.db")


class SQLiteCursorAdapter:
    def __init__(self, cursor, dictionary=False):
        self._cursor = cursor
        self._dictionary = dictionary

    def execute(self, query, params=None):
        # Convert %s placeholder to ? for SQLite
        sqlite_query = re.sub(r'(?<!%)(%s)', '?', query)
        # Handle NOW() -> CURRENT_TIMESTAMP
        sqlite_query = re.sub(r'\bNOW\(\)', 'CURRENT_TIMESTAMP', sqlite_query, flags=re.IGNORECASE)
        sqlite_query = re.sub(r'\bDATABASE\(\)', "''", sqlite_query, flags=re.IGNORECASE)

        if params is None:
            return self._cursor.execute(sqlite_query)
        else:
            # Convert params if dict or list
            if isinstance(params, (list, tuple)):
                clean_params = list(params)
            else:
                clean_params = params
            return self._cursor.execute(sqlite_query, clean_params)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self._dictionary:
            return dict(row)
        return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        if self._dictionary:
            return [dict(r) for r in rows]
        return rows

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()


class SQLiteConnectionAdapter:
    def __init__(self, conn):
        self._conn = conn
        self._conn.row_factory = sqlite3.Row

    def cursor(self, dictionary=False):
        raw_cursor = self._conn.cursor()
        return SQLiteCursorAdapter(raw_cursor, dictionary=dictionary)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def is_connected(self):
        return True

    def close(self):
        self._conn.close()


def init_sqlite_db():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            qr_content TEXT NOT NULL,
            prediction VARCHAR(30) NOT NULL,
            confidence REAL NULL,
            risk_score INTEGER NULL,
            risk_level VARCHAR(30) NULL,
            risk_factors TEXT NULL,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_connection():
    # 1. Try MySQL on port 3307 (user's preferred port)
    if mysql is not None:
        try:
            conn = mysql.connector.connect(
                host="localhost",
                port=3307,
                user="root",
                password="",
                database="cyberguardian",
                connection_timeout=2
            )
            if conn.is_connected():
                return conn
        except Exception:
            pass

        # 2. Try MySQL on standard port 3306
        try:
            conn = mysql.connector.connect(
                host="localhost",
                port=3306,
                user="root",
                password="",
                database="cyberguardian",
                connection_timeout=2
            )
            if conn.is_connected():
                return conn
        except Exception:
            pass

    # 3. Fallback to SQLite (ensures 100% uptime for all users)
    init_sqlite_db()
    raw_conn = sqlite3.connect(SQLITE_DB_PATH)
    return SQLiteConnectionAdapter(raw_conn)


# Test connection upon import
try:
    test_conn = get_connection()
    print("Database ready (connection established).")
    test_conn.close()
except Exception as err:
    print("Database initial check note:", err)