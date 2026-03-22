"""The Pivot API integration."""

from __future__ import annotations
import base64
import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_EMAIL, CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]
POLL_INTERVAL = timedelta(seconds=30)


def build_auth_header(email: str, api_key: str) -> str:
    """Build Basic auth header."""
    encoded = base64.b64encode(f"{email}:{api_key}".encode()).decode()
    return f"Basic {encoded}"


async def fetch_device_data(
    session: aiohttp.ClientSession, host: str, auth: str, imei: str
) -> dict:
    """Fetch latest reported, derived, and device info."""
    async with session.get(
        f"{host}/get_data?imei={imei}&qty=1",
        headers={"Authorization": auth},
    ) as resp:
        resp.raise_for_status()
        reported = await resp.json()

    async with session.get(
        f"{host}/get_derived_data?imei={imei}&qty=1",
        headers={"Authorization": auth},
    ) as resp:
        resp.raise_for_status()
        derived = await resp.json()

    async with session.get(
        f"{host}/get_user_devices",
        headers={"Authorization": auth},
    ) as resp:
        resp.raise_for_status()
        devices = await resp.json()

    if not reported or not derived:
        raise UpdateFailed(f"No data returned for device {imei}")

    device = next((d for d in devices if d["imei"] == imei), None)
    if device is None:
        raise UpdateFailed(f"Device {imei} not found in device list")

    return {
        "reported": reported[0],
        "derived": derived[0],
        "device": device,
    }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pivot API from a config entry."""
    host = entry.data[CONF_HOST]
    email = entry.data[CONF_EMAIL]
    api_key = entry.data[CONF_API_KEY]
    devices: list[dict] = entry.data["devices"]

    session = async_get_clientsession(hass)
    auth = build_auth_header(email, api_key)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    for device in devices:
        imei = device["imei"]
        nickname = device.get("nickname") or imei

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"pivot_api_{imei}",
            update_method=lambda imei=imei: fetch_device_data(
                session, host, auth, imei
            ),
            update_interval=POLL_INTERVAL,
        )

        await coordinator.async_config_entry_first_refresh()

        hass.data[DOMAIN][entry.entry_id][imei] = {
            "coordinator": coordinator,
            "device_info": {
                "imei": imei,
                "nickname": nickname,
                "datetime_added": device.get("datetime_added"),
                "is_owned": device.get("is_owned", False),
            },
        }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
