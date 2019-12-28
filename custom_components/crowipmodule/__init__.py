"""Crow/AAP IP Module init file"""
import asyncio
import logging

import voluptuous as vol

from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, CONF_TIMEOUT, CONF_HOST
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.dispatcher import async_dispatcher_send

_LOGGER = logging.getLogger(__name__)

DOMAIN = "crowipmodule"

DATA_CRW = "crowipmodule"

CONF_CODE = "code"
CONF_CROW_KEEPALIVE = "keepalive_interval"
CONF_CROW_PORT = "port"
CONF_AREANAME = "name"
CONF_AREAS = "areas"
CONF_ZONENAME = "name"
CONF_ZONES = "zones"
CONF_ZONETYPE = "type"
CONF_OUTPUTS = "outputs"
CONF_OUTPUTNAME = "name"

DEFAULT_PORT = 5002
DEFAULT_KEEPALIVE = 60
DEFAULT_ZONETYPE = "opening"
DEFAULT_TIMEOUT = 10

SIGNAL_ZONE_UPDATE = "crowipmodule.zones_updated"
SIGNAL_AREA_UPDATE = "crowipmodule.areas_updated"
SIGNAL_SYSTEM_UPDATE = "crowipmodule.system_updated"
SIGNAL_OUTPUT_UPDATE = "crowipmodule.output_updated"
SIGNAL_KEYPAD_UPDATE = "crowipmodule.keypad_updated"

OUTPUT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_OUTPUTNAME): cv.string,
    }
)
ZONE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONENAME): cv.string,
        vol.Optional(CONF_ZONETYPE, default=DEFAULT_ZONETYPE): cv.string,
    }
)

AREA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_AREANAME): cv.string,
        vol.Optional(CONF_CODE, default=''): cv.string,
    }
)


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_ZONES): {vol.Coerce(int): ZONE_SCHEMA},
                vol.Optional(CONF_AREAS): {vol.Coerce(int): AREA_SCHEMA},
                vol.Optional(CONF_OUTPUTS): {vol.Coerce(int): OUTPUT_SCHEMA},
                vol.Optional(CONF_CROW_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_CROW_KEEPALIVE, default=DEFAULT_KEEPALIVE): vol.All(
                    vol.Coerce(int), vol.Range(min=15)
                ),
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.Coerce(int),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass, config):
    """Set up for Crow IP Module."""
    from pycrowipmodule import CrowIPAlarmPanel

    conf = config.get(DOMAIN)
    host = conf.get(CONF_HOST)
    code = '0000'
    port = conf.get(CONF_CROW_PORT)
    keep_alive = conf.get(CONF_CROW_KEEPALIVE)
    zones = conf.get(CONF_ZONES)
    areas = conf.get(CONF_AREAS)
    outputs = conf.get(CONF_OUTPUTS)
    connection_timeout = conf.get(CONF_TIMEOUT)
    sync_connect = asyncio.Future()

    controller = CrowIPAlarmPanel(
        host,
        port,
        code,
        keep_alive,
        hass.loop,
        connection_timeout,
    )

    hass.data[DATA_CRW] = controller

    @callback
    def connection_fail_callback(data):
        """Network failure callback."""
        _LOGGER.error("Could not establish a connection with the Crow Ip Module")
        if not sync_connect.done():
            sync_connect.set_result(False)

    @callback
    def connected_callback(data):
        """Handle a successful connection."""
        _LOGGER.info("Established a connection with the Crow Ip Module")
        if not sync_connect.done():
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_crowipmodule)
            sync_connect.set_result(True)

    @callback
    def zones_updated_callback(data):
        """Handle zone updates."""
        _LOGGER.debug("Crow Ip Module sent a zone update event. Updating zones...")
        async_dispatcher_send(hass, SIGNAL_ZONE_UPDATE, data)

    @callback
    def areas_updated_callback(data):
        """Handle area changes thrown by crow (including alarms)."""
        _LOGGER.debug("The Crow Ip Module sent an area update event. Updating areas...")
        async_dispatcher_send(hass, SIGNAL_AREA_UPDATE, data)

    @callback
    def system_updated_callback(data):
        #Handle system updates.
        _LOGGER.debug('Crow Ip Module sent a system update event. Updating system...')
        async_dispatcher_send(hass, SIGNAL_SYSTEM_UPDATE, data)

    @callback
    def output_updated_callback(data):
        """Handle output updates."""
        _LOGGER.debug("Crow Ip Module sent an output update event. Updating output...")
        async_dispatcher_send(hass, SIGNAL_OUTPUT_UPDATE, data)

    @callback
    def stop_crowipmodule(event):
        """Shutdown Crow IP Module connection and thread on exit."""
        _LOGGER.info("Shutting down CrowIpModule")
        controller.stop()


    controller.callback_zone_state_change = zones_updated_callback
    controller.callback_area_state_change = areas_updated_callback
    controller.callback_system_state_change = system_updated_callback
    controller.callback_output_state_change = output_updated_callback

    controller.callback_connected = connected_callback
    controller.callback_login_timeout = connection_fail_callback

    _LOGGER.info("Start CrowIpModule.")
    controller.start()

    result = await sync_connect
    if not result:
        return False

    # Load sub-components for Crow Ip Module
    if areas:
        hass.async_create_task(
            async_load_platform(
                hass,
                "alarm_control_panel",
                "crowipmodule",
                {CONF_AREAS: areas},
                config,
            )
        )
        hass.async_create_task(
            async_load_platform(
                hass,
                "sensor",
                "crowipmodule",
                {CONF_AREAS: areas},
                config,
            )
        )
        
    if zones:
        hass.async_create_task(
            async_load_platform(
                hass, 
                "binary_sensor", 
                "crowipmodule", 
                {CONF_ZONES: zones}, 
                config,
            )
        )

    if outputs:
        hass.async_create_task(
            async_load_platform(
                hass, 
                "switch", 
                "crowipmodule", 
                {CONF_OUTPUTS: outputs}, 
                config,
            )
        )

    return True


class CrowIPModuleDevice(Entity):
    """Representation of an Crow IP Module."""

    def __init__(self, name, info, controller):
        """Initialize the device."""
        self._controller = controller
        self._info = info
        self._name = name

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

