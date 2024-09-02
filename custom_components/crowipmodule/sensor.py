"""Support for Crow IP Module sensors (shows panel info)."""

import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType

from . import DATA_CRW, SIGNAL_SYSTEM_UPDATE, CrowIPModuleDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant, config: ConfigType, async_add_entities, discovery_info=None
) -> None:
    """Perform the setup for Crow IP Module  Sensor devices."""
    devices = []
    device = CrowIPModuleSensor(
        hass,
        hass.data[DATA_CRW].system_state,
        hass.data[DATA_CRW],
    )
    devices.append(device)
    async_add_entities(devices)


class CrowIPModuleSensor(CrowIPModuleDevice, Entity):
    """Representation of an Crow IP Module keypad."""

    def __init__(self, hass: HomeAssistant, info, controller) -> None:
        """Initialize the sensor."""
        self._icon = "mdi:alarm"
        _LOGGER.debug("Setting up sensor for system")
        super().__init__("Crow Alarm System", info, controller)

    async def async_added_to_hass(self):
        """Register callbacks."""
        async_dispatcher_connect(self.hass, SIGNAL_SYSTEM_UPDATE, self._update_callback)

    @property
    def icon(self):
        """Return the icon if any."""
        return self._icon

    @property
    def state(self):
        """Return the overall state."""
        return self._info["status"]["mains"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._info["status"]

    @callback
    def _update_callback(self, system):
        """Update the partition state in HA, if needed."""
        self.async_schedule_update_ha_state()
