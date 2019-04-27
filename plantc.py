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
import machine
import math
import network
import ubinascii
from uhashlib import sha256
from plant_unit import Sensor, WaterPump, WateringUnit

class PlantClient(object):

    def __init__(self):

        self.isactive = True

        try:

            # read configuration file
            self.configuration = self.readConfiguration()

            # init watering unit components
            self.wateringunit = WateringUnit(self.configuration["units"][0])

        except ValueError as e:
            self.setActive(False)
            print("Error in configuration data")

        except KeyError as e:
            self.setActive(False)
            print("Error in configuration data")


        while self.isActive():
            sensor_data = self.readSensorData()

            self.wifi_object = self.connectToWIFI(
                self.configuration["network"]["WifiSSID"],
                self.configuration["network"]["WifiPassword"]
            )

            if self.wifi_object.isconnected():
                response = self.postSensorData(sensor_data)

                if (response.status_code == 200):
                    action = response.json()['action']

                    if action == 'REGISTER':
                        self.postRegistration()

                    elif action == 'PUMP':
                        duration = int(response.json()['duration'])
                        self.wateringunit.getWaterPump().pumpWater(duration)

                    elif action == 'DENIED':
                        self.setActive(False)

            if self.disconnectWIFI():
                print("Sleeping " + str(self.configuration["network"]["TimeForDeepSleep"]) + " seconds")

                # going in deep sleep mode
                machine.deepsleep(self.configuration["network"]["TimeForDeepSleep"] * 1000)


    # determines if client is set active
    def isActive(self):
        return self.active


    # setter variable for client activity
    def setActive(self, bool):
        self.active = bool

    # inits a WIFI connection an returns it
    def connectToWIFI(self, ssid, password):

        print("Connecting to WIFI " + ssid)

        try:
            station_adapter = network.WLAN(network.STA_IF)
            station_adapter.active(True)
            station_adapter.connect(ssid, password)

            timeout = self.configuration["network"]["WifiConnectionTimeout"]
            interval = 0.5

            while not station_adapter.isconnected():
                timeout -= interval
                time.sleep(interval)
                if timeout <= 0:
                    print("Connection timed out")
                    break
        except OSError as e:
            print(e)

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

        # collect sensor data from all sensors listed in plantc.conf
        for sensor in self.configuration["sensors"]:
            sensorname = sensor["sensorname"]
            data[sensorname] = self.getAvgTouchValue(sensor["pin"], 1000, 10)

        # sign with sha256 hash of the clients mac address
        data['client'] = self.getClientHash()

        return data


    # posts the data from the sensor as json object via http to the given host
    def postSensorData(self, data):
        response = 0

        try:
            response = urequests.post(
                ''.join('%s:%s' % (self.configuration["host"]["HttpHost"], str(self.configuration["host"]["HttpPort"]))),
                json = data,
                headers = {"Content-Type": "application/json"}
            )

        except OSError as e:
            print(e)

        except ValueError as e:
            print(e)

        return response


    # unknown clients in an old installation with multiple plant clients
    # will be asked for registration
    def postRegistration(self):
        response = 0

        data = {'mac': self.getMacAddress()}

        try:

            response = urequests.post(
                ''.join('%s:%s/register' % (self.configuration["host"]["HttpHost"], str(self.configuration["host"]["HttpPort"]))),
                json = data,
                headers = {"Content-Type": "application/json"}
            )

        except OSError as e:
            print(e)

        except ValueError as e:
            print(e)

        return response


    # +++++ Function getAvgTouchValue +++++

    # --> pin is gpio number of touchpad input
    # --> total is time of measurement in milliseconds
    # --> interval is interval bewtween meausurents in milliseconds
    # <-- returns an average value of the measurements within total

    def getAvgTouchValue(self, pin, total, interval):

        # verify that total and interval are valid
        if total > interval:
            if (total % interval) == 0:
                measurements = total/interval
            else:
                measurements = (total/interval) + 1

            # accessing touchpad pin
            touch = machine.TouchPad(machine.Pin(pin))

            sum_touchvalues = 0
            sum_measurements = measurements

            while measurements > 0:

                touchvalue = touch.read()
                sum_touchvalues += touchvalue
                time.sleep(interval/1000)
                measurements -= 1

            return math.floor(sum_touchvalues/sum_measurements)


    # reads the plantc.conf in the local filesystem
    def readConfiguration(self):
        config = {}

        try:
            f = open("plantc.json", "r")
            config = ujson.loads(f.read())
            f.close()

        except OSError as e:
            print(e)

        return config


    # returs the mac address of the wifi card
    def getMacAddress(self):
        return ubinascii.hexlify(network.WLAN().config('mac')).decode()


    # returns the sha256 hash of the clients mac address
    def getClientHash(self):
        mac = self.getMacAddress()
        hash = sha256(mac)
        hashstring = ''.join(['{:02x}'.format(b) for b in hash.digest()])
        return hashstring
