from threading import Thread, Lock
from queue import Queue
import RPi.GPIO as GPIO
from typing import Dict
import time


class LEDController(Thread):

    def __init__(self, *, pin: int):

        super().__init__()
        self.daemon = True

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        self.pin = pin

        self.qp = Queue()
        self.locker = Lock()

        self.funcs: Dict[str, any] = {
            'on': self.on,
            'off': self.off,
            'typeA': self.typeA,
            'typeB': self.typeB,
        }

    def on(self):
        GPIO.output(self.pin, True)

    def off(self):
        GPIO.output(self.pin, False)

    def typeB(self):

        for x in range(2):
            GPIO.output(self.pin, True)
            time.sleep(0.1)
            GPIO.output(self.pin, False)
            time.sleep(0.1)

    def typeA(self):

        GPIO.output(self.pin, True)
        time.sleep(0.2)
        GPIO.output(self.pin, False)

    def run(self) -> None:
        while True:
            type = self.qp.get()
            if type in self.funcs.keys():
                with self.locker:
                    self.funcs[type]()

    def end(self):

        GPIO.output(self.pin, False)
        GPIO.cleanup()

    def __del__(self):

        GPIO.output(self.pin, False)
        GPIO.cleanup()


