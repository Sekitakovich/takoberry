import time
import board
import busio
import adafruit_adxl34x
from threading import Thread
import logging

from constants import Constants
from led import LEDController


class Motion(Thread):  # for ADXL345

    def __init__(self, *, address: int = 0x53, threshold: int = 18, vervose: bool = False):

        super().__init__()
        self.daemon = True
        self.vervose = vervose
        self.logger = logging.getLogger('Log')

        self.logger.debug('threshold = %d' % threshold)

        self.active: bool = False
        self.shortInterval = 0.25
        self.longInterval = 15

        self.led = LEDController(pin=21)
        self.led.start()
        self.led.qp.put('off')
        # thisBoard = board
        # print(thisBoard)

        i2c = busio.I2C(scl=board.SCL, sda=board.SDA)
        self.accelerometer = adafruit_adxl34x.ADXL345(i2c, address=address)
        self.accelerometer.enable_motion_detection(threshold=threshold)

    def run(self) -> None:
        while True:
            current: bool = self.accelerometer.events['motion']
            if self.active != current:
                if self.vervose:
                    print(current)
                self.active = current
                self.led.qp.put('on' if current else 'off')
                # self.logger.debug(msg='change to Active' if current else 'Stationary ...')
            time.sleep(self.longInterval if current else self.shortInterval)


if __name__ == '__main__':

    motion = Motion(address=0x1D, vervose=True)
    motion.start()

    while True:
        time.sleep(60)
