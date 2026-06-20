"""Switch platform for the Senz WiFi integration."""

from __future__ import annotations

from dataclasses import dataclass

from senzwifi.exceptions import SenzWifiError

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SenzWiFiConfigEntry
from .const import (
    BRAND_NAME,
    MANUFACTURER,
    SUFFIX_EARLY_START,
    SUFFIX_FROST_PROTECTION,
    SUFFIX_VACATION_MODE,
)

DOMAIN_PREFIX = "senz_wifi"


@dataclass(frozen=True, kw_only=True)
class SenzWiFiSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Senz WiFi switch entity."""

    is_on_fn: callable | None = None
    set_on_fn: callable | None = None
    set_off_fn: callable | None = None


SWITCH_DESCRIPTIONS: tuple[SenzWiFiSwitchEntityDescription, ...] = [
    SenzWiFiSwitchEntityDescription(
        key=SUFFIX_VACATION_MODE,
        translation_key=SUFFIX_VACATION_MODE,
        name="Vacation mode",
        is_on_fn=lambda t: t.vacation_enabled,
        set_on_fn=lambda t: setattr(t, "vacation_enabled", True),
        set_off_fn=lambda t: setattr(t, "vacation_enabled", False),
    ),
    SenzWiFiSwitchEntityDescription(
        key=SUFFIX_FROST_PROTECTION,
        translation_key=SUFFIX_FROST_PROTECTION,
        name="Frost protection",
        is_on_fn=lambda t: t.frost_protection_is_enabled,
        set_on_fn=lambda t: setattr(t, "frost_protection_is_enabled", True),
        set_off_fn=lambda t: setattr(t, "frost_protection_is_enabled", False),
    ),
    SenzWiFiSwitchEntityDescription(
        key=SUFFIX_EARLY_START,
        translation_key=SUFFIX_EARLY_START,
        name="Early start",
        is_on_fn=lambda t: t.early_start_of_heating,
        set_on_fn=lambda t: setattr(t, "early_start_of_heating", True),
        set_off_fn=lambda t: setattr(t, "early_start_of_heating", False),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SenzWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Senz WiFi switch entities."""
    coordinator = entry.runtime_data
    thermostats_response = coordinator.data
    all_thermostats = thermostats_response.get_all_thermostats()

    entities: list[SenzWiFiSwitchEntity] = []
    for thermostat in all_thermostats:
        for description in SWITCH_DESCRIPTIONS:
            entities.append(
                SenzWiFiSwitchEntity(coordinator, thermostat, description)
            )

    async_add_entities(entities)


class SenzWiFiSwitchEntity(
    CoordinatorEntity[SenzWiFiConfigEntry], SwitchEntity
):
    """Representation of a Senz WiFi switch entity."""

    entity_description: SenzWiFiSwitchEntityDescription
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: SenzWiFiConfigEntry.runtime_data,
        thermostat,
        description: SenzWiFiSwitchEntityDescription,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._thermostat = thermostat
        self.entity_description = description
        self._attr_translation_key = description.translation_key
        self._attr_name = description.name
        self._attr_unique_id = (
            f"{thermostat.serial_number}_{description.key}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN_PREFIX, thermostat.serial_number)},
            "name": thermostat.room,
            "manufacturer": MANUFACTURER,
            "model": f"{BRAND_NAME} WiFi Thermostat",
            "sw_version": thermostat.sw_version,
        }

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        data = self._get_latest_thermostat()
        if data is None:
            return None
        return self.entity_description.is_on_fn(data)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        data = self._get_latest_thermostat()
        if data is None:
            return

        self.entity_description.set_on_fn(data)
        await self._update_thermostat(data)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        data = self._get_latest_thermostat()
        if data is None:
            return

        self.entity_description.set_off_fn(data)
        await self._update_thermostat(data)

    async def _update_thermostat(self, data) -> None:
        """Send the updated thermostat data to the API."""
        try:
            await self.coordinator.api.update_thermostat(
                data.serial_number, data
            )
        except SenzWifiError as err:
            raise HomeAssistantError(
                f"Failed to update {data.room}: {err}"
            ) from err

    def _get_latest_thermostat(self):
        """Get the latest thermostat data from the coordinator."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get_thermostat(
            self._thermostat.serial_number
        )
