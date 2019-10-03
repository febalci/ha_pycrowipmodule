"""Support for Crow IP Module sensors (shows panel info)."""
import logging

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from . import (
    CONF_AREANAME,
    DATA_CRW,
    AREA_SCHEMA,
    SIGNAL_KEYPAD_UPDATE,
    SIGNAL_AREA_UPDATE,
    CrowIPModuleDevice,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Perform the setup for Crow IP Module  Sensor devices."""
    configured_partitions = discovery_info["areas"]
    devices = []
    for part_num in configured_partitions:
        device_config_data = AREA_SCHEMA(configured_partitions[part_num])
        device = CrowIPModuleSensor(
            hass,
            device_config_data[CONF_AREANAME],
            part_num,
            hass.data[DATA_CRW].area_state[part_num],
            hass.data[DATA_CRW],
        )

        devices.append(device)

    async_add_entities(devices)


class CrowIPModuleSensor(CrowIPModuleDevice, Entity):
    """Representation of an Crow IP Module keypad."""

    def __init__(self, hass, area_name, area_number, info, controller):
        """Initialize the sensor."""
        self._icon = "mdi:alarm"
        if area_number==1:
            self._area_number = 'A'
        else:
            self._area_number = 'B'

        _LOGGER.debug("Setting up sensor for area: %s", area_name)
        super().__init__(area_name + " Keypad", info, controller)

    async def async_added_to_hass(self):
        """Register callbacks."""
        async_dispatcher_connect(self.hass, SIGNAL_KEYPAD_UPDATE, self._update_callback)
        async_dispatcher_connect(
            self.hass, SIGNAL_AREA_UPDATE, self._update_callback
        )

    @property
    def icon(self):
        """Return the icon if any."""
        return self._icon

    @property
    def state(self):
        """Return the overall state."""
        return self._info["status"]["alarm_zone"]
 
    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._info["status"]

    @callback
    def _update_callback(self, area):
        """Update the partition state in HA, if needed."""
        _LOGGER.debug("Area: %s", str(self._area_number))
        _LOGGER.debug("Area Number: %s", str(area))

        if area is None or area == self._area_number:
            self.async_schedule_update_ha_state()
