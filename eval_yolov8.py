r"""
Evaluate a trained YOLOv8 model on a validation set.

Example:
    python eval_yolov8.py --model runs\detect\custom_train\weights\best.pt --data .\dataset\data.yaml
"""

import argparse

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a YOLOv8 model.")
    parser.add_argument("--model", required=True, help="Path to model checkpoint (.pt)")
    parser.add_argument("--data", required=True, help="Path to dataset YAML (data.yaml)")
    parser.add_argument("--imgsz", type=int, default=640, help="Validation image size")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)
    metrics = model.val(data=args.data, imgsz=args.imgsz)
    print("Evaluation complete.")
    print(metrics)


if __name__ == "__main__":
    main()
