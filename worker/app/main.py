"""Worker process entry point."""

import logging

from app.events.consumer import consume


def main() -> None:
    """Configure logging and start the SQS consumer loop."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    consume()


if __name__ == "__main__":
    main()
