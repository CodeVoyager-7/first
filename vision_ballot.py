from __future__ import annotations

import argparse
import json
from pathlib import Path

from ballot_recognition.vision_model import VisionBallotRecognizer


DEFAULT_IMAGE = Path("samples/ballot_sample.png")
DEFAULT_OUTPUT = Path("output/vision_result.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recognize a ballot image with a vision model.")
    parser.add_argument("--image", default=str(DEFAULT_IMAGE), help="Path to the ballot image.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path to save the JSON result.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    image_path = Path(args.image)
    output_path = Path(args.output)
    if not image_path.exists():
        raise FileNotFoundError(f"Ballot image not found: {image_path}")

    recognizer = VisionBallotRecognizer()
    result = recognizer.recognize_with_fallback(image_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    print("Vision recognition complete.")
    print(f"Image: {image_path}")
    print(f"Result JSON: {output_path}")
    print(f"Title: {result.title or 'N/A'}")
    if result.abnormal_details.get("error_message"):
        print(f"Recognition error: {result.abnormal_details['error_message']}")

    print("\nOptions:")
    for code, label in result.option_labels.items():
        print(f"  {code}: {label}")

    print("\nVote summary:")
    for option_code, count in result.summary.items():
        print(f"  {option_code}: {count}")

    print("\nRows:")
    for row in result.rows:
        selected = row.selected_option or "none"
        issue = f" ({row.issue})" if row.issue else ""
        print(f"  Row {row.row_index:02d} | {row.candidate_name} | {selected}{issue}")


if __name__ == "__main__":
    main()
