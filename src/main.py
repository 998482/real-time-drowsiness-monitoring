"""
Real-time driver drowsiness monitoring with OpenCV Haar Cascades.
"""

import cv2
import time
import winsound
import csv
import sqlite3
from datetime import datetime
from pathlib import Path


def load_cascades() -> tuple[cv2.CascadeClassifier, cv2.CascadeClassifier] | tuple[None, None]:
    # Load built-in cascades for face and eye detection.
    face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(face_cascade_path)

    eye_cascade_path = cv2.data.haarcascades + "haarcascade_eye.xml"
    eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

    # Validate cascade files before starting camera loop.
    if face_cascade.empty():
        print("Error: Could not load face Haar Cascade file.")
        return None, None
    if eye_cascade.empty():
        print("Error: Could not load eye Haar Cascade file.")
        return None, None

    return face_cascade, eye_cascade


def draw_face_and_eye_boxes(
    frame: cv2.typing.MatLike,
    gray_frame: cv2.typing.MatLike,
    face_cascade: cv2.CascadeClassifier,
    eye_cascade: cv2.CascadeClassifier,
) -> tuple[bool, bool]:
    # Face detection runs on grayscale for speed and stability.
    faces = face_cascade.detectMultiScale(
        gray_frame,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )
    face_found = len(faces) > 0
    eyes_found = False

    # Detect eyes only inside each face ROI to reduce false positives.
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        face_gray_roi = gray_frame[y : y + h, x : x + w]
        face_color_roi = frame[y : y + h, x : x + w]

        eyes = eye_cascade.detectMultiScale(
            face_gray_roi,
            scaleFactor=1.1,
            minNeighbors=8,
            minSize=(20, 20),
        )
        if len(eyes) > 0:
            eyes_found = True

        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(face_color_roi, (ex, ey), (ex + ew, ey + eh), (255, 0, 0), 2)

    return face_found, eyes_found


def play_alert_sound() -> None:
    # Play a short alarm beep on new alert events.
    try:
        winsound.Beep(1000, 200)
    except RuntimeError:
        # Fallback system bell if Beep is unavailable.
        print("\a", end="")


def setup_alert_log_file() -> Path:
    # Create logs directory and CSV file with header when missing.
    project_root = Path(__file__).resolve().parent.parent
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    log_file_path = logs_dir / "alert_log.csv"
    if not log_file_path.exists():
        with log_file_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["timestamp", "alert_count", "alert_event"])

    return log_file_path


def log_alert_event(log_file_path: Path, alert_count: int) -> None:
    # Append one row per alert episode for later analysis.
    timestamp = datetime.now().isoformat(timespec="seconds")

    with log_file_path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([timestamp, alert_count, "DROWSINESS_ALERT"])


def init_db(db_path: Path) -> None:
    # Database connection happens here to create DB/table automatically.
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS drowsiness_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            blink_count INTEGER NOT NULL,
            eye_closure_duration REAL NOT NULL,
            risk_score REAL NOT NULL,
            status TEXT NOT NULL
        )
        """
    )
    connection.commit()
    connection.close()


def calculate_risk_score(blink_count: int, eye_closure_duration: float) -> tuple[float, str]:
    # Risk score is calculated here using a simple beginner-friendly formula.
    risk_score = (blink_count * 2) + (eye_closure_duration * 10)

    if risk_score <= 30:
        status = "Safe"
    elif risk_score <= 60:
        status = "Moderate"
    else:
        status = "Dangerous"

    return risk_score, status


def insert_drowsiness_log(
    db_path: Path,
    blink_count: int,
    eye_closure_duration: float,
    risk_score: float,
    status: str,
) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")

    # SQL INSERT happens here whenever a new drowsiness episode is detected.
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO drowsiness_logs (
            timestamp, blink_count, eye_closure_duration, risk_score, status
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (timestamp, blink_count, eye_closure_duration, risk_score, status),
    )
    connection.commit()
    connection.close()


def main() -> None:
    face_cascade, eye_cascade = load_cascades()
    if face_cascade is None or eye_cascade is None:
        return

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Webcam started. Press 'Q' to quit.")
    log_file_path = setup_alert_log_file()
    db_path = Path(__file__).resolve().parent.parent / "drowsiness.db"
    init_db(db_path)
    print(f"Alert log file: {log_file_path}")
    print(f"SQLite DB file: {db_path}")

    # Track when eyes first become unavailable.
    eyes_missing_start_time: float | None = None
    alert_threshold_seconds = 2.0
    alert_active = False
    alert_count = 0

    while True:
        success, frame = camera.read()

        if not success:
            print("Warning: Could not read frame from webcam.")
            break

        # Preprocessing: grayscale improves Haar cascade performance.
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Run detection and return visibility flags.
        face_found, eyes_found = draw_face_and_eye_boxes(frame, gray_frame, face_cascade, eye_cascade)

        # Trigger alert only when eyes stay missing for threshold duration.
        now = time.time()
        show_alert = False

        if face_found and not eyes_found:
            if eyes_missing_start_time is None:
                eyes_missing_start_time = now
            elif now - eyes_missing_start_time > alert_threshold_seconds:
                show_alert = True
        else:
            # Reset state when eyes are back or face is out of frame.
            eyes_missing_start_time = None
            alert_active = False

        # Count, sound, and log only once per alert episode.
        if show_alert and not alert_active:
            play_alert_sound()
            alert_count += 1
            log_alert_event(log_file_path, alert_count)
            eye_closure_duration = now - eyes_missing_start_time if eyes_missing_start_time is not None else 0.0
            risk_score, status = calculate_risk_score(alert_count, eye_closure_duration)
            insert_drowsiness_log(db_path, alert_count, eye_closure_duration, risk_score, status)
            alert_active = True

        if show_alert:
            cv2.putText(
                frame,
                "DROWSINESS ALERT!",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                3,
                cv2.LINE_AA,
            )

        # Live alert counter for quick monitoring.
        cv2.putText(
            frame,
            f"Alert Count: {alert_count}",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

        cv2.imshow("Drowsiness Detection (Press Q to quit)", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
