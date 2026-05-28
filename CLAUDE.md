# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Home Assistant **custom integration** (not a standalone Python package) that periodically
aggregates power/energy sensor values and POSTs them to ChargeHQ's Solar/Battery Push API
(or any compatible endpoint). All shippable code lives in
`custom_components/chargehq_push_api_poster/`.

It is a `cloud_push` / `service` integration: it pushes data outward on a timer. There is no
data being pulled *into* Home Assistant, so it deliberately does **not** use HA's standard
`DataUpdateCoordinator`.

## Development workflow

There is no build, no dependency manifest, and no test suite in this repo — it runs inside a
Home Assistant install. The dev loop is:

1. Copy/symlink `custom_components/chargehq_push_api_poster/` into a HA instance's
   `config/custom_components/` directory.
2. Restart Home Assistant.
3. Reproduce via **Settings → Devices & Services → Add Integration → "ChargeHQ Push API Poster"**.
4. Enable debug logging in the HA instance's `configuration.yaml`:
   ```yaml
   logger:
     logs:
       custom_components.chargehq_push_api_poster: debug
   ```

Runtime dependencies (`aiohttp`, `voluptuous`, `homeassistant`) are provided by the HA
environment, not installed here. `manifest.json` declares no extra `requirements`.

### Releasing

Version is the `version` field in `manifest.json`; HACS reads it. The release convention
(see `git log`) is a single commit titled `"<version> <summary>"` that bumps that field.
Minimum supported HA version is pinned in `hacs.json` (`2023.1.0`).

## Architecture

Data flows in one direction every `interval` seconds:

```
HA sensor states ──► EnergyPosterCoordinator ──► EnergyPosterApiClient ──► ChargeHQ HTTP endpoint
                              │
                              └─► last_posted_data ──► LastPostedDataSensor (UI monitoring)
```

- `__init__.py` — wires everything on `async_setup_entry`: reads `entry.data`, gets HA's
  shared aiohttp session via `async_get_clientsession`, builds the API client + coordinator,
  stores the coordinator in `hass.data[DOMAIN][entry.entry_id]`, starts it, and forwards the
  `sensor` platform.
- `coordinator.py` — the core. Uses `async_track_time_interval` (a plain timer), not a
  pull coordinator. Does an immediate post on start, then every `interval`. `_get_sensor_sum`
  / `_get_sensor_value` read live `hass.states`, do unit conversion, and tolerate missing or
  non-numeric states. Caches the most recent payload in `self.last_posted_data`.
- `api.py` — stateless POST client. Builds the `{apiKey, tsms, siteMeters{...}}` JSON payload
  and returns `bool` for success; never raises (logs and returns `False`).
- `config_flow.py` — UI setup **and** options flow. See gotcha below.
- `sensor.py` — `LastPostedDataSensor`, a display-only entity reading from the coordinator.
- `const.py` — `DOMAIN` and all `CONF_*` keys; the single source of truth for config keys.

### Payload contract (ChargeHQ API)

```jsonc
{
  "apiKey": "...",
  "tsms": 1702400000000,          // epoch milliseconds
  "siteMeters": {
    "consumption_kw": 5.5,         // sum of all consumption sensors
    "production_kw":  3.2,         // sum of all solar sensors
    "net_import_kw":  2.3,         // consumption_kw - production_kw (negative = exporting)
    "imported_kwh":   123.45,      // optional, only if a sensor is configured
    "exported_kwh":   67.89        // optional, only if a sensor is configured
  }
}
```

## Project-specific gotchas

- **Internal name ≠ public name.** The domain and product name are
  `chargehq_push_api_poster` / "ChargeHQ Push API Poster", but the classes and the config
  entry title are still the legacy `EnergyPoster*` / "Energy Poster". This is intentional
  drift from a rename — don't "fix" one side in isolation; the config entry title in
  `config_flow.py` is user-visible.
- **Options flow writes to `entry.data`, not `entry.options`.** Reconfiguration mutates
  `data` directly (`async_update_entry(..., data=...)`) and relies on the update listener in
  `__init__.py` to fully reload the entry. Consequently the setup and options schemas in
  `config_flow.py` are duplicated and must be kept in sync by hand.
- **Unit conversion is exact-string-matched.** `coordinator.py` only recognises the literal
  units `"W"`/`"kW"` (power) and `"Wh"`/`"kWh"` (energy). Anything else — including a missing
  unit — is assumed to already be in the base unit (kW/kWh) and logged as a warning. Missing
  or non-numeric power sensors count as `0.0`; energy sensors return `None` and are omitted.
- **Two independent timers.** The coordinator posts every `interval` seconds (min 30), while
  `LastPostedDataSensor` re-renders every 1 second so the UI stays current between posts.
- **Local brand images.** `custom_components/chargehq_push_api_poster/brand/` ships
  `icon.png` (256×256) and `icon@2x.png` (512×512) per HA 2026.3's brands proxy API; these
  override the brands CDN with no extra config. The entity icon (`manifest.json` `"icon"`,
  and `mdi:post` in `sensor.py`) is unrelated to these brand assets.
