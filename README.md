# domoticz_eq3_max
This project is a plugin that allowes using the eQ-3 MAX! radiator thermostats in the home automation software [domoticz](https://www.domoticz.com/).

## Description
Using this plugin, you can control and fully automate your heating using domoticz and eQ-3 MAX! Radiators.

The thermostats are grouped into 'Rooms'. One room contains one or more thermostats, the temperature is set for the room and **not** for each thermostat in the room individually. This is a limitation of the eQ-3 software.

For each thermostat, this plugin can read out the measured temperature and battery level.

By default, this plugin refreshes it's data every 30 seconds by polling the MAX! cube. This way, if temperature are manually set at the termostats, the temperatures are updated in domoticz.

Setting the room temperatures from domoticz occures immediately, these actions are independant from the poll interval.

## Requirements
### Hardware
1. MAX! Cube LAN Gateway
1. MAX! Radiotor Thermostat(s)
### Software
Unfortunatelly, the vendor supplied software is required for the initial setup/configuration. Once all thermostats have been paired with the cube, this software is no longer required.

Please refer to the eQ-3 documentation on how to setup the MAX! Cube and how to pair the thermostats with the cube.

## Installation
### Automatic/GIT
Navigate to the domoticz/plugins folder and execute the following command: ```git clone https://github.com/teeminus/domoticz_eq3_max.git```

Restart domoticz afterwards.

### Manual
Download the content of this repo using [this](https://github.com/teeminus/domoticz_eq3_max/archive/master.zip) link and extract the archive (including all subfolders) to the domoticz/plugins folder. Restart domoticz afterwards.

## Configuration
### Prerequisites
1. Before configuring the domoticz plugin, the MAX! Cube and the Thermostats have to be configured using the eQ-3 software.
1. **Optional**: I recommend assigning a fixed IP to the MAX! Cube.
1. **Optional**: The cube does not need an internet connection to function properly, so you can block the internet access in your router (if possible).

### Configuration in domoticz
1. Navigate to ```Setup->Hardware```
1. Select ```Max!``` from the ```Type``` dropdown menu
1. Configure the plugin
   1. ```IP Address``` : IP address of the MAX! cube.
   1. ```Port``` : MAX! Cube port. **Can be left unchanged.**
   1. ```Heartbeat``` : Manual poll interval for the thermostats temperature (measured and set) and battery level. **Do not choose an interval smaller than 30 seconds.**
   1. ```Create Temperature device``` : Create a domoticz device for each thermostat to display the temperature measured by the thermostat.
   1. ```Create SetPoint device``` : Create a domoticz SetPoint device to set the room temperature from domoticz.
   1. ```Create Percentage device``` : Create a domoticz device for each thermostat to display the battery level.
   1. ```Delete removed devices``` : Delete domoticz device when a room/thermostat is no longer available for the cube.
   1. ```Debug``` : Turn on debug mode. In this mode, the device list is rebuild on every start of the plugin. **Do not turn this on, this really spams the domoticz log.**
1. Click ```Add``` to create a new hardware device.
1. Navigate to ```Setup->Devices``` to add all needed devices to domoticz.

## Limitations
1. Currently, only thermostats are supported.
2. Heating time plans generated by the eQ-3 software are not supported. There are no plans to implement this feature as domoticz is easier to use for that.

## Known bugs
The MAX! Cube seems to hang after a few month. In this case, the cube has to be power cycles manually. Currently, there is no other fix for that problem.

## Contributing
Yes, please! For major changes, please open an issue first to discuss what you would like to change.


## License
[MIT](https://choosealicense.com/licenses/mit/)