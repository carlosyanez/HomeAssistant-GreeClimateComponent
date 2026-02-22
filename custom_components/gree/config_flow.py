"""Config flow for Gree climate integration."""

from __future__ import annotations
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_PORT,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    CONF_ENCRYPTION_KEY,
    CONF_ENCRYPTION_VERSION,
    CONF_UID,
    CONF_ZONE_ID,
    CONF_MASTER,
)
from .gree_protocol import test_connection, discover_gree_devices, detect_device_encryption

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gree climate."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}
        self._discovered_devices: list[dict] = []
        self._selected_device: dict | None = None

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Initial step to choose discovery or manual."""
        if user_input is not None:
            if user_input.get("discovery") == "discover":
                return await self.async_step_discovery()
            return await self.async_step_manual()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("discovery", default="discover"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["discover", "manual"],
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            })
        )

    async def async_step_discovery(self, user_input: dict | None = None) -> FlowResult:
        """Handle device discovery."""
        if user_input is not None:
            selected_id = user_input["device"]
            for device in self._discovered_devices:
                if f"{device['mac']}_{device['host']}" == selected_id:
                    self._selected_device = device
                    await self.async_set_unique_id(device["mac"])
                    self._abort_if_unique_id_configured()
                    return await self.async_step_detect_encryption()

        self._discovered_devices = await discover_gree_devices(self.hass)
        if not self._discovered_devices:
            return await self.async_step_manual()

        device_options = {
            f"{d['mac']}_{d['host']}": f"IP: {d['host']} (MAC: {d['mac']})"
            for d in self._discovered_devices
        }

        return self.async_show_form(
            step_id="discovery",
            data_schema=vol.Schema({vol.Required("device"): vol.In(device_options)})
        )

    async def async_step_detect_encryption(self, user_input: dict | None = None) -> FlowResult:
        """Detect encryption and set Zone/Master parameters."""
        if user_input is not None:
            self._data = {
                CONF_NAME: user_input[CONF_NAME],
                CONF_HOST: self._selected_device["host"],
                CONF_MAC: self._selected_device["mac"],
                CONF_PORT: self._selected_device["port"],
                CONF_ENCRYPTION_VERSION: self._selected_device["encryption_version"],
                CONF_ZONE_ID: user_input[CONF_ZONE_ID],
                CONF_MASTER: user_input[CONF_MASTER],
                CONF_ENCRYPTION_KEY: "",
            }

            if await test_connection(self._data):
                return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
            return self.async_show_form(step_id="detect_encryption", errors={"base": "cannot_connect"})

        # Auto-detect encryption before showing form
        ver = await detect_device_encryption(
            self._selected_device["mac"], 
            self._selected_device["host"], 
            self._selected_device["port"]
        )
        self._selected_device["encryption_version"] = ver or 1

        return self.async_show_form(
            step_id="detect_encryption",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=self._selected_device.get("name", "Gree AC")): str,
                vol.Required(CONF_ZONE_ID, default=1): int,
                vol.Required(CONF_MASTER, default=False): bool,
            })
        )

    async def async_step_manual(self, user_input: dict | None = None) -> FlowResult:
        """Manual entry for all parameters."""
        errors = {}
        if user_input is not None:
            mac = user_input[CONF_MAC].replace("-", ":").lower()
            user_input[CONF_MAC] = mac
            await self.async_set_unique_id(mac)
            self._abort_if_unique_id_configured()

            if await test_connection(user_input):
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_MAC): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_ZONE_ID, default=1): int,
                vol.Required(CONF_MASTER, default=False): bool,
                vol.Optional(CONF_ENCRYPTION_VERSION, default=1): vol.In([1, 2]),
                vol.Optional(CONF_ENCRYPTION_KEY, default=""): str,
            }),
            errors=errors
        )
