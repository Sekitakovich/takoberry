import time
import board
import busio
from adafruit_tsl2561 import TSL2561
from threading import Thread
import logging


class Luminance(object):  # for TSL2561
    def __init__(self, *, address: int = 0x39):
        self.logger = logging.getLogger('Log')

        i2c = busio.I2C(scl=board.SCL, sda=board.SDA)
        self.tsl = TSL2561(i2c)

    def lux(self) -> float:
        return self.tsl.lux

    def luminosity(self) -> tuple:
        return self.tsl.luminosity


if __name__ == '__main__':
    sensor = Luminance()

    while True:

        try:
            print(sensor.tsl.lux)
            # print(sensor.tsl.luminosity)
        except KeyboardInterrupt as e:
            print()
        else:
            time.sleep(1)