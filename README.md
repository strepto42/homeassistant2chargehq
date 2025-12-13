# ChargeHQ Push API Poster

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration to post production/consumption data to ChargeHQ (or any compatible API endpoint).

## Overview

This custom integration for Home Assistant periodically aggregates energy data from your consumption and solar production sensors, then posts it to a configurable API endpoint. It's designed to work with [ChargeHQ](https://chargehq.net/) but can be used with any API that accepts the same JSON structure.

## Features

- **Configurable interval**: Set how often data is posted (default: 30 seconds, minimum: 30 seconds)
- **Multiple sensors**: Aggregate multiple consumption and solar production sensors
- **Optional energy totals**: Optionally include imported and exported kWh totals
- **Monitoring sensor**: Built-in sensor entity to display last posted data
- **Config flow**: Easy setup through the Home Assistant UI
- **HACS compatible**: Install via HACS custom repository
- **Async**: Fully asynchronous using Home Assistant's shared aiohttp session
- **Robust error handling**: Gracefully handles missing sensors and non-numeric states

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Add"
7. Search for "ChargeHQ Push API Poster" and install it
8. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/chargehq_push_api_poster` folder from this repository
2. Copy it to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "ChargeHQ Push API Poster"
4. Fill in the configuration:
   - **API URL**: The endpoint to POST data to (e.g., `https://api.chargehq.net/api/public/push-solar-data`)
   - **API Key**: Your ChargeHQ API key
   - **Consumption Sensors**: Select one or more sensors measuring power consumption (in kW)
   - **Solar Production Sensors**: Select one or more sensors measuring solar production (in kW)
   - **Imported Energy Sensor** (Optional): Select a sensor measuring total imported energy (in kWh)
   - **Exported Energy Sensor** (Optional): Select a sensor measuring total exported energy (in kWh)
   - **Update Interval**: How often to send data (in seconds, minimum: 30, default: 30)

### Monitoring

After setup, a **Last Posted Data** sensor entity is automatically created. This sensor:
- Shows state as "Posted" when data is being sent successfully
- Displays all posted values as entity attributes
- Can be added to dashboards for real-time monitoring
- Updates every second to keep display current

## API Payload Format

The integration posts JSON data in the following format:

### Basic Format (Required Fields)
```json
{
  "apiKey": "<your_api_key>",
  "tsms": 1702400000000,
  "siteMeters": {
    "consumption_kw": 5.5,
    "net_import_kw": 2.3,
    "production_kw": 3.2
  }
}
```

### Extended Format (With Optional Fields)
```json
{
  "apiKey": "<your_api_key>",
  "tsms": 1702400000000,
  "siteMeters": {
    "consumption_kw": 5.5,
    "net_import_kw": 2.3,
    "production_kw": 3.2,
    "imported_kwh": 123.45,
    "exported_kwh": 67.89
  }
}
```

Where:
- `tsms`: Timestamp in milliseconds
- `consumption_kw`: Sum of all consumption sensor values (required)
- `production_kw`: Sum of all solar production sensor values (required)
- `net_import_kw`: `consumption_kw - production_kw` (negative means exporting) (required)
- `imported_kwh`: Total imported energy from grid (optional, only sent if configured)
- `exported_kwh`: Total exported energy to grid (optional, only sent if configured)

## Sensor Requirements

### Power Sensors (Consumption & Solar Production)
Your power sensors should:
- Report values in **kilowatts (kW)** or **watts (W)**
- Be of the `sensor` domain
- Have numeric states
- Have a `unit_of_measurement` attribute set to one of: `W`, `kW`, `watt`, `watts`, `kilowatt`, `kilowatts`

The integration automatically converts watts to kilowatts. If no unit is specified, the value is assumed to be in kW.

### Energy Sensors (Imported & Exported kWh - Optional)
Your energy sensors should:
- Report values in **kilowatt-hours (kWh)** or **watt-hours (Wh)**
- Be of the `sensor` domain
- Have numeric states
- Have a `unit_of_measurement` attribute set to one of: `Wh`, `kWh`, `watthour`, `watthours`, `kilowatthour`, `kilowatthours`

The integration automatically converts watt-hours to kilowatt-hours. If no unit is specified, the value is assumed to be in kWh.

### Error Handling
If a sensor is unavailable or has a non-numeric state, it will be treated as `0.0`.

## Troubleshooting

### Enable Debug Logging

Add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.chargehq_push_api_poster: debug
```

### Common Issues

- **No data being posted**: Check that your sensors exist and have numeric values
- **API errors**: Verify your API URL and API key are correct
- **Missing sensors warning**: Ensure all configured sensor entity IDs are valid

## File Structure

```
custom_components/
└── chargehq_push_api_poster/
    ├── __init__.py          # Integration setup and teardown
    ├── api.py               # API client for posting data
    ├── config_flow.py       # Configuration UI flow
    ├── const.py             # Constants and configuration keys
    ├── coordinator.py       # Timer-based data aggregation and posting
    ├── sensor.py            # Monitoring sensor entity
    ├── manifest.json        # Integration manifest
    ├── strings.json         # UI strings
    └── translations/
        └── en.json          # English translations
```

## ChargeHQ Setup

1. Sign up at [ChargeHQ](https://chargehq.net/)
2. Go to your account settings
3. Find your API key under the "Solar / Battery Push API" section
4. Use `https://api.chargehq.net/api/public/push-solar-data` as the API URL

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
