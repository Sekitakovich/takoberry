import time
import pigpio
from loguru import logger


class Sample(object):
    '''
    pigpioのcallback
    '''
    def __init__(self, *, intPin: int = 17, needPullUp: bool = True):
        self.intPin = intPin
        self.needPullUp = needPullUp

        self.pi = pigpio.pi()

        '''
        sensing
        '''
        self.sensor = self.pi.i2c_open(i2c_bus=1, i2c_address=self.address)
        logger.info(f'sensor = {self.sensor}')

        self.enable()

        '''
        intererupt
        '''
        self.pi.set_mode(self.intPin, mode=pigpio.INPUT)  # 入力に設定
        if self.needPullUp:
            self.pi.set_pull_up_down(self.intPin, pigpio.PUD_UP)  # 内蔵プルアップを有効にする
        cb = self.pi.callback(self.intPin, pigpio.EITHER_EDGE, self.handler)
        logger.info(cb)

    def enable(self) -> None:
        value = 0x7F
        self.pi.i2c_write_byte_data(handle=self.sensor, reg=0x80, byte_val=value)
        pass

    def read(self, *, register: int, length: int) -> str:
        b, d = self.pi.i2c_read_i2c_block_data(self.sensor, register, length)
        # logger.debug(f'b={b} d={d}')
        return self.hexdump(data=d)

    def hexdump(self, *, data: bytes) -> str:
        src = [f'{b:02X}' for b in data]
        dst = ':'.join(src)
        return dst

    def __del__(self):
        self.pi.stop()

    def handler(self, gpio, level, tick):
        logger.debug(f'G={gpio} L={level}, T={tick}')


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
                logger.info(f'counter {counter}')
                G = S.read(register=0xFC, length=4)
                logger.debug(G)
                # U = S.read(register=0xFC, length=1)
                # D = S.read(register=0xFD, length=1)
                # L = S.read(register=0xFE, length=1)
                # R = S.read(register=0xFF, length=1)
                # logger.debug(f'U:D:L:R = [{U} {D} {L} {R}]')
        pass


    main()
