# Discovery round-trip hotfix

Fixed the ideas/discovery budget mode so `и обратно` is handled as a round-trip request instead of silently returning one-way ideas.

Examples now supported:

```text
из СПб куда угодно в июле до 12000 и обратно
куда слетать из Москвы 10.08-20.08 до 60000 и обратно
из СПб куда угодно туда 06.07-08.07 обратно 14.07-16.07 до 70000
```

Semantics:

- Without `и обратно`, the budget is for one outbound flight.
- With `и обратно`, the budget is for the total pair: outbound + inbound.
- Month-based requests such as `в июле и обратно` use the same month as a flexible window for both legs.
- Exact date ranges such as `10.08-20.08 и обратно` mean outbound on the first date and return on the second date.
- Two explicit ranges mean flexible outbound and return windows.

Main files changed:

- `flight_finder/quick_parser.py`
- `flight_finder/travelpayouts_client.py`
- `flight_finder/formatters.py`
- `flight_finder/bot.py`
- `tests/test_ideas_parser.py`
- `tests/test_ideas_diversity.py`
