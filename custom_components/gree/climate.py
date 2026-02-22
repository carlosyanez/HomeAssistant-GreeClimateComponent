"""Gree Climate Entity for Home Assistant."""

import base64
import logging
from datetime import timedelta

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import (
    ATTR_TEMPERATURE,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_PORT,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN, DEFAULT_PORT, DEFAULT_HVAC_MODES, DEFAULT_FAN_MODES,
    DEFAULT_SWING_MODES, DEFAULT_SWING_HORIZONTAL_MODES,
    CONF_HVAC_MODES, CONF_FAN_MODES, CONF_SWING_MODES,
    CONF_SWING_HORIZONTAL_MODES, CONF_ENCRYPTION_KEY,
    CONF_UID, CONF_ENCRYPTION_VERSION, CONF_ZONE_ID, CONF_MASTER,
    MODES_MAPPING, TEMSEN_OFFSET
)
from .gree_protocol import FetchResult, EncryptGCM, GetGCMCipher
from .helpers import decode_temp_c, encode_temp_c, gree_c_to_f, gree_f_to_c

_LOGGER = logging.getLogger(__name__)

async def create_gree_device(hass, config):
    """Factory to create GreeClimate instance from config data."""
    return GreeClimate(
        hass=hass,
        name=config.get(CONF_NAME, "Gree Climate"),
        ip_addr=config.get(CONF_HOST),
        port=config.get(CONF_PORT, DEFAULT_PORT),
        mac_addr=config.get(CONF_MAC).encode().replace(b":", b""),
        encryption_version=config.get(CONF_ENCRYPTION_VERSION, 1),
        encryption_key=config.get(CONF_ENCRYPTION_KEY),
        uid=config.get(CONF_UID, 0),
        zone_id=config.get(CONF_ZONE_ID, 1),
        master=config.get(CONF_MASTER, False),
    )

class GreeClimate(ClimateEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "gree"

    def __init__(self, hass, name, ip_addr, port, mac_addr, encryption_version, encryption_key, uid, zone_id, master):
        self.hass = hass
        self._name = name
        self._ip_addr = ip_addr
        self._port = port
        self._mac_addr_raw = mac_addr
        self._mac_str = mac_addr.decode("utf-8").lower()
        self._zone_id = zone_id
        self._is_master = master
        
        self._unique_id = f"{DOMAIN}_{self._mac_str}_z{zone_id}"
        self.encryption_version = encryption_version
        self._encryption_key = encryption_key.encode("utf8") if encryption_key else None
        self._uid = uid

        # Protocol state
        self._acOptions = {"Wid": self._zone_id, "Pow": 0, "Mod": 0, "SetTem": 25}
        self._current_temperature = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._mac_str)},
            name=self._name,
            manufacturer="Gree",
            model=f"Zone {self._zone_id} {'(Master)' if self._is_master else ''}",
        )

    async def SendStateToAc(self):
        """Prepare and send JSON payload with Wid (Zone ID)."""
        opt_list = ["Pow", "Mod", "SetTem", "WdSpd", "Air", "Blo", "Health", "Lig", "SwUpDn", "Wid"]
        self._acOptions["Wid"] = self._zone_id
        
        filtered_opt = [f'"{k}"' for k in opt_list if self._acOptions.get(k) is not None]
        filtered_p = [str(self._acOptions[k]) for k in opt_list if self._acOptions.get(k) is not None]

        payload = '{"opt":[' + ",".join(filtered_opt) + '],"p":[' + ",".join(filtered_p) + '],"t":"cmd"}'

        if self.encryption_version == 2:
            pack, tag = EncryptGCM(self._encryption_key, payload)
            sent_json = '{"cid":"app","i":0,"pack":"' + pack + '","tcid":"' + self._mac_str + '","tag":"' + tag + '"}'
            cipher = GetGCMCipher(self._encryption_key)
            await FetchResult(cipher, self._ip_addr, self._port, sent_json, version=2)

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            self._acOptions["Pow"] = 0
        else:
            self._acOptions["Pow"] = 1
            self._acOptions["Mod"] = MODES_MAPPING["Mod"].get(hvac_mode)
        await self.SendStateToAc()
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {"zone_id": self._zone_id, "master_unit": self._is_master}
