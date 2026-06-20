"""Sensor platform for the Senz WiFi integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SenzWiFiConfigEntry
from .const import (
    BRAND_NAME,
    MANUFACTURER,
    SUFFIX_BOOST_FLOOR_TEMPERATURE,
    SUFFIX_BOOST_ROOM_TEMPERATURE,
    SUFFIX_COMFORT_END_TIME,
    SUFFIX_COMFORT_TEMPERATURE,
    SUFFIX_ERROR_CODE,
    SUFFIX_FROST_TEMPERATURE,
    SUFFIX_SELECTED_SCHEDULE,
    SUFFIX_SOFTWARE_VERSION,
    SUFFIX_VACATION_TEMPERATURE,
)

DOMAIN_PREFIX = "senz_wifi"


@dataclass(frozen=True, kw_only=True)
class SenzWiFiSensorEntityDescription(SensorEntityDescription):
    """Describes a Senz WiFi sensor entity."""

    value_fn: callable | None = None
    extra_attrs_fn: callable | None = None


SENSOR_DESCRIPTIONS: tuple[SenzWiFiSensorEntityDescription, ...] = [
    SenzWiFiSensorEntityDescription(
        key=SUFFIX_COMFORT_TEMPERATURE,
        translation_key=SUFFIX_COMFORT_TEMPERATURE,
        name="Comfort temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda t: t.comfort_temperature_celsius,
    ),
    SenzWiFiSensorEntityDescription(
        key=SUFFIX_VACATION_TEMPERATURE,
        translation_key=SUFFIX_VACATION_TEMPERATURE,
        name="Vacation temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda t: t.vacation_temperature_celsius,
    ),
    SenzWiFiSensorEntityDescription(
        key=SUFFIX_FROST_TEMPERATURE,
        translation_key=SUFFIX_FROST_TEMPERATURE,
        name="Frost temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda t: t.frost_temperature_celsius,
    ),
    SenzWiFiSensorEntityDescription(
        key=SUFFIX_BOOST_FLOOR_TEMPERATURE,
        translation_key=SUFFIX_BOOST_FLOOR_TEMPERATURE,
        name="Boost floor temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda t: t.boost_floor_temp_celsius,
    ),
    SenzWiFiSensorEntityDescription(
        key=SUFFIX_BOOST_ROOM_TEMPERATURE,
        translation_key=SUFFIX_BOOST_ROOM_TEMPERATURE,
        name="Boost room temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda t: t.boost_room_temp_celsius,
    ),
    SenzWiFiSensorEntityDescription(
        key=SUFFIX_COMFORT_END_TIME,
        translation_key=SUFFIX_COMFORT_END_TIME,
        name="Boost end time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda t: t.comfort_end_time,
    ),
    SenzWiFiSensorEntityDescription(
        key=SUFFIX_ERROR_CODE,
        translation_key=SUFFIX_ERROR_CODE,
        name="Error code",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda t: t.error_code,
    ),
    SenzWiFiSensorEntityDescription(
        key=SUFFIX_SOFTWARE_VERSION,
        translation_key=SUFFIX_SOFTWARE_VERSION,
        name="Software version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda t: t.sw_version,
    ),
    SenzWiFiSensorEntityDescription(
        key=SUFFIX_SELECTED_SCHEDULE,
        translation_key=SUFFIX_SELECTED_SCHEDULE,
        name="Selected schedule",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda t: t.selected_schedule,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SenzWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Senz WiFi sensor entities."""
    coordinator = entry.runtime_data
    thermostats_response = coordinator.data
    all_thermostats = thermostats_response.get_all_thermostats()

    entities: list[SenzWiFiSensorEntity] = []
    for thermostat in all_thermostats:
        for description in SENSOR_DESCRIPTIONS:
            entities.append(
                SenzWiFiSensorEntity(coordinator, thermostat, description)
            )

    async_add_entities(entities)


class SenzWiFiSensorEntity(
    CoordinatorEntity[SenzWiFiConfigEntry], SensorEntity
):
    """Representation of a Senz WiFi sensor entity."""

    entity_description: SenzWiFiSensorEntityDescription
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: SenzWiFiConfigEntry.runtime_data,
        thermostat,
        description: SenzWiFiSensorEntityDescription,
    ) -> None:
        """Initialize the sensor entity."""
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
    def native_value(self) -> StateType:
        """Return the current value of the sensor."""
        data = self._get_latest_thermostat()
        if data is None:
            return None
        return self.entity_description.value_fn(data)

    def _get_latest_thermostat(self):
        """Get the latest thermostat data from the coordinator."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get_thermostat(
            self._thermostat.serial_number
        )
