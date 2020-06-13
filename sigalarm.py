import signal
import time
from datetime import datetime as dt
from threading import Event, Thread
from typing import List

from loguru import logger


class CrystalK(object):
    def __init__(self, *, interval: float = 1):
        self.counter: int = 0
        self.interval = interval
        self.heaertBeat = Event()

    def _handler(self, arg1, arg2):  # void arg1, arg2
        self.counter += 1
        self.heaertBeat.set()

    def begin(self):
        signal.signal(signal.SIGALRM, self._handler)
        signal.setitimer(signal.ITIMER_REAL, self.interval, self.interval)


class Child(Thread):
    def __init__(self, *, hb: Event):
        super().__init__()
        self.daemon = True
        self.hb = hb

    def run(self) -> None:
        passing: List[float] = []
        counter: int = 0
        last = dt.now()
        while True:
            self.hb.clear()
            self.hb.wait()
            # clocker.heaertBeat.clear()
            ts = time.time()
            this = dt.now()
            secs = (this - last).total_seconds()
            passing.append(secs)
            average = sum(passing)/ len(passing)
            te = time.time()
            logger.debug('%d: use %f after %f average = %f' % (counter, te-ts, secs, average))
            last = this
            counter += 1


if __name__ == '__main__':

    clocker = CrystalK(interval=0.5)

    logger.info('Child start')
    child = Child(hb=clocker.heaertBeat)
    child.start()

    logger.info('Heartbeaet Start')
    clocker.begin()

    time.sleep(60)
