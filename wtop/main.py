from typing import List
import time
import psutil
from threading import Thread, Lock
from dataclasses import dataclass, field, asdict
import json5
from loguru import logger


@dataclass()
class CPU(object):
    core: int = 0
    percentage: List[float] = field(default_factory=list)

@dataclass()
class Memory(object):
    total: int = 0
    percentage: float = 0.0


class Collector(Thread):
    def __init__(self, *, interval: int=2):
        super().__init__()

        self.daemon = True
        self.interval = interval
        self.counter = 0
        self.locker = Lock()

        self.cpu = CPU()
        self.memory = Memory()

    def get(self) -> str:
        with self.locker:
            return json5.dumps({
                'cpu': asdict(self.cpu),
                'memory': asdict(self.memory)
            }, indent=2)

    def run(self) -> None:
        while True:
            with self.locker:
                self.cpu.core = psutil.cpu_count(logical=False)
                self.cpu.percentage = psutil.cpu_percent(interval=1, percpu=True)

                memory = psutil.virtual_memory()
                self.memory.total = memory.total
                self.memory.percentage = memory.percent

                self.counter += 1
            time.sleep(self.interval)


if __name__ == '__main__':

    c = Collector()
    c.start()

    while True:
        if c.counter:
            logger.debug(c.get())
        time.sleep(3)