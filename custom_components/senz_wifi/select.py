"""Select platform for the Senz WiFi integration."""

from __future__ import annotations

from dataclasses import dataclass

from senzwifi import RegulationMode
from senzwifi.exceptions import SenzWifiError

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SenzWiFiConfigEntry
from .const import (
    BRAND_NAME,
    MANUFACTURER,
    SUFFIX_REGULATION_MODE,
    SUFFIX_SCHEDULE_SELECT,
)

DOMAIN_PREFIX = "senz_wifi"

REGULATION_MODE_OPTIONS = {
    RegulationMode.SCHEDULE: "Schedule",
    RegulationMode.BOOST: "Boost",
    RegulationMode.MANUAL: "Manual",
    RegulationMode.OFF: "Off",
}

REGULATION_MODE_REVERSE = {v: k for k, v in REGULATION_MODE_OPTIONS.items()}


def _select_regulation_mode(thermostat, option: str):
    """Set the regulation mode on a thermostat."""
    mode = REGULATION_MODE_REVERSE.get(option)
    if mode is None:
        raise ValueError(f"Unknown regulation mode: {option}")
    thermostat.regulation_mode = mode
    return thermostat


def _select_schedule(thermostat, option: str):
    """Set the selected schedule on a thermostat."""
    schedule = next(
        (s for s in thermostat.schedules if s.name == option), None
    )
    if schedule is None:
        raise ValueError(f"Unknown schedule: {option}")
    thermostat.selected_schedule = schedule.number
    return thermostat


@dataclass(frozen=True, kw_only=True)
class SenzWiFiSelectEntityDescription(SelectEntityDescription):
    """Describes a Senz WiFi select entity."""

    options_fn: callable | None = None
    current_option_fn: callable | None = None
    select_option_fn: callable | None = None


SELECT_DESCRIPTIONS: tuple[SenzWiFiSelectEntityDescription, ...] = [
    SenzWiFiSelectEntityDescription(
        key=SUFFIX_REGULATION_MODE,
        translation_key=SUFFIX_REGULATION_MODE,
        name="Regulation mode",
        options_fn=lambda t: list(REGULATION_MODE_OPTIONS.values()),
        current_option_fn=lambda t: REGULATION_MODE_OPTIONS.get(
            t.regulation_mode, "Schedule"
        ),
        select_option_fn=_select_regulation_mode,
    ),
    SenzWiFiSelectEntityDescription(
        key=SUFFIX_SCHEDULE_SELECT,
        translation_key=SUFFIX_SCHEDULE_SELECT,
        name="Schedule",
        options_fn=lambda t: [
            s.name for s in t.schedules if s.name
        ],
        current_option_fn=lambda t: next(
            (s.name for s in t.schedules if s.number == t.selected_schedule),
            None,
        ),
        select_option_fn=_select_schedule,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SenzWiFiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Senz WiFi select entities."""
    coordinator = entry.runtime_data
    thermostats_response = coordinator.data
    all_thermostats = thermostats_response.get_all_thermostats()

    entities: list[SenzWiFiSelectEntity] = []
    for thermostat in all_thermostats:
        for description in SELECT_DESCRIPTIONS:
            entities.append(
                SenzWiFiSelectEntity(coordinator, thermostat, description)
            )

    async_add_entities(entities)


class SenzWiFiSelectEntity(
    CoordinatorEntity[SenzWiFiConfigEntry], SelectEntity
):
    """Representation of a Senz WiFi select entity."""

    entity_description: SenzWiFiSelectEntityDescription
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: SenzWiFiConfigEntry.runtime_data,
        thermostat,
        description: SenzWiFiSelectEntityDescription,
    ) -> None:
        """Initialize the select entity."""
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
    def current_option(self) -> str | None:
        """Return the current selected option."""
        data = self._get_latest_thermostat()
        if data is None:
            return None
        return self.entity_description.current_option_fn(data)

    @property
    def options(self) -> tuple[str, ...]:
        """Return the list of available options."""
        data = self._get_latest_thermostat()
        if data is None:
            return ()
        return tuple(self.entity_description.options_fn(data))

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        data = self._get_latest_thermostat()
        if data is None:
            return

        try:
            updated = self.entity_description.select_option_fn(data, option)
            await self.coordinator.api.update_thermostat(
                updated.serial_number, updated
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
