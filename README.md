# Simple Face Detection (Beginner Project)

This project uses Python + OpenCV to:

1. Open your webcam
2. Detect faces in real time using Haar Cascade
3. Draw a rectangle around faces
4. Show the webcam window
5. Close when you press `Q`
6. Log drowsiness alerts to CSV
7. Generate a graph of alert count over time

---

## Folder Structure

```text
drowsiness_detection/
├─ src/
│  └─ main.py
│  └─ visualize_alerts.py
├─ logs/
│  ├─ alert_log.csv
│  └─ alert_count_over_time.png
├─ requirements.txt
└─ README.md
```

---

## Libraries to Install

You need:

- `opencv-python` (OpenCV library for computer vision)
- `matplotlib` (for graph plotting)

Install command:

```bash
pip install -r requirements.txt
```

---

## How to Run

From the project root folder:

```bash
python src/main.py
```

When the webcam window opens, press `Q` to close.

To generate fatigue graph from the CSV log:

```bash
python src/visualize_alerts.py
```

This saves an image automatically at:

```text
logs/alert_count_over_time.png
```

---

## Simple Explanation of Each File

### `src/main.py`

- Main Python program
- Opens webcam
- Loads Haar Cascade face detector
- Detects faces on each frame
- Draws green rectangles around faces
- Logs drowsiness alert events to CSV
- Shows live video window
- Exits on `Q`

### `src/visualize_alerts.py`

- Reads `logs/alert_log.csv`
- Creates a simple Matplotlib line graph
- X-axis: timestamps
- Y-axis: alert count
- Saves graph image automatically

### `requirements.txt`

- List of Python libraries needed for this project
- Helps you install everything with one command

### `README.md`

- Beginner guide for setup and running
- Explains folder structure and files

---

## Notes for Beginners

- If webcam does not open, close other apps that might be using the camera.
- If `python` command does not work, try `py src/main.py` on Windows.
- Good lighting helps face detection accuracy.
