import sys

from rb.safe_matching_common.essay import (
    DEFAULT_ESSAY_MODEL,
    create_essay,
    ensure_essay_model,
)
from rb.safe_matching_common.privacy import redact_text


def main(image_path: str, model: str) -> None:
    ensure_essay_model(model)
    essay = create_essay(image_path, model)
    redacted = redact_text(essay)
    print(f"Raw essay:\n{essay}\n")
    print(f"Redacted essay (what would be uploaded):\n{redacted}\n")
    print(f"Words: {len(redacted.split())}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else DEFAULT_ESSAY_MODEL)
