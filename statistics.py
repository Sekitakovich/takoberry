from threading import Thread
import time
from typing import Dict
from dataclasses import dataclass
import psutil


@dataclass()
class Info(object):
    cpu: float = 0.0
    mem: float = 0.0


class Statistics(Thread):

    def __init__(self):

        super().__init__()
        self.daemon = True

        self.info = Info()

    def aboutCPU(self):
        self.info.cpu = psutil.cpu_percent(interval=1)

    def aboutMEM(self):
        memory = psutil.virtual_memory()
        self.info.mem = memory.percent

    def run(self) -> None:
        while True:
            self.aboutMEM()
            self.aboutCPU()
            time.sleep(5)


if __name__ == '__main__':

    stat = Statistics()
    stat.start()

    while True:

        time.sleep(1)
        print(stat.info)