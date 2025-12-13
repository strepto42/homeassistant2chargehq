"""Sensor platform for ChargeHQ Push API Poster."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

from .const import DOMAIN
from .coordinator import EnergyPosterCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: EnergyPosterCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LastPostedDataSensor(coordinator, entry.entry_id)], True)


class LastPostedDataSensor(SensorEntity):
    """Sensor showing the last posted data."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, coordinator: EnergyPosterCoordinator, entry_id: str
    ) -> None:
        """Initialise the sensor."""
        self._coordinator = coordinator
        self._attr_name = "Last Posted Data"
        self._attr_unique_id = f"{entry_id}_last_posted_data"
        self._unsub_refresh = None

    async def async_added_to_hass(self) -> None:
        """Handle entity added to Home Assistant."""
        # Schedule periodic updates every second to refresh the display
        self._unsub_refresh = async_track_time_interval(
            self.hass,
            self._async_refresh,
            timedelta(seconds=1),
        )

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None

    @callback
    def _async_refresh(self, _: Any) -> None:
        """Refresh the sensor state."""
        self.async_write_ha_state()

    @property
    def state(self) -> str:
        """Return the state."""
        if self._coordinator.last_posted_data:
            return "Posted"
        return "No data"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self._coordinator.last_posted_data:
            return {}

        # Return all posted data as attributes
        return self._coordinator.last_posted_data

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:post"

