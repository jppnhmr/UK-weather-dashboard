import sqlite3

from typing import List, Tuple, Any, Optional

DATABASE_NAME = "historic_station_data"

def connect():
    conn = sqlite3.connect(f"{DATABASE_NAME}.db")
    return conn

# Setup #
def create_tables():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
CREATE TABLE IF NOT EXISTS stations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    lon         REAL,
    lat         REAL,
    opened      INTEGER,
    data_url    TEXT                
)
""")
    
    cur.execute("""
CREATE TABLE IF NOT EXISTS observations (
    station_id  INTEGER NOT NULL,
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    tmax        REAL,
    tmin        REAL,
    af          INTEGER,
    rain        REAL,
    sun         REAL,
    PRIMARY KEY (station_id, year, month),
    FOREIGN KEY (station_id) REFERENCES stations(id)
)
""")
    
    conn.commit()
    conn.close()

# Insert #
def insert_station(name, lon, lat, opened, data_url):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO stations (name, lon, lat, opened, data_url)
    VALUES (?, ?, ?, ?, ?)              
    """, (name, lon, lat, opened, data_url))

    cur.execute("SELECT id FROM stations WHERE name = ?", (name,))

    station_id = cur.fetchone()[0]

    conn.commit()
    conn.close()

    return station_id

def insert_observation(station_id, year, month, tmax, tmin, af, rain, sun):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO observations
        (station_id, year, month, tmax, tmin, af, rain, sun)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (station_id, year, month, tmax, tmin, af, rain, sun))

    conn.commit()
    conn.close()

# Select
def select(query: str, params: Tuple[Any, ...] = ()) -> Optional [List[Tuple]]:
    conn = connect()
    cur = conn.cursor()

    try:
        cur.execute(query, params)

        results = cur.fetchall()

        return results
    
    except sqlite3.Error as e:
        print(f"Error performing database query: {e}")
        return None
    
    finally:
        conn.close()
