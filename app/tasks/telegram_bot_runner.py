"""
Telegram bot polling entrypoint — used by smarttender_bot Docker service.

Usage:
  python -m app.tasks.telegram_bot_runner
"""

import logging
import sys

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

logger = logging.getLogger("smarttender.bot")


def main() -> None:
    from app.telegram.bot import run_polling
    run_polling()


if __name__ == "__main__":
    main()
