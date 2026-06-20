"""Constants for the Senz WiFi integration."""

from enum import StrEnum

DOMAIN = "senz_wifi"
BRAND_NAME = "Senz"
MANUFACTURER = "Pentair Thermal"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# API client settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0

# Coordinator update interval (seconds)
UPDATE_INTERVAL = 30

# Service names
SERVICE_BOOST = "boost"
CONF_DURATION_MINUTES = "duration_minutes"
DEFAULT_BOOST_DURATION_MINUTES = 180

# Unique ID suffixes for entities
SUFFIX_COMFORT_TEMPERATURE = "comfort_temperature"
SUFFIX_VACATION_TEMPERATURE = "vacation_temperature"
SUFFIX_FROST_TEMPERATURE = "frost_temperature"
SUFFIX_BOOST_FLOOR_TEMPERATURE = "boost_floor_temperature"
SUFFIX_BOOST_ROOM_TEMPERATURE = "boost_room_temperature"
SUFFIX_COMFORT_END_TIME = "comfort_end_time"
SUFFIX_ERROR_CODE = "error_code"
SUFFIX_SOFTWARE_VERSION = "software_version"
SUFFIX_SELECTED_SCHEDULE = "selected_schedule"

SUFFIX_ONLINE = "online"
SUFFIX_HEATING = "heating"

SUFFIX_VACATION_MODE = "vacation_mode"
SUFFIX_FROST_PROTECTION = "frost_protection"
SUFFIX_EARLY_START = "early_start"

SUFFIX_REGULATION_MODE = "regulation_mode"
SUFFIX_SCHEDULE_SELECT = "schedule_select"


class SenzHVACMode(StrEnum):
    """HVAC mode mapping for Senz WiFi thermostats."""

    OFF = "off"
    HEAT = "heat"
    AUTO = "auto"


class SenzPresetMode(StrEnum):
    """Preset mode mapping for Senz WiFi thermostats."""

    NONE = "none"
    BOOST = "boost"
