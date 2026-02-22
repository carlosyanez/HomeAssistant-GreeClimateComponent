# ... (imports remain the same)
from .const import (
    # ... existing constants
    CONF_TEMP_SENSOR_OFFSET,
    CONF_ZONE_ID,  # Ensure these are in your const.py
    CONF_MASTER,
)

async def create_gree_device(hass, config):
    """Create a Gree device instance from config."""
    # ... (existing setup code)
    
    encryption_key = config.get(CONF_ENCRYPTION_KEY)
    uid = config.get(CONF_UID)
    encryption_version = config.get(CONF_ENCRYPTION_VERSION, 1)
    disable_available_check = config.get(CONF_DISABLE_AVAILABLE_CHECK, False)
    temp_sensor_offset = config.get(CONF_TEMP_SENSOR_OFFSET)
    
    # NEW PARAMETERS
    zone_id = config.get(CONF_ZONE_ID, 0)
    master = config.get(CONF_MASTER, 0)
    
    return GreeClimate(
        hass,
        name,
        ip_addr,
        port,
        mac_addr,
        hvac_modes,
        fan_modes,
        swing_modes,
        swing_horizontal_modes,
        encryption_version,
        disable_available_check,
        encryption_key,
        uid,
        temp_sensor_offset,
        zone_id,
        master
    )

class GreeClimate(ClimateEntity):
    _attr_translation_key = "gree"

    def __init__(
        self,
        hass,
        name,
        ip_addr,
        port,
        mac_addr,
        hvac_modes,
        fan_modes,
        swing_modes,
        swing_horizontal_modes,
        encryption_version,
        disable_available_check,
        encryption_key=None,
        uid=None,
        temp_sensor_offset=None,
        zone_id=0,
        master=0, # Added master here
    ):
        # ... (existing init logic)
        
        self._zone_id = zone_id
        self._master = master # Store master status

        self._acOptions = {
            "Pow": None,
            "Mod": None,
            "SetTem": None,
            "WdSpd": None,
            "Air": None,
            "Blo": None,
            "Health": None,
            "SwhSlp": None,
            "Lig": None,
            "SwingLfRig": None,
            "SwUpDn": None,
            "Quiet": None,
            "Tur": None,
            "StHt": None,
            "TemUn": None,
            "HeatCoolType": None,
            "TemRec": None,
            "SvSt": None,
            "SlpMod": None,
            "Wid": self._zone_id, # Initialize with zone_id
        }
        # ... (rest of init)

    async def SendStateToAc(self):
        """Send the current state to the AC unit."""
        opt_list = ["Pow", "Mod", "SetTem", "WdSpd", "Air", "Blo", "Health", "SwhSlp", "Lig", "SwingLfRig", "SwUpDn", "Quiet", "Tur", "StHt", "TemUn", "HeatCoolType", "TemRec", "SvSt", "SlpMod", "AntiDirectBlow", "LigSen"]

        # Ensure the current zone ID is always present in the outgoing packet
        self._acOptions["Wid"] = self._zone_id
        
        # Collect values from _acOptions
        p_values = [self._acOptions.get(k) for k in opt_list]

        # Filter out empty ones and append Wid explicitly to the payload
        filtered_opt = []
        filtered_p = []
        for name, val in zip(opt_list, p_values):
            if val not in ("", None):
                filtered_opt.append(f'"{name}"')
                filtered_p.append(str(val))
        
        # Always include the Zone ID (Wid) in the command
        filtered_opt.append('"Wid"')
        filtered_p.append(str(self._zone_id))

        # ... (rest of the encryption and sending logic remains the same)

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        attributes = super().extra_state_attributes or {}

        if self.outside_temperature is not None:
            attributes["outside_temperature"] = self.outside_temperature
            attributes["outside_temperature_unit"] = self._unit_of_measurement

        if self.room_humidity is not None:
            attributes["room_humidity"] = self.room_humidity
            attributes["room_humidity_unit"] = "%"
            
        # Add our new parameters to the UI attributes for debugging
        attributes["zone_id"] = self._zone_id
        attributes["is_master"] = bool(self._master)

        return attributes
