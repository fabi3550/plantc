#!/usr/bin/python

# TESTS

# (1) No WIFI available
# (2) Wrong connection data
# (3) No sensor contact
# (4) miscellenaous sensor data

import network
import time
import urequests
import ujson

class PlantClient(object):

    def __init__(self):

        self.configuration = self.readConfiguration()
        print(type(self.configuration))

        sensor_data = self.readSensorData()

        if len(sensor_data) > 0:
            self.wifi_object = self.connectToWIFI(
                self.configuration["WifiSSID"],
                self.configuration["WifiPassword"]
            )

            if self.wifi_object.isconnected():
                self.postSensorData(sensor_data)

                if self.disconnectWIFI():
                    time.sleep(self.configuration["TimeForDeepSleep"])
            else:
                # maybe store sensor data with timestamp locally to send it later
                pass



    # inits a WIFI connection an returns it
    def connectToWIFI(self, ssid, password):

        print("Connecting to WIFI " + ssid)
        station_adapter = network.WLAN(network.STA_IF)

        try:
            station_adapter.connect(ssid, password)
        except OSerror as e:
            print(e)

        timeout = self.configuration["WifiConnectionTimeout"]
        interval = 0.5

        while not station_adapter.isconnected():
            timeout -= interval
            time.sleep(interval)
            if timeout <= 0:
                print("Connection timed out")
                break

        return station_adapter

    # disconnects from WIFI
    def disconnectWIFI(self):

        print("Disconnecting WIFI...")
        self.wifi_object.disconnect()
        return self.wifi_object.isconnected()

    # reads data from the chirp sensor and returns a dict object
    # with all relevant information
    def readSensorData(self):

        data = {}

        # some magic happens and then there was data...
        light = 1005
        temperature = 18.9
        capacity = 245

        data["light"] = light
        data["temperature"] = temperature
        data["capacity"] = capacity

        return data

    # posts the data from the sensor as json object via http to the given host
    def postSensorData(self, data):

        print("Posting sensor data")
        response = 0

        try:
            response = urequests.post(
                self.configuration["HttpHost"] + ":" + str(self.configuration["HttpPort"]),
                json = data,
                headers = {"Content-Type": "application/json"}
            )

        except OSError as e:
            print(e)

    # reads the plantc.conf in the local filesystem
    def readConfiguration(self):

        config = {}

        try:
            f = open("plantc.conf", "r")
            config = ujson.loads(f.read())

        except OSError as e:
            print(e)

        return config
