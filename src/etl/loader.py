from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

from normaliser import LOAD_ORDER, read_source


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialise_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.execute("PRAGMA foreign_keys = ON")


def insert_frame(conn: sqlite3.Connection, table: str, frame) -> tuple[int, int, list[str]]:
    columns = list(frame.columns)
    placeholders = ",".join(["?"] * len(columns))
    column_sql = ",".join(columns)
    sql = f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})"
    loaded = 0
    rejections: list[str] = []

    for row in frame.itertuples(index=False, name=None):
        try:
            conn.execute(sql, row)
            loaded += 1
        except sqlite3.IntegrityError as exc:
            rejections.append(str(exc))
    return loaded, len(rejections), rejections


def split_known_companies(frame, known_companies: set[str]):
    if "company_id" not in frame.columns:
        return frame, 0, ""
    valid_mask = frame["company_id"].isin(known_companies)
    rejected = frame.loc[~valid_mask]
    sample = ""
    if not rejected.empty:
        sample = f"Unknown company_id excluded before FK insert: {rejected.iloc[0]['company_id']}"
    return frame.loc[valid_mask].copy(), len(rejected), sample


def load_all(data_dir: Path, db_path: Path, audit_path: Path) -> list[dict[str, object]]:
    conn = connect(db_path)
    initialise_schema(conn)
    audit_rows: list[dict[str, object]] = []
    frames = {table: read_source(data_dir, table) for table in LOAD_ORDER}
    known_companies = set(frames["companies"]["id"].dropna())

    for table in LOAD_ORDER:
        frame = frames[table]
        source_rows = len(frame)
        frame, pre_insert_rejected, pre_insert_sample = split_known_companies(frame, known_companies)
        loaded, rejected, rejections = insert_frame(conn, table, frame)
        total_rejected = pre_insert_rejected + rejected
        audit_rows.append(
            {
                "file": f"{table}.xlsx",
                "table": table,
                "source_rows": source_rows,
                "loaded_rows": loaded,
                "rejected_rows": total_rejected,
                "critical_rejections": rejected,
                "warning_rejections": pre_insert_rejected,
                "sample_rejection": rejections[0] if rejections else pre_insert_sample,
            }
        )
        conn.commit()

    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0].keys()))
        writer.writeheader()
        writer.writerows(audit_rows)

    conn.close()
    return audit_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Load NIFTY100 Excel sources into SQLite.")
    parser.add_argument("--data-dir", default=r"C:\Users\hp\Downloads")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "output" / "nifty100.db"))
    parser.add_argument("--audit", default=str(PROJECT_ROOT / "output" / "load_audit.csv"))
    args = parser.parse_args()

    rows = load_all(Path(args.data_dir), Path(args.db), Path(args.audit))
    for row in rows:
        print(f"{row['table']}: {row['loaded_rows']} loaded, {row['rejected_rows']} rejected")


if __name__ == "__main__":
    main()
