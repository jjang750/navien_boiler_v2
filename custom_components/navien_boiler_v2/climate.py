"""
Support for Navien Component.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/Navien/
"""
import datetime
import json
import logging
import os

import requests
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode, ClimateEntityFeature
)
from homeassistant.const import (
    UnitOfTemperature, ATTR_TEMPERATURE)

_LOGGER = logging.getLogger(__name__)

Navien_API_URL = 'https://igs.krb.co.kr/api'
DEFAULT_NAME = 'Navien'

MAX_TEMP = 45
MIN_TEMP = 10
HVAC_MODE_BATH = '목욕'
STATE_HEAT = '실내'
STATE_ONDOL = '온돌'
STATE_AWAY = '외출'
STATE_OFF = '종료'

BOILER_STATUS = {
    'deviceAlias': '경동 나비엔 보일러',
    'Date': f"{datetime.datetime.now()}",
    "mode": "away",
    "supportedThermostatModes":[],
    "switch": "on",
    "measurement": "°C",
    "temperatureMeasurement": 30,
    "thermostatWaterHeatingSetpoint": 30,
    "waterHeatingSetpointRange": {},
    "thermostatHeatingSetpoint": 30,
    "heatingSetpointRange": {}
}

IS_BOOTED = False

def setup_platform(hass, config, add_entities, discovery_info=None):
    global IS_BOOTED
    """Set up a Navien."""
    scriptpath = os.path.dirname(__file__)
    with open(scriptpath + "/commands.json", "r") as f:
        data = json.load(f)

    device = SmartThingsApi(data)
    device.update()

    add_entities([Navien(device, hass)], True)
    IS_BOOTED = True
    _LOGGER.debug("start navien_boiler_v2 :{0} {1} {2} {3}".format(config, BOILER_STATUS, data, IS_BOOTED))


