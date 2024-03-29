import time
import RPi.GPIO as GPIO
from loguru import logger


class Sample(object):
    '''
    RPi.GPIO
    GPIO --- タクトスイッチ --- GND
    bouncetimeはアテにならないのでチャタリング対策は外でやるべし
    '''

    def __init__(self, *, intPin: int = 17, needPullUp: bool = True):
        self.intPin = intPin
        self.needPullUp = needPullUp

        self.counter = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.intPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.intPin, GPIO.BOTH, callback=self.handler, bouncetime=5)

    def readValue(self) -> int:
        return GPIO.input(self.intPin)

    def handler(self, pin):
        value = self.readValue()
        logger.debug(f'[{self.counter}] {pin} = {value}')
        self.counter += 1

    def close(self):
        GPIO.remove_event_detect(self.intPin)
        GPIO.cleanup()
        logger.info(f'Bye!')


if __name__ == '__main__':
    def main():
        S = Sample()
        logger.info('Start')
        loop = True
        counter = 0
        while loop:
            try:
                time.sleep(1)
            except (KeyboardInterrupt) as e:
                loop = False
            else:
                counter += 1
                # value = S.readValue()
                # logger.info(f'counter {counter} value = {value}')

        S.close()

    main()
