"""Binary sensor platform for the Senz WiFi integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SenzWiFiConfigEntry
from .const import (
    BRAND_NAME,
    MANUFACTURER,
    SUFFIX_HEATING,
    SUFFIX_ONLINE,
)

DOMAIN_PREFIX = "senz_wifi"


@dataclass(frozen=True, kw_only=True)
class SenzWiFiBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Senz WiFi binary sensor entity."""

    is_on_fn: callable | None = None


BINARY_SENSOR_DESCRIPTIONS: tuple[
    SenzWiFiBinarySensorEntityDescription, ...
] = [
    SenzWiFiBinarySensorEntityDescription(
        key=SUFFIX_ONLINE,
        translation_key=SUFFIX_ONLINE,
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda t: t.online,
    ),
    SenzWiFiBinarySensorEntityDescription(
        key=SUFFIX_HEATING,
        translation_key=SUFFIX_HEATING,
        name="Heating",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=lambda t: t.heating,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SenzWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Senz WiFi binary sensor entities."""
    coordinator = entry.runtime_data
    thermostats_response = coordinator.data
    all_thermostats = thermostats_response.get_all_thermostats()

    entities: list[SenzWiFiBinarySensorEntity] = []
    for thermostat in all_thermostats:
        for description in BINARY_SENSOR_DESCRIPTIONS:
            entities.append(
                SenzWiFiBinarySensorEntity(
                    coordinator, thermostat, description
                )
            )

    async_add_entities(entities)


class SenzWiFiBinarySensorEntity(
    CoordinatorEntity[SenzWiFiConfigEntry], BinarySensorEntity
):
    """Representation of a Senz WiFi binary sensor entity."""

    entity_description: SenzWiFiBinarySensorEntityDescription
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: SenzWiFiConfigEntry.runtime_data,
        thermostat,
        description: SenzWiFiBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor entity."""
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
        """Return True if the binary sensor is on."""
        data = self._get_latest_thermostat()
        if data is None:
            return None
        return self.entity_description.is_on_fn(data)

    def _get_latest_thermostat(self):
        """Get the latest thermostat data from the coordinator."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get_thermostat(
            self._thermostat.serial_number
        )
