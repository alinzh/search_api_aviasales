# Affiliate Tracking Guide

How partner links, cookie tracking and commission attribution work for this bot.

## Overview

This bot uses the **Travelpayouts Partner Links API** to convert raw Aviasales
search URLs into real partner links. Every ticket button in Telegram opens a
short `aviasales.tpm.li/...` (or `aviasales.tp.st/...`) URL that:

1. registers the click in Travelpayouts;
2. sets an affiliate cookie on `aviasales.ru`;
3. redirects to the real Aviasales search page;
4. preserves tracking all the way to booking.

## Configuration

```
TRAVELPAYOUTS_MARKER=412646
TRAVELPAYOUTS_TRS=211747
```

- `TRAVELPAYOUTS_MARKER` — partner ID (lower-left corner of the Travelpayouts
  dashboard).
- `TRAVELPAYOUTS_TRS` — Project ID from
  `https://app.travelpayouts.com/profile/sources` (column "ID").

If `TRAVELPAYOUTS_TRS` is not set, the bot falls back to direct Aviasales URLs
with `?marker=<id>&sub_id=<sub_id>`. Cookie-based tracking is not guaranteed in
fallback mode.

## How a click travels

| Step | Actor | What happens |
|------|-------|--------------|
| 1 | User clicks `aviasales.tpm.li/l15W0xtC` in Telegram | Browser hits the Travelpayouts redirect gateway |
| 2 | `tpm.li` server | Returns HTTP 302 with `Location: https://www.aviasales.ru/search/...?marker=412646...` **and registers the click** |
| 3 | Browser follows 302 | Loads aviasales.ru with `marker=412646` in the URL; Aviasales server reads the marker and stores the affiliate association (cookie) |
| 4 | aviasales.ru JavaScript | `history.replaceState()` cleans the address bar — removes all query params for UX. **This is cosmetic only; tracking already happened on step 2.** |

Final address bar shows a clean URL like
`https://www.aviasales.ru/search/LED1307SHA1` — **this is expected and does
not mean the marker was lost**. The click was registered by `tpm.li` before the
browser ever reached aviasales.ru.

### How to verify the marker is present

Run any of these:

```bash
# Show the redirect Location header (contains marker=412646...)
curl -sI --max-redirs 0 "https://aviasales.tpm.li/l15W0xtC" | grep -i location
```

Or paste the `tpm.li` link into https://linkunshorten.com — the Destination URL
will contain `marker=412646...`.

### Bot log confirmation

After each search the bot logs how many offers were converted:

```
Partner Links API: converted 20/20 offers (marker=412646 trs=211747)
```

`20/20` means every offer URL was successfully turned into a partner link.

## Cookie tracking and cross-search commissions

> When someone clicks your tool, the Partner ID is stored in a cookie on their
> device for 30 days (unless otherwise specified by the program). If they make
> a booking during that time, you receive a commission.
> — Travelpayouts documentation

The cookie is tied to the **partner**, not to a specific flight. So if a user:

1. clicks a partner link from the bot;
2. lands on aviasales.ru;
3. changes the route / dates / destination and searches again;
4. buys a completely different ticket;

...the booking is **still attributed to you**, because the affiliate cookie is
already on their device for 30 days.

### Important caveats

| Caveat | Effect |
|--------|--------|
| **Last-click wins** | If the user clicks another partner's link within the 30-day window, the cookie is overwritten and commission goes to that partner instead. |
| **Incognito / cleared cookies** | If the user browses in incognito mode, clears cookies, or uses a different device/browser, the cookie is absent and the booking is not attributed. |
| **Ad blockers** | Some blockers strip referral/tracking params and may prevent the cookie from being set. |
| **SubID is click-scoped** | The SubID (`tg_multi_city_ist_bkk_20261006`) records which bot scenario produced the click. If the user then buys a different route, the booking still appears under the same SubID in reports — SubID tells you "where the click came from", not "what was bought". |

## SubID format

```
tg_<mode>_<origin>_<destination>_<date>
```

Examples:

| SubID | Meaning |
|-------|---------|
| `tg_quick_led_sha_20260706` | Quick search, LED → SHA, departure 2026-07-06 |
| `tg_multi_city_ist_bkk_20261006` | Multi-city leg, IST → BKK, departure 2026-10-06 |
| `tg_discovery_led_bkk_20260710` | Discovery search, LED → BKK |

Use SubIDs in **Reports → Performance** (filter or group by SubID) to see which
bot scenarios actually drive clicks and bookings.

## Where to check statistics

1. **Travelpayouts dashboard → Reports → Performance.**
2. Filter by SubID to see per-scenario performance.
3. Statistics update with a delay — typically minutes to an hour after the
   click. Bookings may take longer to appear and move through statuses
   (pending → paid).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| No clicks in dashboard | `TRAVELPAYOUTS_MARKER` or `TRAVELPAYOUTS_TRS` not set / wrong | Check `.env` and `Settings.from_env()` |
| Bot log shows `converted 0/N` | Partner Links API error (auth, rate limit, network) | Check bot log for `Partner Links API request failed: ...`; verify token and trs |
| Links look like `aviasales.ru/search/...?marker=412646&sub_id=...` (not `tpm.li`) | Fallback mode — `trs` not set or API failed | Set `TRAVELPAYOUTS_TRS` in `.env` and restart |
| Address bar shows clean URL without marker | Normal — Aviasales JS cleans the URL after tracking | Verify via `curl -sI` that the `tpm.li` redirect carries `marker=412646` |
| Click registered but no booking attributed | Cookie cleared, incognito, ad blocker, or another partner overwrote the cookie | This is expected affiliate-program behavior; nothing to fix in code |

## API limits

- Partner Links API: **100 requests/minute** per marker, up to **10 URLs per
  request**.
- A typical search returns ≤10 offers → 1 batch. Multi-city with 5 routes ×
  ~4 legs → ~2 batches. Well within limits.
- Added latency: ~200–500 ms per batch (synchronous, acceptable for MVP).

## References

- [How to create and use affiliate links](https://support.travelpayouts.com/hc/en-us/articles/360027634052)
- [ID and SubID](https://support.travelpayouts.com/hc/en-us/articles/203955653)
- [Aviasales affiliate links](https://support.travelpayouts.com/hc/en-us/articles/5711895629714)
- [API for Travelpayouts partner links](https://support.travelpayouts.com/hc/en-us/articles/25289759198226)
- [Aviasales Data API](https://support.travelpayouts.com/hc/en-us/articles/203956163)
