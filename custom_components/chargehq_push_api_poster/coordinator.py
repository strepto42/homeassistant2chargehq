"""Coordinator for Energy Poster integration."""
from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .api import EnergyPosterApiClient

_LOGGER = logging.getLogger(__name__)


class EnergyPosterCoordinator:
    """Coordinator to handle periodic energy data posting."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: EnergyPosterApiClient,
        consumption_sensors: list[str],
        solar_sensors: list[str],
        interval: int,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: The Home Assistant instance.
            api_client: The API client to post data.
            consumption_sensors: List of consumption sensor entity IDs.
            solar_sensors: List of solar production sensor entity IDs.
            interval: Interval in seconds between posts.
        """
        self._hass = hass
        self._api_client = api_client
        self._consumption_sensors = consumption_sensors
        self._solar_sensors = solar_sensors
        self._interval = interval
        self._unsub_timer: Any = None

    async def async_start(self) -> None:
        """Start the coordinator and schedule periodic updates."""
        _LOGGER.info(
            "Starting Energy Poster coordinator with %d consumption sensors, "
            "%d solar sensors, interval=%d seconds",
            len(self._consumption_sensors),
            len(self._solar_sensors),
            self._interval,
        )

        # Perform an initial post
        await self._async_post_energy_data()

        # Schedule periodic updates
        self._unsub_timer = async_track_time_interval(
            self._hass,
            self._async_scheduled_post,
            timedelta(seconds=self._interval),
        )

    async def async_stop(self) -> None:
        """Stop the coordinator and cancel scheduled updates."""
        _LOGGER.info("Stopping ChargeHQ Push API Poster coordinator")
        if self._unsub_timer is not None:
            self._unsub_timer()
            self._unsub_timer = None

    @callback
    def _async_scheduled_post(self, _: Any) -> None:
        """Handle scheduled post (callback wrapper)."""
        self._hass.async_create_task(self._async_post_energy_data())

    async def _async_post_energy_data(self) -> None:
        """Aggregate sensor data and post to the API."""
        consumption_kw = self._get_sensor_sum(self._consumption_sensors)
        production_kw = self._get_sensor_sum(self._solar_sensors)
        net_import_kw = consumption_kw - production_kw
        timestamp_ms = int(time.time() * 1000)

        _LOGGER.debug(
            "Aggregated energy data: consumption=%.2f kW, production=%.2f kW, "
            "net_import=%.2f kW, timestamp=%d",
            consumption_kw,
            production_kw,
            net_import_kw,
            timestamp_ms,
        )

        await self._api_client.post_energy_data(
            timestamp_ms=timestamp_ms,
            consumption_kw=consumption_kw,
            production_kw=production_kw,
            net_import_kw=net_import_kw,
        )

    def _get_sensor_sum(self, entity_ids: list[str]) -> float:
        """Sum the values of multiple sensors.

        Args:
            entity_ids: List of sensor entity IDs to sum.

        Returns:
            The sum of all sensor values. Non-numeric or missing states are treated as 0.0.
        """
        total = 0.0
        for entity_id in entity_ids:
            state = self._hass.states.get(entity_id)
            if state is None:
                _LOGGER.warning("Sensor %s not found, treating as 0.0", entity_id)
                continue

            try:
                value = float(state.state)
                total += value
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Sensor %s has non-numeric state '%s', treating as 0.0",
                    entity_id,
                    state.state,
                )
                continue

        return total

