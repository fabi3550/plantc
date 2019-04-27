import json
from machine import Pin, PWM
import time

class Sensor(object):
    def __init__(self, pin, lowerbias):
        self.pin = pin
        self.lowerbias = lowerbias

    def getPinNumber(self):
        return self.pin

    def getLowerBias(self):
        return self.lowerbias

class MoistureSensor(Sensor):
    def __init__(self, pin, lowerbias, upperbias):
        Sensor.__init__(self, pin, lowerbias)
        self.upperbias = upperbias

    def getUpperBias(self):
        return self.upperbias

class WaterPump(object):

    def __init__(self, pin, pwm_level):
        self.pin = pin
        self.pwm_level = pwm_level
        self.pwm = machine.PWM(machine.Pin(self.pin))

    def getPWMLevel(self):
        return self.pwd_level

    def getPinNumber(self):
        return self.pin

    def pumpWater(self, seconds=30):

        self.pwm.freq(500)
        self.pwm.duty(math.floor(self.pwm_level*1023))
        time.sleep(seconds)
        self.pwm.duty(0)
        return True


class WateringUnit(object):
    def __init__(self, junit):
        self.junit = junit
        self.isvalid = False

        # init sensors
        for sensor in self.junit["unit"]["sensors"]:
            if (sensor.keys()[0] == "moisture"):
                self.moisture = MoistureSensor(
                    sensor["moisture"]["pin"],
                    sensor["moisture"]["lower_bias"],
                    sensor["moisture"]["upper_bias"]
                )

            if (sensor.keys()[0] == "waterlevel"):
                self.waterlevel = Sensor(
                    sensor["waterlevel"]["pin"],
                    sensor["waterlevel"]["lower_bias"],
                )

        # init waterpump
        if "pump" in self.junit["unit"]:
            self.pump = WaterPump(
                self.junit["unit"]["pump"]["pin"],
                self.junit["unit"]["pump"]["pwd_level"]
            )

        # check for all sensors and actors
        if (
            (self.moisture is not None)
            and (self.waterlevel is not None)
            and (self.pump is not None)
            ):
            self.isvalid = True

    def isValid(self):
        return self.isvalid

    def getMoistureSensor(self):
        return self.moisture

    def getWaterLevelSensor(self):
        return self.waterlevel

    def getWaterPump(self):
        return self.pump


if __name__ == "__main__":

    try:
        f = open("plantc.json", "r")
        jdata = json.loads(f.read())

        for unit in jdata["units"]:
            wateringunit = WateringUnit(unit)

            print(wateringunit.getMoistureSensor().getLowerBias())
            print(wateringunit.getMoistureSensor().getUpperBias())
            print(wateringunit.getMoistureSensor().getPinNumber())

            print(wateringunit.getWaterLevelSensor().getLowerBias())
            print(wateringunit.getWaterLevelSensor().getPinNumber())

            print(wateringunit.getWaterPump().getPWDLevel())
            print(wateringunit.getWaterPump().getPinNumber())


        f.close()
    except IOError as e:
        print(e)
