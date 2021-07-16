import pigpio
import time
from loguru import logger


class Sample(object):
    PIN12 = 12
    PIN13 = 13
    PIN18 = 18
    PIN19 = 19

    def __init__(self, *, pinNumber: int):
        self.pi = pigpio.pi()
        self.pinNumber = pinNumber
        self.isActive = False
        logger.info(f'Ready with GPIO[{self.pinNumber}]')

    def start(self, *, frequency: int=1, Duty: float=50.0):
        if self.isActive is False:
            dutyCycle = int((Duty * 1000000) / 100)
            logger.debug(f'Start with {frequency}Hz : Duty {Duty}')
            self.pi.hardware_PWM(self.pinNumber, frequency, dutyCycle)
            self.isActive = True
        else:
            logger.error(f'Device is in active')

    def stop(self):
        if self.isActive is True:
            self.pi.write(self.pinNumber, 0)
            logger.debug(f'stop')
        else:
            logger.error(f'Device is not in active')


if __name__ == '__main__':
    def main():
        C = Sample(pinNumber=Sample.PIN18)
        C.start()
        time.sleep(5)
        C.stop()
        pass


    main()
