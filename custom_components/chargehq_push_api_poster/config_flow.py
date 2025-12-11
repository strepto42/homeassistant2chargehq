"""Config flow for Energy Poster integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_API_KEY,
    CONF_API_URL,
    CONF_CONSUMPTION_SENSORS,
    CONF_INTERVAL,
    CONF_SOLAR_SENSORS,
    DEFAULT_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class EnergyPosterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Energy Poster."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the input
            if not user_input.get(CONF_API_URL):
                errors[CONF_API_URL] = "api_url_required"
            elif not user_input[CONF_API_URL].startswith(("http://", "https://")):
                errors[CONF_API_URL] = "invalid_url"

            if not user_input.get(CONF_API_KEY):
                errors[CONF_API_KEY] = "api_key_required"

            if not user_input.get(CONF_CONSUMPTION_SENSORS):
                errors[CONF_CONSUMPTION_SENSORS] = "consumption_sensors_required"

            if not user_input.get(CONF_SOLAR_SENSORS):
                errors[CONF_SOLAR_SENSORS] = "solar_sensors_required"

            interval = user_input.get(CONF_INTERVAL, DEFAULT_INTERVAL)
            if not isinstance(interval, int) or interval < 1:
                errors[CONF_INTERVAL] = "invalid_interval"

            if not errors:
                # Create the config entry
                return self.async_create_entry(
                    title="Energy Poster",
                    data=user_input,
                )

        # Show the form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_URL): str,
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_CONSUMPTION_SENSORS): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        multiple=True,
                    )
                ),
                vol.Required(CONF_SOLAR_SENSORS): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        multiple=True,
                    )
                ),
                vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EnergyPosterOptionsFlow:
        """Get the options flow for this handler."""
        return ChargeHQPushApiPosterOptionsFlow(config_entry)


class ChargeHQPushApiPosterOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for ChargeHQ Push API Poster."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the input
            if not user_input.get(CONF_API_URL):
                errors[CONF_API_URL] = "api_url_required"
            elif not user_input[CONF_API_URL].startswith(("http://", "https://")):
                errors[CONF_API_URL] = "invalid_url"

            if not user_input.get(CONF_API_KEY):
                errors[CONF_API_KEY] = "api_key_required"

            if not user_input.get(CONF_CONSUMPTION_SENSORS):
                errors[CONF_CONSUMPTION_SENSORS] = "consumption_sensors_required"

            if not user_input.get(CONF_SOLAR_SENSORS):
                errors[CONF_SOLAR_SENSORS] = "solar_sensors_required"

            interval = user_input.get(CONF_INTERVAL, DEFAULT_INTERVAL)
            if not isinstance(interval, int) or interval < 1:
                errors[CONF_INTERVAL] = "invalid_interval"

            if not errors:
                # Update the config entry
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data=user_input,
                )
                return self.async_create_entry(title="", data={})

        # Get current values
        current_data = self._config_entry.data

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_API_URL,
                    default=current_data.get(CONF_API_URL, ""),
                ): str,
                vol.Required(
                    CONF_API_KEY,
                    default=current_data.get(CONF_API_KEY, ""),
                ): str,
                vol.Required(
                    CONF_CONSUMPTION_SENSORS,
                    default=current_data.get(CONF_CONSUMPTION_SENSORS, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        multiple=True,
                    )
                ),
                vol.Required(
                    CONF_SOLAR_SENSORS,
                    default=current_data.get(CONF_SOLAR_SENSORS, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        multiple=True,
                    )
                ),
                vol.Optional(
                    CONF_INTERVAL,
                    default=current_data.get(CONF_INTERVAL, DEFAULT_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )

