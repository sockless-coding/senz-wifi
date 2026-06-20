# Senz WiFi Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

A [Home Assistant](https://www.home-assistant.io/) custom integration for [Senz WiFi](https://www.senz.co.nz/) (Pentair Thermal WiFi) smart underfloor heating thermostats.

## Features

- **Climate entity** per thermostat with full control:
  - HVAC modes: Auto (schedule), Heat (manual), Off
  - Preset modes: Boost
  - Temperature setting with min/max clamping
  - Current temperature, target temperature, and HVAC action reporting
- **Sensor entities** per thermostat:
  - Comfort temperature
  - Vacation temperature
  - Frost temperature
  - Boost floor temperature
  - Boost room temperature
  - Boost end time (timestamp)
  - Error code (diagnostic)
  - Software version (diagnostic)
  - Selected schedule (diagnostic)
- **Binary sensor entities** per thermostat:
  - Online status (diagnostic)
  - Heating active
- **Switch entities** per thermostat:
  - Vacation mode
  - Frost protection
  - Early start of heating
- **Select entities** per thermostat:
  - Regulation mode (Schedule / Boost / Manual / Off)
  - Schedule selection (from available schedules)
- **Boost service** — start boost/comfort mode with configurable duration
- **Diagnostics** — download config entry diagnostics (credentials redacted)
- **Re-authentication flow** — automatically prompts for new credentials if the session expires

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Click **Explore & Download Repositories**
3. Search for **Senz WiFi**
4. Click **Download**
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/senz_wifi` folder into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **Senz WiFi**
4. Enter your Senz WiFi account email and password
5. The integration will discover all thermostats in your account

## Entities

Each thermostat is created as a device with the following entities:

| Entity | Domain | Description |
|--------|--------|-------------|
| `{room}` | `climate` | Main thermostat control |
| Comfort temperature | `sensor` | Comfort/boost temperature setpoint |
| Vacation temperature | `sensor` | Vacation mode temperature |
| Frost temperature | `sensor` | Frost protection temperature |
| Boost floor temperature | `sensor` | Boost floor temperature setpoint |
| Boost room temperature | `sensor` | Boost room temperature setpoint |
| Boost end time | `sensor` | When the current boost will end |
| Error code | `sensor` | Device error code (0 = no error) |
| Software version | `sensor` | Thermostat firmware version |
| Selected schedule | `sensor` | Currently active schedule number |
| Online | `binary_sensor` | Whether the thermostat is online |
| Heating | `binary_sensor` | Whether heating is currently active |
| Vacation mode | `switch` | Toggle vacation mode |
| Frost protection | `switch` | Toggle frost protection |
| Early start | `switch` | Toggle early start of heating |
| Regulation mode | `select` | Set regulation mode (Schedule/Boost/Manual/Off) |
| Schedule | `select` | Select active schedule |

## Services

### `senz_wifi.boost`

Start boost/comfort mode on a thermostat.

**Service data:**

| Field | Required | Description |
|-------|----------|-------------|
| `entity_id` | Yes | The climate entity to boost |
| `duration_minutes` | No | Duration in minutes (default: 180, max: 1440) |

**Example automation:**

```yaml
automation:
  - alias: "Boost living room in the morning"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: senz_wifi.boost
        target:
          entity_id: climate.living_room
        data:
          duration_minutes: 120
```

## Requirements

- Home Assistant 2024.1.0 or later
- `senzwifi` Python package (installed automatically)

## Troubleshooting

- **Authentication errors**: If your credentials are no longer valid, the integration will prompt you to re-authenticate via the config flow.
- **No entities created**: Ensure your thermostats are online and accessible via the Senz WiFi API.
- **Slow updates**: The integration polls the cloud API every 30 seconds. This is the expected behavior for a cloud-based integration.

## License

MIT License — see [LICENSE](LICENSE) for details.
