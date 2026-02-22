"""Constants for the Gree Climate integration."""

DOMAIN = "gree"

# Configuration Keys
CONF_UID = "uid"
CONF_ENCRYPTION_KEY = "encryption_key"
CONF_ENCRYPTION_VERSION = "encryption_version"
CONF_ZONE_ID = "zone_id"
CONF_MASTER = "master"
CONF_DISABLE_AVAILABLE_CHECK = "disable_available_check"
CONF_TEMP_SENSOR_OFFSET = "temp_sensor_offset"

# Defaults
DEFAULT_PORT = 7000
DEFAULT_TARGET_TEMP_STEP = 1

# Option Keys for OptionsFlow
OPTION_KEYS = [
    "hvac_modes",
    "fan_modes",
    "swing_modes",
    "swing_horizontal_modes",
    CONF_DISABLE_AVAILABLE_CHECK,
    CONF_TEMP_SENSOR_OFFSET,
]
