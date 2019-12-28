"""Support for Crow IP Module-based alarm control panel"""
import logging

import voluptuous as vol

import homeassistant.components.alarm_control_panel as alarm
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)

from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    STATE_UNKNOWN,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import (
    CONF_CODE,
    CONF_AREANAME,
    DATA_CRW,
    AREA_SCHEMA,
    SIGNAL_KEYPAD_UPDATE,
    SIGNAL_AREA_UPDATE,
    CrowIPModuleDevice,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_ALARM_KEYPRESS = "crow_alarm_keypress"
ATTR_KEYPRESS = "keypress"
ALARM_KEYPRESS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required(ATTR_KEYPRESS): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Perform the setup for Crow IP Module alarm panels."""
    configured_areas = discovery_info["areas"]
    # config['crowipmodule']['zones'][i]['name']
    devices = []
    for part_num in configured_areas:
        device_config_data = AREA_SCHEMA(configured_areas[part_num])
        device = CrowIPModuleAlarm(
            hass,
            part_num,
            device_config_data[CONF_AREANAME],
            device_config_data[CONF_CODE],
            hass.data[DATA_CRW].area_state[part_num],
            hass.data[DATA_CRW],
        )
        devices.append(device)

    async_add_entities(devices)

    @callback
    def alarm_keypress_handler(service):
        """Map services to methods on Alarm."""
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        keypress = service.data.get(ATTR_KEYPRESS)

        target_devices = [
            device for device in devices if device.entity_id in entity_ids
        ]

        for device in target_devices:
            device.async_alarm_keypress(keypress)

    hass.services.async_register(
        alarm.DOMAIN,
        SERVICE_ALARM_KEYPRESS,
        alarm_keypress_handler,
        schema=ALARM_KEYPRESS_SCHEMA,
    )

    return True


class CrowIPModuleAlarm(CrowIPModuleDevice, alarm.AlarmControlPanel):
    """Representation of an Crow IP Module-based alarm panel."""

    def __init__(
        self, hass, area_number, alarm_name, code, info, controller):
        """Initialize the alarm panel."""
        if area_number==1:
            self._area_number = 'A'
        else:
            self._area_number = 'B'
        self._code = code

        _LOGGER.debug("Setting up alarm: %s", alarm_name)
        super().__init__(alarm_name, info, controller)

    async def async_added_to_hass(self):
        """Register callbacks."""
        async_dispatcher_connect(self.hass, SIGNAL_KEYPAD_UPDATE, self._update_callback)
        async_dispatcher_connect(
            self.hass, SIGNAL_AREA_UPDATE, self._update_callback
        )

    @callback
    def _update_callback(self, area):
        """Update Home Assistant state, if needed."""
        if area is None or area == self._area_number:
            self.async_schedule_update_ha_state()

    """Required to show up Keypad on alarm panel"""
    @property
    def code_format(self):
        """Regex for code format or None if no code is required."""
        if self._code != '':
            return None
        return alarm.FORMAT_NUMBER

    @property
    def state(self):
        """Return the state of the device."""
        state = STATE_UNKNOWN

        if self._info["status"]["alarm"]:
            state = STATE_ALARM_TRIGGERED
        elif self._info["status"]["armed"]:
            state = STATE_ALARM_ARMED_AWAY
        elif self._info["status"]["stay_armed"]:
            state = STATE_ALARM_ARMED_HOME
        elif self._info["status"]["exit_delay"]:
            state = STATE_ALARM_PENDING
        elif self._info["status"]["stay_exit_delay"]:
            state = STATE_ALARM_PENDING
        elif self._info["status"]["disarmed"]:
            state = STATE_ALARM_DISARMED
        return state

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        if code:
            self.hass.data[DATA_CRW].disarm(str(code))
        else:
            self.hass.data[DATA_CRW].disarm(str(self._code))

    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        self.hass.data[DATA_CRW].arm_stay()

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""

        if code:
            self.hass.data[DATA_CRW].send_keypress(str(code))
        else:
            self.hass.data[DATA_CRW].send_keypress(str(self._code))
#            self.hass.data[DATA_CRW].arm_away()

    async def async_alarm_trigger(self, code=None):
        """Alarm trigger command. Will be used to trigger a panic alarm."""
        self.hass.data[DATA_CRW].panic_alarm('')

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._info["status"]

    @callback
    def async_alarm_keypress(self, keypress=None):
        """Send custom keypress."""
        if keypress:
            self.hass.data[DATA_CRW].send_keypress(str(keypress))

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY

