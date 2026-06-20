"""Climate platform for the Senz WiFi integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from senzwifi import RegulationMode
from senzwifi.exceptions import SenzWifiError

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.climate.const import PRESET_NONE
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SenzWiFiConfigEntry
from .const import (
    BRAND_NAME,
    DOMAIN,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)

PRESET_BOOST = "boost"

HVAC_MODES = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]
PRESET_MODES = [PRESET_NONE, PRESET_BOOST]

# Mapping from Senz regulation mode to HA HVAC mode
REGULATION_TO_HVAC = {
    RegulationMode.SCHEDULE: HVACMode.AUTO,
    RegulationMode.BOOST: HVACMode.HEAT,
    RegulationMode.MANUAL: HVACMode.HEAT,
    RegulationMode.OFF: HVACMode.OFF,
}

# Default temperature step
TARGET_TEMP_STEP = 0.5


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SenzWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Senz WiFi climate entities."""
    coordinator = entry.runtime_data

    thermostats_response = coordinator.data
    all_thermostats = thermostats_response.get_all_thermostats()

    async_add_entities(
        SenzWiFiClimateEntity(coordinator, thermostat)
        for thermostat in all_thermostats
    )


class SenzWiFiClimateEntity(CoordinatorEntity[SenzWiFiConfigEntry], ClimateEntity):
    """Representation of a Senz WiFi thermostat as a climate entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_fan_mode = None
    _attr_fan_modes = None
    _attr_hvac_modes = HVAC_MODES
    _attr_preset_modes = PRESET_MODES
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = TARGET_TEMP_STEP
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )

    def __init__(
        self,
        coordinator: SenzWiFiConfigEntry.runtime_data,
        thermostat,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._thermostat = thermostat
        self._attr_unique_id = thermostat.serial_number
        self._attr_device_info = {
            "identifiers": {(DOMAIN, thermostat.serial_number)},
            "name": thermostat.room,
            "manufacturer": MANUFACTURER,
            "model": f"{BRAND_NAME} WiFi Thermostat",
            "sw_version": thermostat.sw_version,
        }

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        data = self._get_latest_thermostat()
        return data.temperature_celsius if data else None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        data = self._get_latest_thermostat()
        if data is None:
            return None
        # In manual mode the setpoint is manual_temperature,
        # in boost mode it's comfort_temperature, in schedule mode
        # we still show manual_temperature as the current setpoint.
        return data.manual_temperature_celsius

    @property
    def target_temperature_low(self) -> float | None:
        """Return the low target temperature."""
        data = self._get_latest_thermostat()
        return data.min_temp_celsius if data else None

    @property
    def target_temperature_high(self) -> float | None:
        """Return the high target temperature."""
        data = self._get_latest_thermostat()
        return data.max_temp_celsius if data else None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        data = self._get_latest_thermostat()
        if data is None:
            return HVACMode.OFF
        return REGULATION_TO_HVAC.get(data.regulation_mode, HVACMode.AUTO)

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation if away."""
        data = self._get_latest_thermostat()
        if data is None:
            return HVACAction.OFF
        if data.regulation_mode == RegulationMode.OFF:
            return HVACAction.OFF
        if data.heating:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def preset_mode(self) -> str:
        """Return the current preset mode."""
        data = self._get_latest_thermostat()
        if data is None:
            return PRESET_NONE
        if data.regulation_mode == RegulationMode.BOOST:
            return PRESET_BOOST
        return PRESET_NONE

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        data = self._get_latest_thermostat()
        if data is None:
            return

        if hvac_mode == HVACMode.OFF:
            try:
                await self.coordinator.api.turn_off(data.serial_number)
            except SenzWifiError as err:
                raise HomeAssistantError(
                    f"Failed to turn off {data.room}: {err}"
                ) from err
            return

        if hvac_mode == HVACMode.HEAT:
            # Switch to manual mode keeping current manual temperature
            temp = data.manual_temperature_celsius
            try:
                await self.coordinator.api.set_manual_temperature(
                    data.serial_number, temp
                )
            except SenzWifiError as err:
                raise HomeAssistantError(
                    f"Failed to set manual mode on {data.room}: {err}"
                ) from err
            return

        if hvac_mode == HVACMode.AUTO:
            # Switch back to schedule mode
            try:
                data.regulation_mode = RegulationMode.SCHEDULE
                await self.coordinator.api.update_thermostat(
                    data.serial_number, data
                )
            except SenzWifiError as err:
                raise HomeAssistantError(
                    f"Failed to set schedule mode on {data.room}: {err}"
                ) from err
            return

        raise HomeAssistantError(f"Unsupported HVAC mode: {hvac_mode}")

    async def async_set_temperature(
        self,
        temperature: float | None = None,
        hvac_mode: HVACMode | None = None,
        **kwargs,
    ) -> None:
        """Set new target temperature."""
        if temperature is None:
            return

        data = self._get_latest_thermostat()
        if data is None:
            return

        # Clamp to valid range
        min_temp = data.min_temp_celsius
        max_temp = data.max_temp_celsius
        temperature = max(min_temp, min(max_temp, temperature))

        # If an hvac_mode is specified, set that first
        if hvac_mode is not None and hvac_mode != self.hvac_mode:
            await self.async_set_hvac_mode(hvac_mode)

        try:
            await self.coordinator.api.set_manual_temperature(
                data.serial_number, temperature
            )
        except SenzWifiError as err:
            raise HomeAssistantError(
                f"Failed to set temperature on {data.room}: {err}"
            ) from err

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode."""
        data = self._get_latest_thermostat()
        if data is None:
            return

        if preset_mode == PRESET_BOOST:
            try:
                await self.coordinator.api.start_boost(data.serial_number)
            except SenzWifiError as err:
                raise HomeAssistantError(
                    f"Failed to start boost on {data.room}: {err}"
                ) from err
            return

        if preset_mode == PRESET_NONE:
            # Return to schedule mode
            try:
                data.regulation_mode = RegulationMode.SCHEDULE
                await self.coordinator.api.update_thermostat(
                    data.serial_number, data
                )
            except SenzWifiError as err:
                raise HomeAssistantError(
                    f"Failed to set schedule mode on {data.room}: {err}"
                ) from err
            return

        raise HomeAssistantError(f"Unsupported preset mode: {preset_mode}")

    async def async_select_preset_mode(self, preset_mode: str) -> None:
        """Select a preset mode (alias for async_set_preset_mode)."""
        await self.async_set_preset_mode(preset_mode)

    def _get_latest_thermostat(self):
        """Get the latest thermostat data from the coordinator."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get_thermostat(
            self._thermostat.serial_number
        )
