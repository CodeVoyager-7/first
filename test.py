from __future__ import annotations

import argparse
import base64
import os
from pathlib import Path

from zai import ZhipuAiClient


DEFAULT_IMAGE = Path("samples/ballot_sample.png")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke test Zhipu/GLM image understanding with one local image.")
    parser.add_argument("--image", default=str(DEFAULT_IMAGE), help="Path to the image for a quick vision-model test.")
    parser.add_argument("--model", default="glm-4.6v", help="Zhipu vision model name.")
    parser.add_argument("--prompt", default="Describe this image.", help="Prompt sent with the image.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    api_key = os.getenv("VISION_MODEL_API_KEY")
    if not api_key:
        raise RuntimeError("Please set VISION_MODEL_API_KEY before running this script.")

    image_path = Path(args.image)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    img_base = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    client = ZhipuAiClient(api_key=api_key)
    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": img_base}},
                    {"type": "text", "text": args.prompt},
                ],
            }
        ],
        thinking={"type": "enabled"},
    )
    print(response.choices[0].message)


if __name__ == "__main__":
    main()
