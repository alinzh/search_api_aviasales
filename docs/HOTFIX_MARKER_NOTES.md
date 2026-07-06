# Hotfix: Travelpayouts marker/SubID via Partner Links API

## Problem history

1. The very first patch generated links as `?marker=<partner_id>&sub_id=<sub_id>`.
2. A later hotfix changed the format to `?marker=<partner_id>.<sub_id>` (dot notation). This notation is only valid for White Label URLs, not for direct `www.aviasales.ru/search/...` links. Aviasales stripped the marker on internal redirects, so clicks were not attributed to the partner.
3. On top of that, simply appending `?marker=...` to a direct Aviasales URL never sets the affiliate cookie, so the 30-day tracking window required by Travelpayouts never started.

## Current approach

Links are now produced via the **Travelpayouts Partner Links API**
(`POST https://api.travelpayouts.com/links/v1/create`).

When `TRAVELPAYOUTS_TRS` (Project ID from
`https://app.travelpayouts.com/profile/sources`) is configured together with
`TRAVELPAYOUTS_MARKER`:

1. `_build_ticket_link` returns a **clean Aviasales URL** plus a separate
   `sub_id` (stored in `offer.raw["_sub_id"]`).
2. After search results are collected and ranked, `_convert_links_to_partner`
   batches the URLs (up to 10 per request, per API limits) and POSTs them to
   the Partner Links API.
3. The API returns short `aviasales.tp.st/...` (or `aviasales.tpo.li/...`)
   partner URLs that:
   - register the click in Travelpayouts;
   - set the 30-day affiliate cookie;
   - redirect to the real Aviasales search page;
   - preserve tracking all the way to booking.
4. `offer.link` is rewritten in place with the partner URL.

## Fallback

If `TRAVELPAYOUTS_TRS` is not set, or the Partner Links API call fails
(network error, invalid token, rate limit), each offer falls back to a direct
Aviasales URL with **separate** query params:

```
?marker=<partner_id>&sub_id=<sub_id>
```

This is the safest manual format for direct Aviasales URLs. Cookie-based
tracking is not guaranteed in fallback mode, but the marker is at least valid
and visible to Aviasales on the initial page load.

## Configuration

```
TRAVELPAYOUTS_MARKER=412646
TRAVELPAYOUTS_TRS=211747
```

`TRAVELPAYOUTS_TRS` is the numeric Project ID from the Travelpayouts dashboard
(`https://app.travelpayouts.com/profile/sources`, column "ID").

## Limits

- Partner Links API: 100 requests/minute per marker, up to 10 URLs per request.
- A typical search returns ≤10 offers → 1 batch; multi-city with 5 routes ×
  ~4 legs → ~2 batches. Well within limits.
- Added latency: ~200-500ms per batch (synchronous, acceptable for MVP).
