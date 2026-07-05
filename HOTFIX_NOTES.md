# Hotfix notes

Fixed startup crash:

- removed invalid `from typing import set` from `flight_finder/config.py`.

Validation performed in the sandbox:

```bash
python -m compileall flight_finder search telegram_bot tests
pytest -q
```

Result: `4 passed`.

Note: the sandbox does not have `pyTelegramBotAPI` installed, so full runtime import of
`telegram_bot.bot` was not checked here. Your local `aviasales` conda env already reaches
`flight_finder/config.py`, so `telebot` is installed there.

The old grep check `grep -c "_with_restart" telegram_bot/bot.py` is no longer valid because
`telegram_bot/bot.py` is now only a compatibility entrypoint. Restart UX is implemented in
`flight_finder/bot.py` via `restart_menu()` and `restart_callback()`.

Use this instead:

```bash
grep -c "restart_callback\|restart_menu" flight_finder/bot.py
```
