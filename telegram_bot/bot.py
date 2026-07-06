"""Compatibility entrypoint.

Old command:
    python telegram_bot/bot.py

New preferred command:
    python run_bot.py

The old implementation kept most handlers in this file, including restart helpers.
The new UX implementation moved handlers to flight_finder.bot; restart behavior is
implemented there via restart_menu() and restart_callback().
"""

from flight_finder.bot import main


if __name__ == "__main__":
    main()
