import sqlite3
from datetime import datetime

DB_PATH = "state.db"




def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)




def init_db():
    conn = get_conn()
    cur = conn.cursor()

   
    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_status (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

  
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        trend TEXT,
        score INTEGER,
        reasons TEXT,
        entry REAL,
        stop_loss REAL,
        target REAL,
        created_at TEXT
    )
    """)

   
    cur.execute("""
    CREATE TABLE IF NOT EXISTS confidence_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        score INTEGER,
        created_at TEXT
    )
    """)

    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS active_trades (
        symbol TEXT PRIMARY KEY,
        entry REAL,
        stop_loss REAL,
        target REAL,
        rr REAL,
        quantity REAL,
        trend TEXT,
        status TEXT,
        opened_at TEXT
    )
    """)

    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS last_prices (
        symbol TEXT PRIMARY KEY,
        price REAL,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()




def update_system_status(key, value):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT OR REPLACE INTO system_status (key, value) VALUES (?, ?)",
        (key, str(value))
    )

    conn.commit()
    conn.close()




def update_last_price(symbol, price):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO last_prices (symbol, price, updated_at)
    VALUES (?, ?, ?)
    """, (symbol, price, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()




def insert_confidence(score):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO confidence_history (score, created_at)
    VALUES (?, ?)
    """, (score, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()


def insert_alert(signal):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO alerts
    (symbol, trend, score, reasons, entry, stop_loss, target, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        signal["symbol"],
        signal["trend"],
        signal["score"],
        " | ".join(signal["reasons"]),
        signal["trade"]["entry"],
        signal["trade"]["stop_loss"],
        signal["trade"]["target"],
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()



def get_active_trade(symbol):
    conn = get_conn()
    cur = conn.cursor()

    row = cur.execute("""
    SELECT symbol, entry, stop_loss, target, quantity, trend
    FROM active_trades
    WHERE symbol=? AND status='OPEN'
    """, (symbol,)).fetchone()

    conn.close()

    if not row:
        return None

    return {
        "symbol": row[0],
        "entry": row[1],
        "stop_loss": row[2],
        "target": row[3],
        "quantity": row[4],
        "trend": row[5]
    }


def create_active_trade(signal):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO active_trades
    (symbol, entry, stop_loss, target, rr, quantity, trend, status, opened_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
    """, (
        signal["symbol"],
        signal["trade"]["entry"],
        signal["trade"]["stop_loss"],
        signal["trade"]["target"],
        signal["trade"]["rr"],
        signal["trade"]["quantity"],
        signal["trend"],
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


def close_active_trade(symbol):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE active_trades
    SET status='CLOSED'
    WHERE symbol=?
    """, (symbol,))

    conn.commit()
    conn.close()
