"""
View summary stats from the SQLite drowsiness alert database.
"""

import sqlite3
from pathlib import Path


def get_total_alerts(connection: sqlite3.Connection) -> int:
    # SQL query: count all rows (each row is one logged alert episode).
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM drowsiness_logs")
    (count,) = cursor.fetchone()
    return int(count)


def get_average_risk_score(connection: sqlite3.Connection) -> float:
    # SQL query: compute average risk_score across all alerts.
    # COALESCE returns 0 when the table has no rows yet.
    cursor = connection.cursor()
    cursor.execute("SELECT COALESCE(AVG(risk_score), 0) FROM drowsiness_logs")
    (avg_score,) = cursor.fetchone()
    return float(avg_score)


def get_dangerous_events_count(connection: sqlite3.Connection) -> int:
    # SQL query: count only events where status is 'Dangerous'.
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM drowsiness_logs WHERE status = ?", ("Dangerous",))
    (count,) = cursor.fetchone()
    return int(count)


def get_recent_alerts(connection: sqlite3.Connection, limit: int = 5) -> list[tuple]:
    # SQL query: fetch the latest alerts by id (most recent first).
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT id, timestamp, blink_count, eye_closure_duration, risk_score, status
        FROM drowsiness_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return cursor.fetchall()


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / "drowsiness.db"

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        print("Run the webcam detection first to create and populate the database.")
        return

    connection = sqlite3.connect(db_path)
    try:
        total_alerts = get_total_alerts(connection)
        avg_risk_score = get_average_risk_score(connection)
        dangerous_count = get_dangerous_events_count(connection)
        recent_alerts = get_recent_alerts(connection, limit=5)
    except sqlite3.Error as exc:
        print("SQLite error while reading logs.")
        print(f"Details: {exc}")
        return
    finally:
        connection.close()

    print("=" * 60)
    print("Drowsiness DB Summary")
    print("=" * 60)
    print(f"DB Path               : {db_path}")
    print(f"Total Alerts          : {total_alerts}")
    print(f"Average Risk Score    : {avg_risk_score:.2f}")
    print(f"Total Dangerous Events: {dangerous_count}")
    print("-" * 60)
    print("Latest 5 Alerts")
    print("-" * 60)

    if not recent_alerts:
        print("No alerts found yet.")
        return

    header = f"{'ID':>4}  {'Timestamp':19}  {'Blink':>5}  {'Closure(s)':>10}  {'Risk':>7}  {'Status':>9}"
    print(header)
    print("-" * len(header))

    for alert_id, ts, blink, closure, risk, status in recent_alerts:
        print(f"{alert_id:>4}  {ts:19}  {blink:>5}  {closure:>10.2f}  {risk:>7.2f}  {status:>9}")

    print("=" * 60)


if __name__ == "__main__":
    main()

