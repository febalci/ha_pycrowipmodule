"""Support for Crow IP Module sensors (shows panel info)."""
import logging

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_OFF, STATE_ON

from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)
from . import (
    CONF_OUTPUTNAME,
    DATA_CRW,
    OUTPUT_SCHEMA,
    SIGNAL_OUTPUT_UPDATE,
    CrowIPModuleDevice,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Perform the setup for Crow IP Module  Switch devices."""
    configured_outputs = discovery_info["outputs"]
    devices = []

    for output_num in configured_outputs:
        device_config_data = OUTPUT_SCHEMA(configured_outputs[output_num])
        device = CrowIPModuleOutput(
            hass,
            output_num,
            device_config_data[CONF_OUTPUTNAME],
            hass.data[DATA_CRW].output_state[output_num],
            hass.data[DATA_CRW],
        )
        devices.append(device)
    async_add_entities(devices)

class CrowIPModuleOutput(CrowIPModuleDevice, SwitchEntity):
    """Representation of an Crow IP Module Output Switch."""

    def __init__(self, hass, output_number, output_name, info, controller):
        """Initialize the switch"""
        self._output_number = output_number
        _LOGGER.debug("Setting up switch for system...")
        super().__init__("Crow " + output_name, info, controller)
        self._name = "Crow Output " + output_name
        self._state = STATE_OFF

    async def async_added_to_hass(self):
        """Register callbacks."""
        async_dispatcher_connect(self.hass, SIGNAL_OUTPUT_UPDATE, self._update_callback)

    @property
    def name(self):
        """Return name of the output."""
        return self._name

    @property
    def is_on(self):
        """Return true if device is on."""
        self._state = self._info["status"]["open"]
        _LOGGER.debug("Is_on="+str(self._state))
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn on the output."""
        self.hass.data[DATA_CRW].command_output(str(self._output_number))
        self._state = STATE_ON
        self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the output."""
        self.hass.data[DATA_CRW].command_output(str(self._output_number))
        self._state = STATE_OFF
        self.async_schedule_update_ha_state()

    @callback
    def _update_callback(self, output):
        """Update the output state in HA, if needed."""
        if output is None or int(output) == int(self._output_number):
            self.async_schedule_update_ha_state()
            _LOGGER.debug("Update poutput"+str(output))
