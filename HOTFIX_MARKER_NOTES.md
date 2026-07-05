# Hotfix: Travelpayouts marker/SubID

The previous patch generated links as:

```text
?marker=<partner_id>&sub_id=<sub_id>
```

This is not the safest manual format for direct Aviasales URLs. The safer direct-link format is now:

```text
?marker=<partner_id>.<sub_id>
```

The separate `sub_id` field is still valid when using the Travelpayouts Partner Links API (`/links/v1/create`), but the bot currently builds direct links without calling that API.
