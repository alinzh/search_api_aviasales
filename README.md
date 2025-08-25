# search_api_aviasales

---

[![OSA-improved](https://img.shields.io/badge/improved%20by-OSA-yellow)](https://github.com/aimclub/OSA)

---

## Overview

search_api_aviasales helps users easily find the best and most affordable flight routes across multiple cities, offering advanced filters and personalized options. Through an intuitive Telegram bot, it simplifies trip planning by guiding users to discover more flexible and cost-effective travel solutions than typical flight search platforms.

---

## Table of Contents

- [Core features](#core-features)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Contributing](#contributing)
- [Citation](#citation)

---
## Core features

1. **Flexible Multi-City Flight Search**: Allows users to search for aviatickets across 2 to 6 cities, supporting complex itineraries with customizable travel periods, time spent in each city, and both roundtrip or one-way options.
2. **Telegram Bot Integration**: Provides a Telegram bot interface so that users can interact with the flight search engine through a conversational UI without coding knowledge.
3. **Advanced Filtering Options**: Supports detailed filters, including exclusion of specific airlines, minimum transit times, and precise date/period selection for departure and return flights.
4. **Graph-Based Route Optimization**: Utilizes a graph data model and search algorithms (such as DFS on MultiDiGraphs) to construct and evaluate all possible flight routes, optimizing for cost or travel time.
5. **Result Sorting and Comparison**: Sorts and presents possible routes by lowest price and shortest total travel time, allowing users to choose the best option according to their preferences.

---

## Installation

Install search_api_aviasales using one of the following methods:

**Build from source:**

1. Clone the search_api_aviasales repository:
```sh
git clone https://github.com/alinzh/search_api_aviasales
```

2. Navigate to the project directory:
```sh
cd search_api_aviasales
```
## Getting Started

You can start using the project by interacting with the Telegram bot:

- Link to the bot: [https://t.me/search_avia_bot](https://t.me/search_avia_bot)
- Watch a demo video: [Video with bot](https://github.com/alinzh/search_api_aviasales/assets/124587537/738c9d29-fa38-4168-8c31-1734a6817716)

The bot allows you to search for airline tickets based on complex filters such as multiple cities, desired time spent in each city, custom periods for your trip, and airline exclusions. No coding knowledge is required to use the Telegram bot.

Additionally, you can use the Search class directly in your code for custom integrations. 

A diagram of the project structure is available below:

![uml_03_07_2023 (1)](https://github.com/alinzh/search_api_aviasales/assets/124587537/ab6e3f4b-4a1a-472a-9a81-d99c33dcaeb3)

---

## Contributing

- **[Report Issues](https://github.com/alinzh/search_api_aviasales/issues)**: Submit bugs found or log feature requests for the project.

- **[Submit Pull Requests](https://github.com/alinzh/search_api_aviasales/tree/master/.github/CONTRIBUTING.md)**: To learn more about making a contribution to search_api_aviasales.

---

## Citation

If you use this software, please cite it as below.

### APA format:

    alinzh (2023). search_api_aviasales repository [Computer software]. https://github.com/alinzh/search_api_aviasales

### BibTeX format:

    @misc{search_api_aviasales,

        author = {alinzh},

        title = {search_api_aviasales repository},

        year = {2023},

        publisher = {github.com},

        journal = {github.com repository},

        howpublished = {\url{https://github.com/alinzh/search_api_aviasales.git}},

        url = {https://github.com/alinzh/search_api_aviasales.git}

    }

---
