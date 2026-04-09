"""
Simple real-time object detection with OpenCV + YOLOv8 (Ultralytics).

Requirements:
    pip install ultralytics opencv-python yara-python
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import cv2
import yara
from ultralytics import YOLO


WINDOW_NAME = "YOLOv8 Webcam Detection"
BUTTON_X1, BUTTON_Y1, BUTTON_X2, BUTTON_Y2 = 20, 50, 280, 90


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run webcam YOLO detection with YARA alerting.")
    parser.add_argument("--model", default="yolov8n.pt", help="YOLO model path (.pt)")
    parser.add_argument("--camera", type=int, default=0, help="Webcam index")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--output", default="detections.json", help="Detections JSON output path")
    parser.add_argument("--rules", default="lab_safety_violation.yar", help="YARA rule file path")
    parser.add_argument("--user", default="", help="Session user name label")
    parser.add_argument("--users-db", default="users.json", help="Path to saved user names JSON")
    return parser.parse_args()


def load_users(users_db_file: Path) -> list[str]:
    if not users_db_file.exists():
        users_db_file.write_text("[]", encoding="utf-8")
        return []
    users = json.loads(users_db_file.read_text(encoding="utf-8"))
    if not isinstance(users, list):
        raise ValueError("Users DB must be a JSON list of names.")
    cleaned = [str(name).strip() for name in users if str(name).strip()]
    return sorted(set(cleaned))


def save_users(users_db_file: Path, users: list[str]) -> None:
    users_db_file.write_text(json.dumps(sorted(set(users)), indent=2), encoding="utf-8")


def on_mouse(event: int, x: int, y: int, flags: int, state: dict) -> None:
    _ = flags
    if event == cv2.EVENT_LBUTTONDOWN:
        in_button = BUTTON_X1 <= x <= BUTTON_X2 and BUTTON_Y1 <= y <= BUTTON_Y2
        if in_button:
            state["request_name_change"] = True


def main() -> None:
    args = parse_args()

    # Load a small YOLOv8 model.
    # It will auto-download on first run if not already present.
    model = YOLO(args.model)

    # Open the selected webcam index.
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open webcam (index {args.camera}).")

    # Output file where detections will be stored.
    output_file = Path(args.output)
    yara_rule_file = Path(args.rules)
    users_db_file = Path(args.users_db)

    users = load_users(users_db_file)

    # Non-biometric identity label (user-provided).
    user_name = args.user.strip()
    if not user_name:
        user_name = input("Enter your name for this session: ").strip() or "unknown_user"
    if user_name not in users:
        users.append(user_name)
        save_users(users_db_file, users)

    # Keep detections in memory so the JSON file is always valid JSON.
    detections_log = []
    output_file.write_text("[]", encoding="utf-8")

    if not yara_rule_file.exists():
        raise FileNotFoundError(f"YARA rule file not found: {yara_rule_file.resolve()}")

    # Compile the YARA rule once, then reuse it for each frame.
    rules = yara.compile(filepath=str(yara_rule_file))

    # Face presence detector (not biometric identification).
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    if face_cascade.empty():
        raise RuntimeError("Failed to load OpenCV face cascade classifier.")

    print("Starting detection... Press 'q' in the video window to quit.")
    print(f"Session user label: {user_name}")
    print(f"Saving detections to: {output_file.resolve()}")
    print(f"Saved users DB: {users_db_file.resolve()}")
    print(f"Loaded YARA rule: {yara_rule_file.resolve()}")
    print("Click 'Add/Change User' button or press 'n' to change active user.")

    state = {"request_name_change": False}
    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse, state)

    # Process webcam frames continuously.
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Warning: Failed to read frame from webcam.")
            break

        if state["request_name_change"]:
            entered_name = input("Enter user name: ").strip()
            if entered_name:
                user_name = entered_name
                if user_name not in users:
                    users.append(user_name)
                    save_users(users_db_file, users)
                print(f"Active user changed to: {user_name}")
            state["request_name_change"] = False

        # Run inference on the current frame.
        results = model(frame, verbose=False, conf=args.conf)
        result = results[0]

        # Timestamp for detections from this frame.
        timestamp = datetime.now().isoformat(timespec="milliseconds")

        # Detect faces for user-presence checks (not identity matching).
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        face_detected = len(faces) > 0
        for (fx, fy, fw, fh) in faces:
            cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (255, 200, 0), 2)
            cv2.putText(
                frame,
                f"Face present: {user_name}",
                (fx, max(20, fy - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 200, 0),
                2,
            )

        # Structured detection records from this frame.
        frame_detections = []

        # Draw each detection as a rectangle + class label.
        for box in result.boxes:
            # Bounding box coordinates (x1, y1, x2, y2).
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

            # Class index -> readable class name.
            cls_id = int(box.cls[0].item())
            class_name = model.names.get(cls_id, str(cls_id))

            # Confidence score (0.0 to 1.0).
            conf = float(box.conf[0].item())
            label = f"{class_name} {conf:.2f}"

            # Save a structured detection record.
            frame_detections.append(
                {
                    "object_name": class_name,
                    "confidence_score": round(conf, 4),
                    "timestamp": timestamp,
                    "user_name": user_name,
                    "face_detected": face_detected,
                }
            )

            # Draw rectangle around object.
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw label above the rectangle.
            cv2.putText(
                frame,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

        # Persist detections continuously.
        if frame_detections:
            detections_log.extend(frame_detections)
            output_file.write_text(
                json.dumps(detections_log, indent=2),
                encoding="utf-8",
            )

            unique_names = sorted({item["object_name"] for item in frame_detections})
            # Print detected object names once per frame (unique values only).
            print(f"Detected ({user_name}):", ", ".join(unique_names))

            # Match detected object names against the YARA rule.
            detection_text = " ".join(unique_names)
            matches = rules.match(data=detection_text)
            if matches:
                matched_rule_names = ", ".join(match.rule for match in matches)
                print(f"YARA MATCH ({user_name}): {matched_rule_names}")
                cv2.putText(
                    frame,
                    f"ALERT: {matched_rule_names}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 0, 255),
                    3,
                )

        # Draw simple UI controls and active user label.
        cv2.rectangle(frame, (BUTTON_X1, BUTTON_Y1), (BUTTON_X2, BUTTON_Y2), (80, 80, 80), -1)
        cv2.rectangle(frame, (BUTTON_X1, BUTTON_Y1), (BUTTON_X2, BUTTON_Y2), (255, 255, 255), 2)
        cv2.putText(
            frame,
            "Add/Change User (click or 'n')",
            (BUTTON_X1 + 8, BUTTON_Y1 + 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        cv2.putText(
            frame,
            f"Active user: {user_name}",
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        # Show the annotated frame.
        cv2.imshow(WINDOW_NAME, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("n"):
            state["request_name_change"] = True
        # Exit on 'q'.
        if key == ord("q"):
            break

    # Clean up resources.
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
