"""Compatibility entrypoint.

Old command:
    python telegram_bot/bot.py

New preferred command:
    python run_bot.py
"""

from flight_finder.bot import main


if __name__ == "__main__":
    main()
