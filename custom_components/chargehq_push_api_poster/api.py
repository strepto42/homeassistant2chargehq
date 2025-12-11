"""API client for ChargeHQ Push API Poster integration."""
from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientSession

_LOGGER = logging.getLogger(__name__)


class EnergyPosterApiClient:
    """API client to post energy data to the configured endpoint."""

    def __init__(
        self,
        session: ClientSession,
        api_url: str,
        api_key: str,
    ) -> None:
        """Initialize the API client.

        Args:
            session: The aiohttp client session from Home Assistant.
            api_url: The API endpoint URL to POST data to.
            api_key: The API key for authentication.
        """
        self._session = session
        self._api_url = api_url
        self._api_key = api_key

    async def post_energy_data(
        self,
        timestamp_ms: int,
        consumption_kw: float,
        production_kw: float,
        net_import_kw: float,
    ) -> bool:
        """Post energy data to the configured API endpoint.

        Args:
            timestamp_ms: Timestamp in milliseconds.
            consumption_kw: Total consumption in kW.
            production_kw: Total solar production in kW.
            net_import_kw: Net import (consumption - production) in kW.

        Returns:
            True if the POST was successful, False otherwise.
        """
        payload: dict[str, Any] = {
            "apiKey": self._api_key,
            "tsms": timestamp_ms,
            "siteMeters": {
                "consumption_kw": consumption_kw,
                "net_import_kw": net_import_kw,
                "production_kw": production_kw,
            },
        }

        try:
            async with self._session.post(
                self._api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status >= 200 and response.status < 300:
                    _LOGGER.debug(
                        "Successfully posted energy data: consumption=%.2f kW, "
                        "production=%.2f kW, net_import=%.2f kW",
                        consumption_kw,
                        production_kw,
                        net_import_kw,
                    )
                    return True
                else:
                    response_text = await response.text()
                    _LOGGER.error(
                        "Failed to post energy data. Status: %s, Response: %s",
                        response.status,
                        response_text,
                    )
                    return False
        except ClientError as err:
            _LOGGER.error("Error posting energy data: %s", err)
            return False
        except Exception as err:
            _LOGGER.exception("Unexpected error posting energy data: %s", err)
            return False

