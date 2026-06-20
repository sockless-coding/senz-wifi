"""Sensor platform for the Senz WiFi integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SenzWiFiConfigEntry
from .const import (
    BRAND_NAME,
    CONF_HEATING_POWER_WATTS,
    DEFAULT_HEATING_POWER_WATTS,
    MANUFACTURER,
    SUFFIX_BOOST_FLOOR_TEMPERATURE,
    SUFFIX_BOOST_ROOM_TEMPERATURE,
    SUFFIX_COMFORT_END_TIME,
    SUFFIX_COMFORT_TEMPERATURE,
    SUFFIX_CURRENT_TEMPERATURE,
    SUFFIX_ENERGY,
    SUFFIX_ERROR_CODE,
    SUFFIX_FROST_TEMPERATURE,
    SUFFIX_POWER,
    SUFFIX_SELECTED_SCHEDULE,
    SUFFIX_SOFTWARE_VERSION,
    SUFFIX_VACATION_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN_PREFIX = "senz_wifi"


def _parse_timestamp(value: str | None) -> datetime | None:
    """Parse a timestamp string from the API into a datetime object.

    The API returns timestamps in format like "13-11-2024 16:00:00+00:00".
    """
    if value is None:
        return None
    try:
        # Format: DD-MM-YYYY HH:MM:SS+00:00
        return datetime.strptime(value, "%d-%m-%Y %H:%M:%S%z")
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True, kw_only=True)
class SenzWiFiSensorEntityDescription(SensorEntityDescription):
    """Describes a Senz WiFi sensor entity."""

    value_fn: callable | None = None
    extra_attrs_fn: callable | None = None


SENSOR_DESCRIPTIONS: tuple[SenzWiFiSensorEntityDescription, ...] = [
    SenzWiFiSensorEntityDescription(
        key=SUFFIX_CURRENT_TEMPERATURE,
        translation_key=SUFFIX_CURRENT_TEMPERATURE,
        name="Current temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda t: t.temperature_celsius,
    ),
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
        value_fn=lambda t: _parse_timestamp(t.comfort_end_time),
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

        # Add power sensor
        entities.append(
            SenzWiFiPowerSensor(coordinator, thermostat)
        )

        # Add energy sensor
        entities.append(
            SenzWiFiEnergySensor(coordinator, thermostat)
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


class SenzWiFiPowerSensor(
    CoordinatorEntity[SenzWiFiConfigEntry], SensorEntity
):
    """Representation of a Senz WiFi power sensor.

    Reports the current power consumption based on whether heating is active.
    When heating is on, reports the configured heating power in watts.
    When heating is off, reports 0 watts.
    """

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_suggested_unit_of_measurement = UnitOfPower.WATT

    def __init__(
        self,
        coordinator: SenzWiFiConfigEntry.runtime_data,
        thermostat,
    ) -> None:
        """Initialize the power sensor."""
        super().__init__(coordinator)
        self._thermostat = thermostat
        self._attr_unique_id = (
            f"{thermostat.serial_number}_{SUFFIX_POWER}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN_PREFIX, thermostat.serial_number)},
            "name": thermostat.room,
            "manufacturer": MANUFACTURER,
            "model": f"{BRAND_NAME} WiFi Thermostat",
            "sw_version": thermostat.sw_version,
        }

    @property
    def _heating_power_watts(self) -> int:
        """Get the configured heating power from the config entry options."""
        return self.coordinator.config_entry.options.get(
            f"{self._thermostat.serial_number}_{CONF_HEATING_POWER_WATTS}",
            DEFAULT_HEATING_POWER_WATTS,
        )

    @property
    def native_value(self) -> StateType:
        """Return the current power consumption in watts."""
        data = self._get_latest_thermostat()
        if data is None:
            return None
        if data.heating:
            return self._heating_power_watts
        return 0

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "heating_power_watts": self._heating_power_watts,
        }

    def _get_latest_thermostat(self):
        """Get the latest thermostat data from the coordinator."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get_thermostat(
            self._thermostat.serial_number
        )


class SenzWiFiEnergySensor(
    CoordinatorEntity[SenzWiFiConfigEntry], SensorEntity, RestoreEntity
):
    """Representation of a Senz WiFi energy sensor.

    Tracks cumulative energy consumption in kWh based on heating activity.
    Uses the configured heating power and the heating state to calculate
    energy consumption over time.
    """

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(
        self,
        coordinator: SenzWiFiConfigEntry.runtime_data,
        thermostat,
    ) -> None:
        """Initialize the energy sensor."""
        super().__init__(coordinator)
        self._thermostat = thermostat
        self._attr_unique_id = (
            f"{thermostat.serial_number}_{SUFFIX_ENERGY}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN_PREFIX, thermostat.serial_number)},
            "name": thermostat.room,
            "manufacturer": MANUFACTURER,
            "model": f"{BRAND_NAME} WiFi Thermostat",
            "sw_version": thermostat.sw_version,
        }
        self._energy_kwh: float = 0.0
        self._last_heating_state: bool | None = None
        self._last_update_time: datetime | None = None

    @property
    def _heating_power_watts(self) -> int:
        """Get the configured heating power from the config entry options."""
        return self.coordinator.config_entry.options.get(
            f"{self._thermostat.serial_number}_{CONF_HEATING_POWER_WATTS}",
            DEFAULT_HEATING_POWER_WATTS,
        )

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()

        # Try to restore previous state
        last_state = await self.async_get_last_state()
        if last_state is not None:
            try:
                self._energy_kwh = float(last_state.state)
            except (ValueError, TypeError):
                self._energy_kwh = 0.0

        # Also restore last heating state from attributes
        if last_state is not None:
            self._last_heating_state = last_state.attributes.get(
                "_last_heating_state"
            )

        # Get last restored time from state
        if last_state is not None:
            self._last_update_time = last_state.last_updated

    @property
    def native_value(self) -> StateType:
        """Return the current energy consumption in kWh."""
        data = self._get_latest_thermostat()
        if data is None:
            return self._energy_kwh

        now = datetime.now(timezone.utc)

        if self._last_update_time is not None:
            # Calculate energy consumed since last update
            elapsed_seconds = (now - self._last_update_time).total_seconds()

            if self._last_heating_state is not None and elapsed_seconds > 0:
                # If heating was on during the last interval, add energy
                if self._last_heating_state:
                    energy_added = (
                        self._heating_power_watts
                        * elapsed_seconds
                        / 3600000  # W * s / (W*h per kWh * 3600 s/h)
                    )
                    self._energy_kwh += energy_added

        self._last_heating_state = data.heating
        self._last_update_time = now

        return round(self._energy_kwh, 3)

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "heating_power_watts": self._heating_power_watts,
            "_last_heating_state": self._last_heating_state,
        }

    def _get_latest_thermostat(self):
        """Get the latest thermostat data from the coordinator."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get_thermostat(
            self._thermostat.serial_number
        )

    async def async_options_updated(self, config_entry: ConfigEntry) -> None:
        """Handle options update."""
        self._heating_power_watts = config_entry.options.get(
            f"{self._thermostat.serial_number}_{CONF_HEATING_POWER_WATTS}",
            DEFAULT_HEATING_POWER_WATTS,
        )
        self.async_write_ha_state()
