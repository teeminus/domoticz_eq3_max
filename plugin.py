"""
<plugin key="Max" name="Max!" author="Teeminus" version="1.0.0" wikilink="" externallink="">
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="192.168.0.222"/>
        <param field="Port" label="Port" width="200px" required="true" default="62910"/>
        <param field="Mode1" label="Heartbeat" width="200px" required="true" default="30"/>
        <param field="Mode2" label="Create Temperature device" width="75px">
            <options>
                <option label="True" value="True" default="true"/>
                <option label="False" value="False"/>
            </options>
        </param>
        <param field="Mode3" label="Create SetPoint device" width="75px">
            <options>
                <option label="True" value="True" default="true"/>
                <option label="False" value="False"/>
            </options>
        </param>
        <param field="Mode4" label="Create Percentage device" width="75px">
            <options>
                <option label="True" value="True" default="true"/>
                <option label="False" value="False"/>
            </options>
        </param>
        <param field="Mode5" label="Delete removed devices" width="75px">
            <options>
                <option label="True" value="True"/>
                <option label="False" value="False" default="true"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import base64
import binascii
from io import BytesIO
import datetime

class MaxCube(object):
    def __init__(self, serial, rf_address, firmware_version):
        self.serial           = serial
        self.rf_address       = rf_address
        self.firmware_version = firmware_version

    def print(self):
        Domoticz.Debug('Max!Cube info')
        Domoticz.Debug('-> Serial:     ' + self.serial)
        Domoticz.Debug('-> RF-Address: ' + self.rf_address)
        Domoticz.Debug('-> Firmware:   ' + self.firmware_version)

class MaxDevice(object):
    # Properties of the Max! device
    type                    = 0
    rf_address              = ''
    serial                  = ''
    name                    = ''
    room_id                 = 0
    battery_low             = False
    mode                    = 0
    valve_position          = 0
    temperature_setpoint    = 0
    date_until              = '2000-01-01T'
    time_until              = '01:00:00Z'
    temperature_actual      = 0
    
    # Domoticz unit id
    domoticz_percentage_id  = None
    domoticz_temperature_id = None
    
    # Automatically set the device as used => enabled while debugging
    domoticz_deviceused = 0
    
    # Domoticz device types
    @staticmethod
    def devicePercentageType():
        return 0xF3
    @staticmethod
    def devicePercentageSubType():
        return 0x06
    @staticmethod
    def deviceTemperatureType():
        return 0x50
    @staticmethod
    def deviceTemperatureSubType():
        return 0x05
    
    # Function to check if device is suitable for creating a domoticz device
    @staticmethod
    def isDeviceTypeSupported(type):
        # Only the following device types are supported:
        # - Heating Thermostat (1)
        # - Heating Thermostat Plus (2)
        return ((type >= 1) and (type <= 2))
    
    def __init__(self, rf_address):
        self.rf_address = rf_address
    
    def dump(self):
        Domoticz.Debug('MaxDevice dump')
        Domoticz.Debug('->type:                    ' + str(self.type))
        Domoticz.Debug('->rf_address:              ' + self.rf_address)
        Domoticz.Debug('->serial:                  ' + self.serial)
        Domoticz.Debug('->name:                    ' + self.name)
        Domoticz.Debug('->room_id:                 ' + str(self.room_id))
        Domoticz.Debug('->battery_low:             ' + str(self.battery_low))
        Domoticz.Debug('->mode:                    ' + str(self.mode))
        Domoticz.Debug('->valve_position:          ' + str(self.valve_position))
        Domoticz.Debug('->temperature_setpoint:    ' + ("%.1f" % self.temperature_setpoint))
        Domoticz.Debug('->date_until:              ' + self.date_until)
        Domoticz.Debug('->time_until:              ' + self.time_until)
        Domoticz.Debug('->temperature_actual:      ' + ("%.1f" % self.temperature_actual))
        if self.domoticz_percentage_id is None:
            Domoticz.Debug('->domoticz_percentage_id:  None')
        else:
            Domoticz.Debug('->domoticz_percentage_id:  ' + str(self.domoticz_percentage_id))
        if self.domoticz_temperature_id is None:
            Domoticz.Debug('->domoticz_temperature_id: None')  
        else:    
            Domoticz.Debug('->domoticz_temperature_id: ' + str(self.domoticz_temperature_id))
    
    def delete(self):
        # Check if the device has been created
        if self.domoticz_percentage_id in Devices:
            # Delete the device
            Devices[self.domoticz_percentage_id].delete()
        if self.domoticz_temperature_id in Devices:
            # Delete the device
            Devices[self.domoticz_temperature_id].delete()
    
    def update(self, maxRooms):
        # Check if the device type is supported
        if MaxDevice.isDeviceTypeSupported(self.type) == False:
            return

        # Generate device name
        deviceName = self.name
        if self.room_id != 0:
            for room_rf_address, room in maxRooms.items():
                if room.id == self.room_id:
                    deviceName = room.name + ' - ' + deviceName
        
        # Check if the percentage device has to be created
        if self.domoticz_percentage_id is None and Parameters['Mode4'] == 'True':
            # Find next available domoticz device id
            for i in range(1, 256):
                # Check if the unit id is already taken
                if i not in Devices:
                    self.domoticz_percentage_id = i
                    break
            
            # Check if we found a new device id
            if self.domoticz_percentage_id is not None:
                # Create new domoticz device
                device_type    = MaxDevice.devicePercentageType()
                device_subtype = MaxDevice.devicePercentageSubType()
                Domoticz.Device(Name=deviceName, Unit=self.domoticz_percentage_id, DeviceID=self.rf_address, Type=device_type, Subtype=device_subtype, Used=self.domoticz_deviceused).Create()
                Domoticz.Debug('Created new Domoticz percentage device with id: ' + str(self.domoticz_percentage_id))
            else:
                # Failed to create device
                Domoticz.Error('Did not create new room as the unit id would be greater than 255')
        
        # Check if the percentage device has been created
        if self.domoticz_percentage_id is not None:
            # Get battery level
            batteryLevel = 255
            if self.battery_low is True:
                batteryLevel = 0
            
            # Update the device
            strValue = str(self.valve_position)
            Devices[self.domoticz_percentage_id].Update(nValue = 0, sValue=strValue, BatteryLevel=batteryLevel)
        
        # Check if the temperature device has to be created
        if self.domoticz_temperature_id is None and Parameters['Mode2'] == 'True':
            # Find next available domoticz device id
            for i in range(1, 256):
                # Check if the unit id is already taken
                if i not in Devices:
                    self.domoticz_temperature_id = i
                    break
            
            # Check if we found a new device id
            if self.domoticz_temperature_id is not None:
                # Create new domoticz device
                device_type    = MaxDevice.deviceTemperatureType()
                device_subtype = MaxDevice.deviceTemperatureSubType()
                Domoticz.Device(Name=deviceName, Unit=self.domoticz_temperature_id, DeviceID=self.rf_address, Type=device_type, Subtype=device_subtype, Used=self.domoticz_deviceused).Create()
                Domoticz.Debug('Created new Domoticz temperature device with id: ' + str(self.domoticz_temperature_id))
            else:
                # Failed to create device
                Domoticz.Error('Did not create new room as the unit id would be greater than 255')
        
        # Check if the temperature device has been created
        if self.domoticz_temperature_id is not None:
            # Build update string
            strValue = ''
            
            # We only have a current temperature if we are in Auto or Manual mode
            if self.mode < 2:
                strValue += ("%.1f" % self.temperature_actual)
            else:
                strValue += ("%.1f" % self.temperature_setpoint)
            
            # Get battery level
            batteryLevel = 255
            if self.battery_low is True:
                batteryLevel = 0
            
            # Update the device
            Devices[self.domoticz_temperature_id].Update(nValue = 0, sValue=strValue, BatteryLevel=batteryLevel)

class MaxRoom(object):
    # Properties of the Max! room
    id                   = 0
    rf_address           = ''
    name                 = ''
    setpoint             = 0
    
    # Domoticz unit id
    domoticz_setpoint_id = None
    
    # Automatically set the device as used => enabled while debugging
    domoticz_deviceused = 0
    
    # Domoticz device types
    @staticmethod
    def deviceSetpointType():
        return 0xF2
    @staticmethod
    def deviceSetpointSubType():
        return 0x01
    
    def __init__(self, rf_address):
        self.rf_address = rf_address
    
    def dump(self):
        Domoticz.Debug('MaxRoom dump')
        Domoticz.Debug('->id:                   ' + str(self.id))
        Domoticz.Debug('->rf_address:           ' + self.rf_address)
        Domoticz.Debug('->name:                 ' + self.name)
        Domoticz.Debug('->setpoint:             ' + ("%.1f" % self.setpoint))
        if self.domoticz_setpoint_id is None:
            Domoticz.Debug('->domoticz_setpoint_id: None')
        else:
            Domoticz.Debug('->domoticz_setpoint_id: ' + str(self.domoticz_setpoint_id))
    
    def delete(self):
        # Check if the device has been created
        if self.domoticz_setpoint_id in Devices:
            # Delete the device
            Devices[self.domoticz_setpoint_id].Delete()

    def update(self):
        # Check if the setpoint device has to be created
        if self.domoticz_setpoint_id is None and Parameters['Mode3'] == 'True':
            # Find next available domoticz device id
            for i in range(1, 256):
                # Check if the unit id is already taken
                if i not in Devices:
                    self.domoticz_setpoint_id = i
                    break
            
            # Check if we found a new device id
            if self.domoticz_setpoint_id is not None:
                # Create new domoticz device
                device_type    = MaxRoom.deviceSetpointType()
                device_subtype = MaxRoom.deviceSetpointSubType()
                Domoticz.Device(Name=self.name, Unit=self.domoticz_setpoint_id, DeviceID=self.rf_address, Type=device_type, Subtype=device_subtype, Used=self.domoticz_deviceused).Create()
                Domoticz.Debug('Created new Domoticz setpoint device with id: ' + str(self.domoticz_setpoint_id))
            else:
                # Failed to create device
                Domoticz.Error('Did not create new room as the unit id would be greater than 255')
        
        # Check if the setpoint device has been created
        if self.domoticz_setpoint_id is not None:
            strValue = "%.1f" % self.setpoint
            Devices[self.domoticz_setpoint_id].Update(nValue = 0, sValue=strValue)

class BasePlugin:
    # TCP connection to the Cube
    tcpConn              = None

    # Status flag if we got meta data
    metaDataComplete     = False
    metaDataCount        = 0
    metaDataTotal        = 0
    
    # Cube device
    maxCube              = None
    
    # Dicts for rooms and devices
    maxRooms             = {}
    maxDevices           = {}
    
    # Mapping between room id and room rf_address
    maxRoomIdToRfAddress = {}
   
    # Flag if old, unknown devices shall be deleted
    deleteUnknownDevices = False
    
    def cubeParseC(self, Data):
        # Print message type
        Domoticz.Debug('Got C message')

    def cubeParseH(self, Data):
        # Print message type
        Domoticz.Debug('Got H message')
    
        # Parse cube data
        serial, rf_address, firmware_version, *_ = Data.decode().strip().split(',')
        
        # Check if cube object has been created
        if self.maxCube is None:
            self.maxCube = MaxCube(serial, rf_address, firmware_version)
        else:
            self.maxCube.serial           = serial
            self.maxCube.rf_address       = rf_address
            self.maxCube.firmware_version = firmware_version
        
        # Print cube infos
        self.maxCube.print()
    
    def cubeParseL(self, Data):
        # Print message type
        Domoticz.Debug('Got L message')
        
        # Only parse message if we got all meta infos
        if self.metaDataComplete == False:
            Domoticz.Debug('Ignoring L message as we don\'t have any meta infos')
            return
        
        # Decode data
        encoded = Data.strip()
        decoded = BytesIO(base64.decodebytes(encoded))
        
        # Flag to request meta data in case we get a status for a device we don't know yet
        requestMetaData = False
        
        # List of rooms to update
        requiredRoomUpdates = []
        
        # Loop over device status data
        while True:
            # Read message length
            try:
                msg_len = ord(decoded.read(1))
            except TypeError:
                break
            
            # Get device rf address
            device_rf_address = str(binascii.b2a_hex(decoded.read(3)), 'utf-8')
            
            # Check if the device exists
            if device_rf_address not in self.maxDevices:
                Domoticz.Log('Got message for device "' + device_rf_address + '" but I have no matching device...')
                decoded.read(msg_len - 3)
                requestMetaData = True
                continue
            
            # Get message data
            decoded.read(1) # Unknown message
            device_flags_1 = ord(decoded.read(1)) # Device flags (1/2)
            device_flags_2 = ord(decoded.read(1)) # Device flags (2/2)
            
            # Check if the error flag is set => flag_1 & (1 << 3) set
            if (device_flags_1 & (1 << 3)) > 0:
                Domoticz.Log('Error flag set for device "' + device_rf_address + '", resetting error...')
                
                # Send reset command
                resetCmd = 'r:01,' + base64.encodebytes(binascii.a2b_hex(device_rf_address)).decode('utf-8').strip() + '\r\n'
                if self.tcpConn is not None:
                    if self.tcpConn.Connected() == True:
                        self.tcpConn.Send(resetCmd)
                    else:
                        self.tcpConn.Connect()
            
            # Check if the device data is valid => flag_1 & (1 << 4) set
            if (device_flags_1 & (1 << 4)) == 0:
                Domoticz.Log('Got invalid infos from device: ' + device_rf_address)
                decoded.read(msg_len - 6)
                continue                
            
            # Parse device flags
            self.maxDevices[device_rf_address].battery_low = ((device_flags_2 & 0x80) > 0)
            self.maxDevices[device_rf_address].mode        = (device_flags_2 & 0x03)  
            
            # Check if there are more infos to parse
            if msg_len > 6:
                # Valve position
                self.maxDevices[device_rf_address].valve_position = ord(decoded.read(1))
                
                # Setpoint temperature
                msg_byte8 = ord(decoded.read(1))
                self.maxDevices[device_rf_address].temperature_setpoint = (msg_byte8 & 0x7F) / 2
                
                # The next two bytes depend on device type and device mode
                if self.maxDevices[device_rf_address].type != 3: # No a wall mounted Thermostat
                    # When the device is in auto or manual mode, the following two bytes contain the current temperature
                    if self.maxDevices[device_rf_address].mode < 2:
                        self.maxDevices[device_rf_address].temperature_actual = ((ord(decoded.read(1)) * 256) + ord(decoded.read(1))) / 10
                    else:
                        # The next two bytes are the until date
                        device_date       = decoded.read(2)
                        
                        # Parse y-m-d
                        device_date_year  = ord(device_date[1] & 0x1F) + 2000
                        device_date_month = ((ord(device_date[0]) >> 4) & 0x0E)  + ((ord(device_date[1]) >> 6) & 0x01) + 1
                        device_date_day   = ord(device_date[0]) & 0x1F + 1
                        
                        # Build date string
                        self.maxDevices[device_rf_address].date_until = str(device_date_year) + '-'
                        self.maxDevices[device_rf_address].date_until += ("%02" % device_date_month) + '-'
                        self.maxDevices[device_rf_address].date_until += ("%02" % device_date_day) + 'T'
                
                # The next byte is the until time
                device_time_until = ord(decoded.read(1)) / 2
                self.maxDevices[device_rf_address].time_until = ("%02d" % device_time_until) + ':'
                if device_time_until == int(device_time_until):
                    self.maxDevices[device_rf_address].time_until += '0'
                else:
                    self.maxDevices[device_rf_address].time_until += '3'
                self.maxDevices[device_rf_address].time_until += '0:00Z'
                if msg_len == 12:
                    self.maxDevices[device_rf_address].temperature_actual = (ord(decoded.read(1)) + ((msg_byte8 & 0x80) * 256)) / 10
                
                # Update room setpoint
                room_rf_address = self.maxRoomIdToRfAddress[self.maxDevices[device_rf_address].room_id]
                self.maxRooms[room_rf_address].setpoint = self.maxDevices[device_rf_address].temperature_setpoint
                
                # Add room to update list
                if room_rf_address not in requiredRoomUpdates:
                    requiredRoomUpdates.append(room_rf_address)
                    
            # Update the device
            self.maxDevices[device_rf_address].update(self.maxRooms)
    
        # Update rooms
        for room_rf_address in requiredRoomUpdates:
            self.maxRooms[room_rf_address].update()            
    
        # Check if we need to request meta data from the cube
        #if requestMetaData == True:
        #    if self.tcpConn is not None:
        #        self.tcpConn.Send('m:\r\n')
    
    def cubeParseM(self, Data):
        # Print message type
        Domoticz.Debug('Got M message')
        
        # Decode data
        msgIdx, msgTotal, encoded = Data.strip().split(b',', 2)
        msgIdx                    = int(msgIdx)
        msgTotal                  = int (msgTotal)
        decoded                   = BytesIO(base64.decodebytes(encoded))
        
        # Check if the total number of meta data messages has been set before
        if self.metaDataCount == 0:
            self.metaDataTotal = msgTotal
        
        # Check if the meta data message has the correct index
        if msgIdx != self.metaDataCount:
            Domoticz.Log('Meta data message order disruped. Expected message with id "' + str(self.metaDataCount) + '", got "' + str(msgIdx) + '"')
        
        # Increase message counter
        self.metaDataCount += 1
        
        # Check if we got all meta data messages
        if self.metaDataCount == self.metaDataTotal:
            self.metaDataComplete = True
        
        # Unknown bytes
        ord(decoded.read(1))
        ord(decoded.read(1))
        
        # Parse rooms
        rooms      = {}
        room_count = ord(decoded.read(1))
        for i in range(room_count):
            # Get room data
            room_id         = ord(decoded.read(1))
            room_name_len   = ord(decoded.read(1))
            room_name       = str(decoded.read(room_name_len), 'utf-8')
            room_rf_address = str(binascii.b2a_hex(decoded.read(3)), 'utf-8')
            
            # Store room infos
            rooms[room_rf_address]      = MaxRoom(room_rf_address)
            rooms[room_rf_address].id   = room_id
            rooms[room_rf_address].name = room_name
            if Parameters['Mode6'] == 'Debug':
                rooms[room_rf_address].domoticz_deviceused = 1            
        
        # Cleanup global room infos
        if self.deleteUnknownDevices == True:
            for room_rf_address, room in self.maxRooms.items():
                # Check if the room is not in the new list
                if room_rf_address not in rooms:
                    # Delete room
                    Domoticz.Debug('Deleting room:')
                    room.dump()
                    room.delete()
                    del self.maxRoomIdToRfAddress[room.id]
                    del self.maxRooms[room_rf_address]
        
        # Update global room infos
        for room_rf_address, room in rooms.items():
            # Check if we already know the room
            if room_rf_address in self.maxRooms:
                # Update room infos
                self.maxRooms[room_rf_address].id                  = room.id
                self.maxRooms[room_rf_address].name                = room.name
                self.maxRooms[room_rf_address].domoticz_deviceused = room.domoticz_deviceused
                self.maxRoomIdToRfAddress[room.id]                 = room.rf_address
            else:
                # Add room to list
                Domoticz.Debug('Found new room:')
                room.dump()
                self.maxRooms[room_rf_address] = room
                self.maxRoomIdToRfAddress[room.id] = room.rf_address
                
                # Update room in database
                self.maxRooms[room_rf_address].update()
        
        # Parse devices
        devices       = {}
        devices_count = ord(decoded.read(1))
        for i in range(devices_count):
            # Get device data
            device_type       = ord(decoded.read(1))
            device_rf_address = str(binascii.b2a_hex(decoded.read(3)), 'utf-8')
            device_serial     = str(decoded.read(10), 'utf-8')
            device_name_len   = ord(decoded.read(1))
            device_name       = str(decoded.read(device_name_len), 'utf-8')
            device_room_id    = ord(decoded.read(1))
            
            # Store device data
            devices[device_rf_address]         = MaxDevice(device_rf_address)
            devices[device_rf_address].type    = device_type
            devices[device_rf_address].serial  = device_serial
            devices[device_rf_address].name    = device_name
            devices[device_rf_address].room_id = device_room_id
            if Parameters['Mode6'] == 'Debug':
                devices[device_rf_address].domoticz_deviceused = 1
        
        # Cleanup global device infos
        if self.deleteUnknownDevices == True:
            for device_rf_address, device in self.maxDevices.items():
                # Check if the device is not in the new list
                if device_rf_address not in devices:
                    # Delete device
                    Domoticz.Debug('Deleting device:')
                    device.dump()
                    device.delete()
                    del self.maxDevices[device_rf_address]
        
        # Update global device infos
        for device_rf_address, device in devices.items():
            # Check if we already know the device
            if device_rf_address in self.maxDevices:
                # Update device infos
                self.maxDevices[device_rf_address].type                = device.type
                self.maxDevices[device_rf_address].name                = device.name
                self.maxDevices[device_rf_address].room_id             = device.room_id
                self.maxDevices[device_rf_address].domoticz_deviceused = device.domoticz_deviceused
            # Only the supported device types will be stored
            elif MaxDevice.isDeviceTypeSupported(device.type) == True:
                # Add device to list
                Domoticz.Debug('Found new device:')
                device.dump()
                self.maxDevices[device_rf_address] = device
            
                # Update device in database
                self.maxDevices[device_rf_address].update(self.maxRooms)

    def cubeParseS(self, Data):
        # Print message type
        Domoticz.Debug('Got S message')
        
        # Get message values
        duty_cycle, command_result, free_mem = Data.decode().strip().split(',')
        duty_cycle = int(duty_cycle, 16)
        free_mem = int(free_mem, 16)
        
        # Print debug stuff
        Domoticz.Debug('-> Duty Cycle:        ' + str(duty_cycle))
        Domoticz.Debug('-> Command Result:    ' + command_result + ' (' + str(int(command_result, 16)) + ')')
        Domoticz.Debug('-> Free Memory Slots: ' + str(free_mem))
        
        # Check duty cycle counter
        if duty_cycle >= 90:
            if duty_cycle == 100:
                Domoticz.Error('Cube has reached it\'s maximum amount of messages. Messages might get stored and send later')
            else:
                Domoticz.Log('Cube nearly reached it\'s maximum amount of messages. Be carefull to not loose messages')

        # Check command result
        if command_result != '0':
            Domoticz.Error('Last command failed')

    messageParserMap = {
        b'C:': cubeParseC,
        b'H:': cubeParseH,
        b'L:': cubeParseL,
        b'M:': cubeParseM,
        b'S:': cubeParseS,
    }

    # Variable to store unprocessed message parts
    unprocessedData = []

    def __init__(self):
        return

    def onStart(self):
        # Check if we are in debug mode
        if Parameters['Mode6'] == 'Debug':
            # Toggle debugging
            Domoticz.Debugging(1)
            
            # Delete old devices
            for x in list(Devices):
                Devices[x].Delete()

        # Restore devices
        for x in list(Devices):
            # Check device type
            if Devices[x].Type == MaxRoom.deviceSetpointType() and Devices[x].SubType == MaxRoom.deviceSetpointSubType():
                # Create new room
                room      = MaxRoom(Devices[x].DeviceID)
                room.name = Devices[x].Name
                try:
                    room.setpoint = float(Devices[x].sValue)
                except:
                    pass
                room.domoticz_setpoint_id = x
                if Parameters['Mode6'] == 'Debug':
                    room.domoticz_deviceused = 1
                
                # Add room to list
                self.maxRooms[room.rf_address] = room       
            else:
                # Check if the device already exists
                if Devices[x].DeviceID in self.maxDevices:
                    # Update only the domoticz id
                    if Devices[x].Type == MaxDevice.devicePercentageType() and Devices[x].SubType == MaxDevice.devicePercentageSubType():
                        self.maxDevices[Devices[x].DeviceID].domoticz_percentage_id  = x
                        device.valve_position = int(Devices[x].sValue)
                    else:
                        self.maxDevices[Devices[x].DeviceID].domoticz_temperature_id = x
                        device.temperature_setpoint = float(Devices[x].sValue)
                else:
                    # Create new device
                    device             = MaxDevice(Devices[x].DeviceID)
                    if Devices[x].Type == MaxDevice.devicePercentageType() and Devices[x].SubType == MaxDevice.devicePercentageSubType():
                        device.domoticz_percentage_id  = x
                        device.valve_position = int(Devices[x].sValue)
                    else:
                        device.domoticz_temperature_id = x
                        device.temperature_setpoint = float(Devices[x].sValue)
                    device.name        = Devices[x].Name
                    if Parameters['Mode6'] == 'Debug':
                        device.domoticz_deviceused = 1
    
                    # Add device to list
                    self.maxDevices[device.rf_address] = device

        # Print restored device/room data
        if Parameters['Mode6'] == 'Debug':
            # Print all restored rooms
            for rf_address, room in self.maxRooms.items():
                # Print debug infos
                Domoticz.Debug('Restored room:')
                Domoticz.Debug('-> rf_address:           ' + rf_address)
                Domoticz.Debug('-> name:                 ' + room.name)
                Domoticz.Debug('-> setpoint:             ' + ("%.1f" % room.setpoint))
                Domoticz.Debug('-> domoticz_setpoint_id: ' + str(room.domoticz_setpoint_id))
                Domoticz.Debug('-> Last seen:            ' + Devices[room.domoticz_setpoint_id].LastUpdate)

            # Print all restored devices
            for rf_address, device in self.maxDevices.items():
                # Print debug infos
                Domoticz.Debug('Restored device:')
                Domoticz.Debug('-> rf_address:              ' + rf_address)
                Domoticz.Debug('-> name:                    ' + device.name)
                Domoticz.Debug('-> valve_position:          ' + str(device.valve_position))
                Domoticz.Debug('-> temperature_actual:      ' + ("%.1f" % device.temperature_actual))
                Domoticz.Debug('-> domoticz_percentage_id:  ' + str(device.domoticz_percentage_id))
                Domoticz.Debug('-> domoticz_temperature_id: ' + str(device.domoticz_temperature_id))
                Domoticz.Debug('-> Last seen:               ' + Devices[device.domoticz_temperature_id].LastUpdate)            

        # Set heartbeat interval
        try:
            Domoticz.Heartbeat(int(Parameters['Mode1']))
        except:
            Domoticz.Heartbeat(30)

        # Delete unknown devices
        if Parameters['Mode5'] == 'True':
            self.deleteUnknownDevices = True

        # Connect to cube
        self.tcpConn = Domoticz.Connection(Name='MaxCube', Transport='TCP/IP', Protocol='None', Address=Parameters['Address'], Port=Parameters['Port'])
        self.tcpConn.Connect()
        return True

    def onStop(self):
        # Send quit to the cube
        if self.tcpConn is not None:
            if self.tcpConn.Connected() == True:
                self.tcpConn.Send('q:\r\n')
                self.tcpConn.Disconnect()

    def onConnect(self, Connection, Status, Description):
        #Domoticz.Log('onConnect called')
        return

    def onMessage(self, Connection, Data):
        # Check if we have unprocessed data left
        if len(self.unprocessedData) > 0:
            # Join data
            Data = b''.join([self.unprocessedData, Data])

            # Clear message buffer
            self.unprocessedData = []

        # Loop over all received bytes
        while Data.__len__() > 2:
            # Search for line break
            i = Data.find(bytes([0x0D, 0x0A]))

            # Get parser function for message
            f = self.messageParserMap.get(Data[:2], None)
            
            # Check if the line break has been found
            if i != -1:
                # Check if the message type is unknown
                if f is None:
                    Domoticz.Log('Got unknown message type: ' + str(Data[:2]))
                else:
                    # Call message handler
                    f(self, Data[2:i])
                
                # Remove current message
                Data = Data[i+2:]
            else:
                # Store unprocessed data
                self.unprocessedData = Data

                # Stop processing
                break

    def onCommand(self, Unit, Command, Level, Hue):
        # Check if the socket is initialized
        if self.tcpConn is None:
            Domoticz.Error('Won\'t send command as the socket is not open')
            return
        
        # Only send commands if we got meta infos
        if self.metaDataComplete == False:
            Domoticz.Error('Won\'t send command as we didn\'t got meta infos from the Cube')
            return

        # Check if the tcp connection is open
        if self.tcpConn.Connected() == False:
            # Reconnect
            self.tcpConn.Connect()
            return
        
        # Check if the command is for a room
        if Devices[Unit].Type == MaxRoom.deviceSetpointType() and Devices[Unit].SubType == MaxRoom.deviceSetpointSubType():
            # Only update room if the room id is set => would be broadcast command otherwise
            if self.maxRooms[Devices[Unit].DeviceID].id == 0:
                Domoticz.Error('Won\'t send command as the room has no ID set (e.g. the room is unknown to the cube)')
                return
            
            # Only temperature steps of 0.5 are supported
            Level = int(Level * 2) / 2
            
            # Reset all temperatures below 5C to 0C
            if Level < 5:
                Level = 0
            
            # Build set command
            setCmd = [0x00]
            
            # Command is for a room
            setCmd.append(0x04)
            
            # We want to set a temperature
            setCmd.append(0x40)
            
            # rf_address from can be empty
            setCmd.append(0)
            setCmd.append(0)
            setCmd.append(0)
            
            # Add room address
            room_address = binascii.a2b_hex(Devices[Unit].DeviceID)
            setCmd.append(room_address[0])
            setCmd.append(room_address[1])
            setCmd.append(room_address[2])
            
            # Add room number
            setCmd.append(self.maxRooms[Devices[Unit].DeviceID].id)
            
            # Add mode and temperature
            modeTemp = 0x40 # Manual mode
            modeTemp += int(Level * 2)
            setCmd.append(modeTemp)
            
            # Until data is 2000-01-01
            setCmd.append(0)
            setCmd.append(0)
            
            # Until time is 00:00
            setCmd.append(0)
            
            # Send set command
            self.tcpConn.Send('s:' + base64.encodebytes(bytes(setCmd)).decode('utf-8').strip() + '\r\n')
            
            # Update device
            self.maxRooms[Devices[Unit].DeviceID].setpoint = Level
            self.maxRooms[Devices[Unit].DeviceID].update()
        else:
            Domoticz.Log('onCommand called for Unit ' + str(Unit) + ': Parameter ' + str(Command) + ', Level: ' + str(Level))
            Domoticz.Debug('-> Name:     ' + Devices[Unit].Name)
            Domoticz.Debug('-> DeviceID: ' + Devices[Unit].DeviceID)
            Domoticz.Debug('-> nValue:   ' + str(Devices[Unit].nValue))
            Domoticz.Debug('-> sValue:   ' + Devices[Unit].sValue)

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log('Notification: ' + Name + ',' + Subject + ',' + Text + ',' + Status + ',' + str(Priority) + ',' + Sound + ',' + ImageFile)

    def onDisconnect(self, Connection):
        # Send quit to the cube
        if self.tcpConn is None:
            return
        if self.tcpConn.Connected() == True:
            self.tcpConn.Send('q:\r\n')
            self.tcpConn.Disconnect()

    def onHeartbeat(self):
        # Request infos about the devices
        if self.tcpConn is None:
            return
        if self.tcpConn.Connected() == True and self.metaDataComplete == True:
            self.tcpConn.Send('l:\r\n')
        elif self.tcpConn.Connected() == False:
            self.tcpConn.Connect()

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return