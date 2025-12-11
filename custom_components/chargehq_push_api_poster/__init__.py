"""The Energy Poster integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnergyPosterApiClient
from .const import (
    CONF_API_KEY,
    CONF_API_URL,
    CONF_CONSUMPTION_SENSORS,
    CONF_INTERVAL,
    CONF_SOLAR_SENSORS,
    DEFAULT_INTERVAL,
    DOMAIN,
)
from .coordinator import EnergyPosterCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Energy Poster from a config entry."""
    _LOGGER.info("Setting up Energy Poster integration")

    # Get configuration from entry
    api_url = entry.data[CONF_API_URL]
    api_key = entry.data[CONF_API_KEY]
    consumption_sensors = entry.data[CONF_CONSUMPTION_SENSORS]
    solar_sensors = entry.data[CONF_SOLAR_SENSORS]
    interval = entry.data.get(CONF_INTERVAL, DEFAULT_INTERVAL)

    # Get the shared aiohttp session
    session = async_get_clientsession(hass)

    # Create the API client
    api_client = EnergyPosterApiClient(
        session=session,
        api_url=api_url,
        api_key=api_key,
    )

    # Create the coordinator
    coordinator = EnergyPosterCoordinator(
        hass=hass,
        api_client=api_client,
        consumption_sensors=consumption_sensors,
        solar_sensors=solar_sensors,
        interval=interval,
    )

    # Store the coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Start the coordinator
    await coordinator.async_start()

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Energy Poster integration")

    # Get the coordinator
    coordinator: EnergyPosterCoordinator = hass.data[DOMAIN].pop(entry.entry_id)

    # Stop the coordinator
    await coordinator.async_stop()

    # Clean up domain data if empty
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.info("Reloading ChargeHQ Push API Poster integration due to options change")
    await hass.config_entries.async_reload(entry.entry_id)

