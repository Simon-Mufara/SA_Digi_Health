"""
Scan object detection JSON output with YARA rules.

Usage:
    python yara_json_scanner.py
    python yara_json_scanner.py --rules lab_safety_violation.yar --input detections.json
"""

import argparse
import json
from pathlib import Path

import yara


def build_scan_text(detections: list[dict]) -> str:
    """Convert JSON detections into flat text that YARA can scan."""
    parts: list[str] = []
    for item in detections:
        object_name = str(item.get("object_name", ""))
        confidence = str(item.get("confidence_score", ""))
        timestamp = str(item.get("timestamp", ""))
        parts.append(
            f"object_name:{object_name} confidence_score:{confidence} timestamp:{timestamp}"
        )
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run YARA rules on detection JSON.")
    parser.add_argument("--rules", default="lab_safety_violation.yar", help="Path to YARA rules file")
    parser.add_argument("--input", default="detections.json", help="Path to detection JSON file")
    args = parser.parse_args()

    rules_path = Path(args.rules)
    input_path = Path(args.input)

    if not rules_path.exists():
        raise FileNotFoundError(f"Rules file not found: {rules_path.resolve()}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON file not found: {input_path.resolve()}")

    # 1) Load YARA rules from file.
    rules = yara.compile(filepath=str(rules_path))

    # 2) Read JSON detection output.
    with input_path.open("r", encoding="utf-8") as f:
        detections = json.load(f)

    if not isinstance(detections, list):
        raise ValueError("Expected a JSON array of detection objects.")

    # 3) Convert JSON records to scan text.
    scan_text = build_scan_text(detections)

    # 4) Run YARA matching.
    matches = rules.match(data=scan_text)

    # 5) Print alerts when rules match.
    if matches:
        print("ALERT: YARA rules matched.")
        for match in matches:
            print(f"- {match.rule}")
    else:
        print("No YARA matches.")


if __name__ == "__main__":
    main()
