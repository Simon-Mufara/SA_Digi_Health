r"""
Train a custom YOLOv8 model for more robust detection.

Expected dataset format: Ultralytics YOLO dataset YAML.
Example:
    python train_yolov8.py --data .\dataset\data.yaml --model yolov8n.pt --epochs 100 --imgsz 640
"""

import argparse

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a custom YOLOv8 model.")
    parser.add_argument("--data", required=True, help="Path to dataset YAML (data.yaml)")
    parser.add_argument("--model", default="yolov8n.pt", help="Base model checkpoint")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Training image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--project", default="runs\\detect", help="Output project directory")
    parser.add_argument("--name", default="custom_train", help="Run name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
    )


if __name__ == "__main__":
    main()