class SmartThingsApi:

    def __init__(self, data):
        """Initialize the Air Korea API.."""
        self.result = {}
        self.data = data
        self.token = data['token']
        self.deviceId = data['deviceId']
        self.headers = {
            'Authorization': 'Bearer {}'.format(self.token)
        }

    def send(self, cmd, args) -> bool:
        print("send : {0}  {1}  {2}".format(cmd, args, self.data))
        _LOGGER.debug("send : {0}  {1}  {2}".format(cmd, args, self.data))

        if cmd is None or self.data is None: # or args is None
            return False

        try:
            if cmd == "switch" and args == "on":
                self.data[cmd]['arguments'] = []
            else:
                self.data[cmd]['arguments'] = [args]

            command = "{\"commands\": [" + json.dumps(self.data[cmd]) + "]}"
            print("command : " + command)
            _LOGGER.debug("command : " + command)

            SMARTTHINGS_API_URL = f'https://api.smartthings.com/v1/devices/{self.deviceId}/commands'

            response = requests.post(SMARTTHINGS_API_URL, timeout=10, headers=self.headers, data=command)

            print(" Call to Navien Boiler API {} ".format(response))
            _LOGGER.debug(" Call to Navien Boiler API {} ".format(response))

            if response.status_code != 200:
                print("error send command : {}".format(response))
                _LOGGER.error("error send command : {}".format(response))
                return False

        except Exception as ex:
            _LOGGER.error('Failed to send Navien Boiler API Error: %s', ex)
            print(" Failed to send Navien Boiler API Error: {} ".format(ex))
            raise
        return True

    def switch_on(self) -> None:
        print("switch_on : ")
        _LOGGER.debug("switch_on : ")
        BOILER_STATUS['switch'] = "on"
        self.send("switch", 'on')

    def switch_off(self) -> None:
        print("switch_off : ")
        _LOGGER.debug("switch_off : ")
        self.setThermostatMode("OFF")

    def setThermostatMode(self, mode) -> None:
        print("setThermostatMode : " + mode)
        _LOGGER.debug("setThermostatMode : " + mode)

        if mode == 'heat' or mode == 'away' or mode == 'ondol' or mode == 'OFF':
            self.send("setThermostatMode", mode)
            BOILER_STATUS['mode'] = mode
        else:
            _LOGGER.error("Unsupported Thermostat Mode : " + mode)

    def ondol(self):
        self.setThermostatMode("ondol")

    def away(self):
        self.setThermostatMode("away")

    def heat(self):
        self.setThermostatMode("heat")

    def setThermostatHeatingSetpoint(self, temperature) -> None:
        print("setThermostatHeatingSetpoint : {}".format(temperature))
        _LOGGER.debug("setThermostatHeatingSetpoint : {}".format(temperature))
        BOILER_STATUS['thermostatHeatingSetpoint'] = temperature
        self.send("setThermostatHeatingSetpoint", temperature)

    def setThermostatWaterHeatingSetpoint(self, temperature) -> None:
        print("setThermostatWaterHeatingSetpoint : {}".format(temperature))
        _LOGGER.debug("setThermostatWaterHeatingSetpoint : {}".format(temperature))
        BOILER_STATUS['thermostatWaterHeatingSetpoint'] = temperature
        self.send("setThermostatWaterHeatingSetpoint", temperature)

    def update(self):
        """Update function for updating api information."""
        try:
            SMARTTHINGS_API_URL = f'https://api.smartthings.com/v1/devices/{self.deviceId}/status'

            response = requests.get(SMARTTHINGS_API_URL, timeout=10, headers=self.headers)

            if response.status_code == 200:

                response_json = response.json()

                BOILER_STATUS['switch'] = response_json['components']['main']['switch']['switch']['value']
                BOILER_STATUS['measurement'] = response_json['components']['main']['temperatureMeasurement']['temperature']['unit']
                # 현재온도
                BOILER_STATUS['temperatureMeasurement'] = response_json['components']['main']['temperatureMeasurement']['temperature']['value']
                # 모드와 모드에 따른 온도
                BOILER_STATUS['mode'] = response_json['components']['main']['thermostatMode']['thermostatMode']['value']
                BOILER_STATUS['supportedThermostatModes'] = response_json['components']['main']['thermostatMode']['supportedThermostatModes']['value']
                BOILER_STATUS['thermostatHeatingSetpoint'] = response_json['components']['main']['thermostatHeatingSetpoint']['heatingSetpoint']['value']
                BOILER_STATUS['heatingSetpointRange'] = response_json['components']['main']['thermostatHeatingSetpoint']['heatingSetpointRange']['value']
                # 온수온도
                BOILER_STATUS['thermostatWaterHeatingSetpoint'] = response_json['components']['main']['thermostatWaterHeatingSetpoint']['heatingSetpoint']['value']
                BOILER_STATUS['waterHeatingSetpointRange'] = response_json['components']['main']['thermostatWaterHeatingSetpoint']['heatingSetpointRange']['value']

                self.result = BOILER_STATUS

                print('JSON Response: type %s, %s', type(self.result), self.result)

            else:
                _LOGGER.debug(f'Error Code: {response.status_code}')
                print(f'Error Code: {response.status_code}')

        except Exception as ex:
            _LOGGER.error('Failed to update Navien Boiler API status Error: %s', ex)
            print(" Failed to update Navien Boiler API status Error:  ")
            raise


