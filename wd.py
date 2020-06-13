from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import FileModifiedEvent
import pathlib
import time

from loguru import logger


class Handler(FileSystemEventHandler):
    def __init__(self, *, target: str):
        super().__init__()
        self.target = target

    def on_any_event(self, event):
        file = pathlib.Path(event.src_path)
        name = file.name
        if name == self.target:
            logger.debug(name)

    def on_deleted(self, event: FileModifiedEvent):
        file = pathlib.Path(event.src_path)
        name = file.name
        if name == self.target:
            logger.debug(name)

    def on_moved(self, event: FileModifiedEvent):
        file = pathlib.Path(event.src_path)
        name = file.name
        if name == self.target:
            logger.debug(name)

    def on_created(self, event: FileModifiedEvent):
        file = pathlib.Path(event.src_path)
        name = file.name
        if name == self.target:
            logger.debug(name)

    def on_modified(self, event: FileModifiedEvent):
        file = pathlib.Path(event.src_path)
        name = file.name
        if name == self.target:
            logger.debug(name)


if __name__ == '__main__':

    handler = Handler(target='sample.txt')
    observer = Observer()
    observer.schedule(event_handler=handler, path='./')
    observer.start()

    while True:
        time.sleep(10)
        with open('sample.txt', 'wt') as f:
            f.write('OK')

