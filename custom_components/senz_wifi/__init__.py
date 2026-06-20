"""The Senz WiFi integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import voluptuous as vol

from senzwifi.exceptions import SenzWifiError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    CONF_DURATION_MINUTES,
    CONF_HEATING_POWER_WATTS,
    DEFAULT_BOOST_DURATION_MINUTES,
    DEFAULT_HEATING_POWER_WATTS,
    DOMAIN,
    SERVICE_BOOST,
)
from .coordinator import SenzWiFiCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

BOOST_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_DURATION_MINUTES,
            default=DEFAULT_BOOST_DURATION_MINUTES,
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
    }
)

type SenzWiFiConfigEntry = ConfigEntry[SenzWiFiCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SenzWiFiConfigEntry,
) -> bool:
    """Set up Senz WiFi from a config entry."""
    coordinator = await SenzWiFiCoordinator.create_and_setup(hass, entry)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:  # noqa: BLE001
        _LOGGER.exception("Failed to fetch initial data: %s", err)
        await coordinator.async_shutdown()
        raise

    entry.runtime_data = coordinator

    # Store serial numbers in options for the options flow
    thermostats_response = coordinator.data
    all_thermostats = thermostats_response.get_all_thermostats()
    serial_numbers = [t.serial_number for t in all_thermostats]

    current_options = dict(entry.options)
    current_options["serial_numbers"] = serial_numbers

    # Set default heating power for each thermostat if not already set
    for serial in serial_numbers:
        key = f"{serial}_{CONF_HEATING_POWER_WATTS}"
        if key not in current_options:
            current_options[key] = DEFAULT_HEATING_POWER_WATTS

    if current_options != entry.options:
        hass.config_entries.async_update_entry(
            entry,
            options=current_options,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register boost service
    async def handle_boost_service(call) -> None:
        """Handle the boost service call."""
        entity_id = call.data[ATTR_ENTITY_ID]
        duration_minutes = call.data[CONF_DURATION_MINUTES]

        # Resolve entity to get the thermostat serial number
        state = hass.states.get(entity_id)
        if state is None:
            raise HomeAssistantError(f"Entity {entity_id} not found")

        # Extract serial number from unique_id
        entity_registry = await async_get_entity_registry(hass)
        entity_entry = entity_registry.async_get(entity_id)
        if entity_entry is None:
            raise HomeAssistantError(
                f"Entity {entity_id} not found in registry"
            )

        serial_number = entity_entry.unique_id
        if not serial_number:
            raise HomeAssistantError(
                f"Entity {entity_id} has no unique_id"
            )

        end_time = datetime.now(timezone.utc) + timedelta(
            minutes=duration_minutes
        )

        try:
            await coordinator.api.start_boost(serial_number, end_time)
        except SenzWifiError as err:
            raise HomeAssistantError(
                f"Failed to boost thermostat {serial_number}: {err}"
            ) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_BOOST,
        handle_boost_service,
        schema=BOOST_SERVICE_SCHEMA,
    )

    return True


async def async_options_flow(
    hass: HomeAssistant,
    entry: SenzWiFiConfigEntry,
):
    """Handle options flow."""
    from .config_flow import SenzWiFiOptionsFlowHandler

    return SenzWiFiOptionsFlowHandler()


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SenzWiFiConfigEntry,
) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_shutdown()
        hass.services.async_remove(DOMAIN, SERVICE_BOOST)

    return unload_ok