class Navien(ClimateEntity):

    def __init__(self, device, hass):
        """Initialize the thermostat."""
        self._hass = hass
        self._name = '경동 나비엔 보일러'
        self.device = device
        self.node_id = 'navien_climate'
        self.result = {}

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.node_id

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            'node_id': self.node_id,
            'device_alias': self._name
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return {
            'node_id': self.node_id,
            'device_mode': BOILER_STATUS['mode']
        }

    @property
    def supported_features(self):
        """Return the list of supported features."""
        features = 0
        if self.is_on:
            features |= ClimateEntityFeature.PRESET_MODE # 프리셋 모드
        if BOILER_STATUS['mode'] != 'OFF':
            features |= ClimateEntityFeature.TARGET_TEMPERATURE # 온도 조절 모드로 되어 있지 않으면 un support set_temperature 오류 발생
        return features

    @property
    def available(self):
        """Return True if entity is available."""
        return BOILER_STATUS['switch'] == 'on'

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return UnitOfTemperature.CELSIUS

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return BOILER_STATUS['heatingSetpointRange']['step']

    @property
    def target_temperature_low(self):
        """Return the minimum temperature."""
        return BOILER_STATUS['heatingSetpointRange']['minimum']

    @property
    def target_temperature_high(self):
        """Return the maximum temperature."""
        return BOILER_STATUS['heatingSetpointRange']['maximum']

    @property
    def is_on(self):
        """Return true if heater is on."""
        return BOILER_STATUS['switch'] == 'on'

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return int(BOILER_STATUS['temperatureMeasurement'])

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return int(BOILER_STATUS['thermostatHeatingSetpoint'])

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.
        Need to be one of HVAC_MODE_*.
        """
        if self.is_on:
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.
        Need to be a subset of HVAC_MODES.
        """
        return [HVACMode.OFF, HVACMode.HEAT]

    @property
    def preset_modes(self):
        """Return a list of available preset modes.
        Requires SUPPORT_PRESET_MODE.
        """
        return [STATE_HEAT, STATE_ONDOL, STATE_AWAY, STATE_OFF]

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., home, away, temp.
        Requires SUPPORT_PRESET_MODE.
        """
        operation_mode = BOILER_STATUS['mode']
        if operation_mode == 'heat':
            return STATE_HEAT
        elif operation_mode == 'away':
            return STATE_AWAY
        elif operation_mode == 'ondol':
            return STATE_ONDOL
        elif operation_mode == 'OFF':
            return STATE_OFF
        else:
            _LOGGER.error("Unrecognized preset_mode: %s", operation_mode)

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return BOILER_STATUS['heatingSetpointRange']['minimum']

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return BOILER_STATUS['heatingSetpointRange']['maximum']

    def set_preset_mode(self, preset_mode):
        _LOGGER.debug("set_preset_mode >>>> " + preset_mode)
        """Set new preset mode."""
        if self.is_on is False:
            self.device.switch_on()
            BOILER_STATUS['switch'] = 'on'
        if preset_mode == STATE_HEAT:
            self.device.heat()
            BOILER_STATUS['mode'] = 'heat'
        elif preset_mode == STATE_ONDOL:
            self.device.ondol()
            BOILER_STATUS['mode'] = 'ondol'
        elif preset_mode == STATE_AWAY:
            self.device.away()
            BOILER_STATUS['mode'] = 'away'
        elif preset_mode == STATE_OFF:
            self.device.switch_off()
            BOILER_STATUS['mode'] = 'OFF'
        else:
            _LOGGER.error("Unrecognized set_preset_mode: %s", preset_mode)

        self.update()

    def set_hvac_mode(self, hvac_mode):
        _LOGGER.debug("set_hvac_mode >>>> " + hvac_mode)
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.HEAT:
            self.device.switch_on()
            BOILER_STATUS['switch'] = 'on'
            BOILER_STATUS['mode'] = 'away'
        elif hvac_mode == HVACMode.OFF:
            self.device.switch_off()
            BOILER_STATUS['mode'] = 'OFF'

        self.update()

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        _LOGGER.debug(f" set_temperature >>>>>>>>>>>> {kwargs}")
        if self.is_on is False:
            self.device.switch_on()
        temperature = kwargs.get(ATTR_TEMPERATURE)
        _LOGGER.debug(f" temperature >>>>>>>>>>>> {temperature}")

        if temperature is None:
            return None

        # 난방 모드에 따른 온도 변경
        operation_mode = BOILER_STATUS['mode']
        if operation_mode == 'away':
            BOILER_STATUS['thermostatWaterHeatingSetpoint'] = temperature
            self.device.setThermostatWaterHeatingSetpoint(temperature)
        else:
            BOILER_STATUS['thermostatHeatingSetpoint'] = temperature
            self.device.setThermostatHeatingSetpoint(temperature)

        self.update()

    def turn_on(self):
        """Turn the entity on."""
        self.device.switch_on()
        self.update()

    def turn_off(self):
        """Turn the entity off."""
        self.device.switch_off()
        self.update()

    def toggle(self):
        """Toggle the entity."""
        if self.is_on:
            self.turn_off()
        else:
            self.turn_on()
        self.update()

    def update(self):
        _LOGGER.debug(" updated!! ")
        self.result = self.device.update()


if __name__ == '__main__':
    """example_integration sensor 
    platform setup"""
    print(" start navien boiler v2 ")
    with open("commands.json", "r") as f:
        data = json.load(f)
    token = data['token']
    deviceId = data['deviceId']
    print("token : {}".format(token))
    print("deviceId : {}".format(deviceId))
    real_time_api = SmartThingsApi(data)
    real_time_api.away()
    real_time_api.setThermostatWaterHeatingSetpoint(30)
    # real_time_api.heat()
    # real_time_api.setThermostatHeatingSetpoint(30)
    print("{}".format(BOILER_STATUS))

