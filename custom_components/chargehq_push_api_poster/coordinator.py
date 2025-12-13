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
        imported_kwh_sensor: str | None = None,
        exported_kwh_sensor: str | None = None,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: The Home Assistant instance.
            api_client: The API client to post data.
            consumption_sensors: List of consumption sensor entity IDs.
            solar_sensors: List of solar production sensor entity IDs.
            interval: Interval in seconds between posts.
            imported_kwh_sensor: Optional imported kWh sensor entity ID.
            exported_kwh_sensor: Optional exported kWh sensor entity ID.
        """
        self._hass = hass
        self._api_client = api_client
        self._consumption_sensors = consumption_sensors
        self._solar_sensors = solar_sensors
        self._interval = interval
        self._imported_kwh_sensor = imported_kwh_sensor
        self._exported_kwh_sensor = exported_kwh_sensor
        self._unsub_timer: Any = None
        self.last_posted_data: dict[str, Any] = {}

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

        # Get optional imported/exported kWh values
        imported_kwh = None
        if self._imported_kwh_sensor:
            imported_kwh = self._get_sensor_value(self._imported_kwh_sensor)

        exported_kwh = None
        if self._exported_kwh_sensor:
            exported_kwh = self._get_sensor_value(self._exported_kwh_sensor)

        # Store data for display sensor
        self.last_posted_data = {
            "timestamp_ms": timestamp_ms,
            "consumption_kw": consumption_kw,
            "production_kw": production_kw,
            "net_import_kw": net_import_kw,
        }

        if imported_kwh is not None:
            self.last_posted_data["imported_kwh"] = imported_kwh

        if exported_kwh is not None:
            self.last_posted_data["exported_kwh"] = exported_kwh

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
            imported_kwh=imported_kwh,
            exported_kwh=exported_kwh,
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

    def _get_sensor_value(self, entity_id: str) -> float | None:
        """Get the value of a single sensor.

        Args:
            entity_id: The sensor entity ID.

        Returns:
            The sensor value or None if unavailable or non-numeric.
        """
        state = self._hass.states.get(entity_id)
        if state is None:
            _LOGGER.warning("Sensor %s not found", entity_id)
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Sensor %s has non-numeric state '%s'",
                entity_id,
                state.state,
            )
            return None

