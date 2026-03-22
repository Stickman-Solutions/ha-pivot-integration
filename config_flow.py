"""Config flow for the Pivot API integration."""

from __future__ import annotations
import logging
import base64
from typing import Any
import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_EMAIL, CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_API_KEY): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)


def _build_auth_header(email: str, api_key: str) -> str:
    """Build a Basic auth header value from email and API key."""
    credentials = f"{email}:{api_key}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


async def validate_and_fetch_devices(
    hass: HomeAssistant, data: dict[str, Any]
) -> list[dict]:
    """Validate credentials and return list of devices.

    Raises CannotConnect if the host is unreachable.
    Raises InvalidAuth if credentials are rejected.
    """
    session = async_get_clientsession(hass)
    auth_header = _build_auth_header(data[CONF_EMAIL], data[CONF_API_KEY])

    try:
        async with session.get(
            f"{data[CONF_HOST]}/get_user_devices",
            headers={"Authorization": auth_header},
        ) as resp:
            _LOGGER.debug("Got response status: %s", resp.status)
            if resp.status in {401, 403}:
                raise InvalidAuth
            if resp.status not in {200, 202}:
                raise CannotConnect
            return await resp.json()
    except aiohttp.ClientError as err:
        raise CannotConnect from err


class PivotApiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pivot API."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                devices = await validate_and_fetch_devices(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Store devices in the config entry so __init__.py can register them
                return self.async_create_entry(
                    title=user_input[CONF_EMAIL],
                    data={
                        **user_input,
                        "devices": devices,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
