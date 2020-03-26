import board
import busio
from adafruit_ina219 import INA219
import time


class Sensor(object):
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.device = INA219(i2c)

    def measure(self):
        bus_voltage = self.device.bus_voltage
        shunt_voltage = self.device.shunt_voltage
        current = self.device.current
        print("PSU Voltage:   {:6.3f} V".format(bus_voltage + shunt_voltage))
        print("Shunt Voltage: {:9.6f} V".format(shunt_voltage))
        print("Load Voltage:  {:6.3f} V".format(bus_voltage))
        print("Current:       {:9.6f} A".format(current / 1000))
        print('')


if __name__ == '__main__':
    sensor = Sensor()

    while True:
        time.sleep(3)
        sensor.measure()
