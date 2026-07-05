# Flexible Flight Finder — UX-патч для `search_api_aviasales`

Это версия, в которой фокус смещён с длинного пошагового сценария Telegram-бота на продуктовый UX:

- быстрый поиск **одной фразой**;
- режим «куда можно улететь в страну/регион»;
- фильтры по цене, пересадкам и длительности в пути;
- карточки результатов вместо длинной простыни текста;
- affiliate-friendly ссылки через `TRAVELPAYOUTS_MARKER` и `sub_id`;
- простая SQLite-аналитика поисков;
- заготовка price alerts;
- совместимые entrypoints: `python run_bot.py` и `python telegram_bot/bot.py`.

## Пример запроса

```text
из СПб в Китай 06.07-14.07 до 70000 до 1 пересадки до 18ч
```

Бот распарсит:

- город отправления: Санкт-Петербург / `LED`;
- направление: Китай, несколько IATA-кодов из `data/countries.json`;
- даты: 06.07–14.07;
- цена: до 70 000 ₽;
- пересадки: максимум 1;
- длительность: максимум 18 часов.

## Как запустить

```bash
cp .env.example .env
# Заполни TELEGRAM_BOT_TOKEN и AVIASALES_TOKEN
pip install -r requirements.txt
python run_bot.py
```

Через Docker:

```bash
cp .env.example .env
docker compose up --build
```

## Что улучшено в UX

### Было

Пользователь проходил длинную цепочку вопросов: город, дата, тип маршрута, конечный город, дата, промежуточные города, транзит, исключения, старт поиска. Это тяжело продавать обычному пользователю.

### Стало

Главный сценарий начинается с понятного меню:

```text
🚀 Быстрый поиск одной фразой
🌏 Куда можно улететь в страну/регион
🧭 Multi-city маршрут
💡 Примеры
```

Пользователь может просто написать:

```text
из Москвы в Таиланд 10.08-20.08 до 60000
```

Результаты отправляются карточками:

```text
#1 🇨🇳 Шанхай — 42 300 ₽
Санкт-Петербург → Шанхай
🕒 06.07.2026 13:40, в пути 13ч 40м
🔁 1 пересадка
✈️ Turkish Airlines
[Открыть билет]
```

## Где добавлять города и страны

- `data/city2code.json` — алиасы городов и IATA-коды.
- `data/countries.json` — страна/регион → список IATA-кодов.
- `data/airlines.json` — IATA-код авиакомпании → читаемое название.

Это сделано специально: можно быстро расширять покрытие без переписывания логики бота.

## Монетизация

### 1. Affiliate links

Если задан `TRAVELPAYOUTS_MARKER`, ссылки на билеты автоматически получают:

- `marker=<TRAVELPAYOUTS_MARKER>`;
- `sub_id=tg_<mode>_<origin>_<destination>_<date>`.

Так можно понимать, какие сценарии реально дают клики и покупки: Китай, Таиланд, multi-city, alerts и т.д.

### 2. Freemium

В эту сборку легко добавить лимиты:

- бесплатно: 5 поисков в день, 1 price alert;
- платно: больше поисков, больше alerts, расширенные страны, экспорт, daily digest.

Место для лимитов: `flight_finder/storage.py` + middleware в `flight_finder/bot.py`.

### 3. Price alerts

Кнопка «Следить за ценой» уже сохраняет запрос в SQLite. Следующий шаг — cron/worker, который раз в несколько часов вызывает `TravelpayoutsClient.search()` и отправляет уведомление, если цена ниже `threshold_price`.

## Структура

```text
flight_finder/
  bot.py                  # новый Telegram UX
  quick_parser.py          # парсер запросов одной фразой
  travelpayouts_client.py  # клиент Aviasales/Travelpayouts Data API
  formatters.py            # карточки и тексты
  directories.py           # города/страны/авиакомпании
  storage.py               # SQLite: searches + price_alerts
search/search.py           # совместимый wrapper для старого import
telegram_bot/bot.py        # совместимый старый entrypoint
```

## Что ещё стоит сделать следующим PR

1. Добавить полноценный `APScheduler` или Celery/Redis для price alerts.
2. Сделать Telegram Mini App для формы фильтров.
3. Подключить нормальную базу аэропортов/городов вместо маленького JSON.
4. Добавить rate limiting и daily limits для freemium.
5. Сделать `admin`-команды только для `ADMIN_TELEGRAM_IDS`.
6. Добавить web landing с SEO-страницами: «куда улететь из СПб в Китай в июле».
