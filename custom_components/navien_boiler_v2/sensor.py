import datetime
import json
import logging
import os

import requests
from homeassistant.components.sensor import SensorEntity

BOILER_STATUS = {
    'deviceAlias': '경동 나비엔 보일러',
    'Date': f"{datetime.datetime.now()}",
    "mode": "away",
    "supportedThermostatModes":[],
    "switch": "on",
    "measurement": "°C",
    "temperatureMeasurement": 30,
    "thermostatWaterHeatingSetpoint": 30,
    "thermostatHeatingSetpoint": 30,
    "heatingSetpointRange": ""
}

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """example_integration sensor platform setup"""
    _LOGGER.info(" start navien boiler v2 ")

    scriptpath = os.path.dirname(__file__)
    with open(scriptpath + "/commands.json", "r") as f:
        data = json.load(f)

    data['token'] = config.get('token')
    data['deviceId'] = config.get('deviceId')

    _LOGGER.debug("start navien_boiler_v2 :{0} {1} {2} ".format(config, discovery_info, data))

    entitie = []
    for key in BOILER_STATUS.keys():
        api = SmartThingsApi(key, data)
        entitie += [Sensor(hass, api, key)]
    add_entities(entitie)


class SmartThingsApi:

    def __init__(self, key, data):
        """Initialize the Air Korea API.."""
        self.result = {}
        self._key = key
        self.data = data
        self.token = data['token']
        self.deviceId = data['deviceId']
        self.headers = {
            'Authorization': 'Bearer {}'.format(self.token)
        }

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
                # 외출일때 난방온수 온도와 온수 온도를 같게 한다.
                if BOILER_STATUS['mode'] == "away":
                    BOILER_STATUS['thermostatHeatingSetpoint'] = response_json['components']['main']['thermostatWaterHeatingSetpoint']['heatingSetpoint']['value']
                    BOILER_STATUS['heatingSetpointRange'] = response_json['components']['main']['thermostatWaterHeatingSetpoint']['heatingSetpointRange'][
                        'value']

                self.result = BOILER_STATUS

                print('JSON Response: type %s, %s', type(self.result), self.result)

            else:
                _LOGGER.debug(f'Error Code: {response.status_code}')
                print(f'Error Code: {response.status_code}')

        except Exception as ex:
            _LOGGER.error('Failed to update Navien Boiler API status Error: %s', ex)
            print(" Failed to update Navien Boiler API status Error:  ")
            raise


class Sensor(SensorEntity):
    """sensor platform class"""
    def __init__(self, hass, api, key):
        """sensor init"""
        self._state = None
        self._hass = hass
        self._api = api
        self._key = key
        self.var_icon = 'mdi:bathtub'
        self.TEMP_CELSIUS = "°C"

    async def async_update(self):
        """Retrieve latest state."""
        await self._hass.async_add_executor_job(self.update)

    def update(self):
        """sensor update"""
        _LOGGER.debug(' update !! ')

        self._api.update()
        if self._api.result is None:
            _LOGGER.error(' not updated !! API is None ')
            return

        self._state = self._api.result[self._key]
        _LOGGER.debug(f' {self._key} : {self._state}')

    @property
    def name(self):
        """return sensor name"""
        return "navien_"+self._key

    @property
    def unique_id(self):
        """Return a unique ID."""
        return "navien_"+self._key

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            'node_id': "navien_"+self._key,
            "name": BOILER_STATUS['deviceAlias'],
            "DeviceEntryType": "service"
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return BOILER_STATUS

    @property
    def available(self):
        """Return True if entity is available."""
        if BOILER_STATUS['switch'] == 'off':
            return False
        return True

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if BOILER_STATUS['mode'] == 'heat':
            return 'mdi:home-thermometer-outline'
        elif BOILER_STATUS['mode'] == 'ondol':
            return 'mdi:heating-coil'
        elif BOILER_STATUS['mode'] == 'away':
            return 'mdi:exit-run'
        else:
            return 'mdi:bathtub'

    @property
    def state_class(self):
        if self._key == 'mode' or self._key == 'switch' or self._key == 'deviceAlias' or self._key == 'Date':
            return None
        else:
            return 'measurement'

    @property
    def device_class(self):
        if self._key == 'mode' or self._key == 'switch' or self._key == 'deviceAlias':
            return None
        elif self._key == 'Date':
            return 'timestamp'
        else:
            return 'temperature'


if __name__ == '__main__':
    """example_integration sensor platform setup"""
    print(" start navien boiler ")

    scriptpath = os.path.dirname(__file__)
    with open(scriptpath + "/commands.json", "r") as f:
        data = json.load(f)

    real_time_api = SmartThingsApi('Date', data)
    real_time_api.update()
    print(real_time_api.result)
    # add_entities([Sensor(real_time_api)])
