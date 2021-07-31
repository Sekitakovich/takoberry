import time
import pigpio
from loguru import logger


class Sample(object):
    '''
    pigpiod -l # -mをつけるとcallbackが効かない!
    GPIO --- タクトスイッチ --- GND
    チャタリングで0と1がバラっと続くが試験なので
    '''

    def __init__(self, *, intPin: int = 17, needPullUp: bool = True):
        self.intPin = intPin
        self.needPullUp = needPullUp

        self.pi = pigpio.pi()

        self.pi.set_mode(self.intPin, mode=pigpio.INPUT)  # 入力に設定
        if self.needPullUp:
            self.pi.set_pull_up_down(self.intPin, pigpio.PUD_UP)  # 内蔵プルアップを有効にする
            logger.debug(f'with PULLUP')
        self.counter = 0
        cb = self.pi.callback(self.intPin, pigpio.EITHER_EDGE, self.handler)
        # logger.info(cb)

    def readValue(self) -> int:
        return self.pi.read(self.intPin)

    def handler(self, gpio, level, tick):
        logger.debug(f'[{self.counter}] G={gpio} L={level}, T={tick}')
        self.counter += 1

    def close(self):
        self.pi.stop()
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
