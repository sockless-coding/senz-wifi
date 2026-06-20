"""Diagnostics for the Senz WiFi integration."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from . import SenzWiFiConfigEntry

TO_REDACT = {CONF_PASSWORD, CONF_EMAIL}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    thermostats_response = coordinator.data
    all_thermostats = thermostats_response.get_all_thermostats()

    thermostat_data = []
    for t in all_thermostats:
        thermostat_data.append(
            {
                "serial_number": t.serial_number,
                "room": t.room,
                "group_name": t.group_name,
                "temperature_celsius": t.temperature_celsius,
                "regulation_mode": t.regulation_mode,
                "online": t.online,
                "heating": t.heating,
                "vacation_enabled": t.vacation_enabled,
                "comfort_temperature_celsius": t.comfort_temperature_celsius,
                "manual_temperature_celsius": t.manual_temperature_celsius,
                "frost_temperature_celsius": t.frost_temperature_celsius,
                "frost_protection_is_enabled": t.frost_protection_is_enabled,
                "early_start_of_heating": t.early_start_of_heating,
                "error_code": t.error_code,
                "sw_version": t.sw_version,
                "selected_schedule": t.selected_schedule,
                "min_temp_celsius": t.min_temp_celsius,
                "max_temp_celsius": t.max_temp_celsius,
            }
        )

    return {
        "config_entry": async_redact_data(entry.data, TO_REDACT),
        "thermostats": thermostat_data,
    }
