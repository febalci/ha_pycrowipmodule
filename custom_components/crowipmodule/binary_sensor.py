"""Support for Crow Alarm IP Module."""
import datetime
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util

from . import (
    CONF_ZONENAME,
    CONF_ZONETYPE,
    DATA_CRW,
    SIGNAL_ZONE_UPDATE,
    ZONE_SCHEMA,
    CrowIPModuleDevice,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Crow binary sensor devices."""
    configured_zones = discovery_info["zones"]

    devices = []
    for zone_num in configured_zones:
        device_config_data = ZONE_SCHEMA(configured_zones[zone_num])
        device = CrowIPModuleBinarySensor(
            hass,
            zone_num,
            device_config_data[CONF_ZONENAME],
            device_config_data[CONF_ZONETYPE],
            hass.data[DATA_CRW].zone_state[zone_num],
            hass.data[DATA_CRW],
        )
        devices.append(device)

    async_add_entities(devices)


class CrowIPModuleBinarySensor(CrowIPModuleDevice, BinarySensorEntity):
    """Representation of an Crow IP Module binary sensor."""

    def __init__(self, hass, zone_number, zone_name, zone_type, info, controller):
        """Initialize the binary_sensor."""
        self._zone_type = zone_type
        self._zone_number = zone_number

        _LOGGER.debug("Setting up zone: %s", zone_name)
        super().__init__(zone_name, info, controller)

    async def async_added_to_hass(self):
        """Register callbacks."""
        async_dispatcher_connect(self.hass, SIGNAL_ZONE_UPDATE, self._update_callback)

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._info["status"]["open"]

    @property
    def device_class(self):
        """Return the class of this sensor, from DEVICE_CLASSES."""
        return self._zone_type

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._info["status"]

    @callback
    def _update_callback(self, zone):
        """Update the zone's state, if needed."""
        if zone is None or int(zone) == self._zone_number:
            self.async_schedule_update_ha_state()
