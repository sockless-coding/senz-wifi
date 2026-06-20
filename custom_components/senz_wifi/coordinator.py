"""Coordinator for the Senz WiFi integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from senzwifi import AsyncSenzWifi, ThermostatsResponse
from senzwifi.exceptions import AuthenticationError, SenzWifiError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SenzWiFiCoordinator(DataUpdateCoordinator[ThermostatsResponse]):
    """Class to manage fetching data from the Senz WiFi API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: AsyncSenzWifi,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
            always_update=True,
        )
        self.api = api

    @classmethod
    def create_and_setup(
        cls,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> SenzWiFiCoordinator:
        """Create the coordinator and authenticate."""
        api = AsyncSenzWifi(
            email=config_entry.data[CONF_EMAIL],
            password=config_entry.data[CONF_PASSWORD],
            max_retries=DEFAULT_MAX_RETRIES,
            timeout=DEFAULT_TIMEOUT,
        )
        coordinator = cls(hass, config_entry, api)
        return coordinator

    async def _async_update_data(self) -> ThermostatsResponse:
        """Fetch data from the Senz WiFi API."""
        try:
            await self.api._ensure_authenticated()
            return await self.api.get_thermostats()
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(
                "Authentication with Senz WiFi failed"
            ) from err
        except SenzWifiError as err:
            raise UpdateFailed(f"Error communicating with Senz WiFi API: {err}") from err

    async def async_shutdown(self) -> None:
        """Shutdown the API client."""
        pass
