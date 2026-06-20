"""Number platform for the Senz WiFi integration."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SenzWiFiConfigEntry
from .const import (
    BRAND_NAME,
    CONF_HEATING_POWER_WATTS,
    DEFAULT_HEATING_POWER_WATTS,
    MANUFACTURER,
)

DOMAIN_PREFIX = "senz_wifi"

HEATING_POWER_NUMBER_DESCRIPTION = NumberEntityDescription(
    key=CONF_HEATING_POWER_WATTS,
    translation_key=CONF_HEATING_POWER_WATTS,
    name="Heating power",
    entity_category=EntityCategory.DIAGNOSTIC,
    native_min_value=100,
    native_max_value=10000,
    native_step=50,
    native_unit_of_measurement=UnitOfPower.WATT,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SenzWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Senz WiFi number entities."""
    coordinator = entry.runtime_data
    thermostats_response = coordinator.data
    all_thermostats = thermostats_response.get_all_thermostats()

    entities: list[SenzWiFiHeatingPowerNumber] = []
    for thermostat in all_thermostats:
        entities.append(
            SenzWiFiHeatingPowerNumber(coordinator, thermostat, entry)
        )

    async_add_entities(entities)


class SenzWiFiHeatingPowerNumber(NumberEntity):
    """Representation of a Senz WiFi heating power number entity."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: SenzWiFiConfigEntry.runtime_data,
        thermostat,
        config_entry: SenzWiFiConfigEntry,
    ) -> None:
        """Initialize the heating power number entity."""
        self._thermostat = thermostat
        self._config_entry = config_entry
        self.entity_description = HEATING_POWER_NUMBER_DESCRIPTION
        self._attr_unique_id = (
            f"{thermostat.serial_number}_{CONF_HEATING_POWER_WATTS}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN_PREFIX, thermostat.serial_number)},
            "name": thermostat.room,
            "manufacturer": MANUFACTURER,
            "model": f"{BRAND_NAME} WiFi Thermostat",
            "sw_version": thermostat.sw_version,
        }

    @property
    def native_value(self) -> float:
        """Return the configured heating power in watts."""
        return self._config_entry.options.get(
            f"{self._thermostat.serial_number}_{CONF_HEATING_POWER_WATTS}",
            DEFAULT_HEATING_POWER_WATTS,
        )

    async def async_set_native_value(self, value: float) -> None:
        """Update the heating power setting."""
        int_value = int(value)
        current_options = dict(self._config_entry.options)
        current_options[
            f"{self._thermostat.serial_number}_{CONF_HEATING_POWER_WATTS}"
        ] = int_value

        self.hass.config_entries.async_update_entry(
            self._config_entry,
            options=current_options,
        )

        # Trigger a state update on all entities
        await self.hass.services.async_call(
            "homeassistant",
            "update_entity",
            {
                "entity_id": [
                    self.entity_id,
                ],
            },
            blocking=True,
        )
