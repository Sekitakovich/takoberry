from serial import Serial, SerialException, SerialTimeoutException
from typing import List, Dict
from threading import Thread, Lock
from multiprocessing import Process, Queue as MPQueue
from queue import Queue
from functools import reduce
from operator import xor
import time
import json
from dataclasses import dataclass, asdict
import requests
from datetime import datetime as dt
from datetime import timedelta
from logging import getLogger
import argparse
import configparser
from pprint import pprint

from log import LogConfigure
from led import LEDController
from motion import Motion


@dataclass()
class Must(object):
    lat: float = 0.0
    lng: float = 0.0
    sog: float = 0.0
    cog: float = 0.0
    ns: str = ''
    ew: str = ''
    utc: str = ''
    jst: str = ''
    mode: str = ''  # N<A<D<E


@dataclass()
class DOP(object):
    p: float = 0.0
    h: float = 0.0
    v: float = 0.0


@dataclass()
class Plus(object):
    alt: float = 0.0
    sats: int = 0
    kmh: float = 0.0
    dop: DOP = DOP()


@dataclass()
class Location(object):
    must: Must = Must()
    plus: Plus = Plus()


class Driver(Thread):

    def __init__(self, *, sp: Serial, qp: Queue, dump: bool, cs: str):

        super().__init__()
        self.daemon = True
        self.logger = getLogger('Log')

        self.location = Location()

        self.sp = sp
        self.qp = qp
        self.cs = cs  # cycle suffix

        self.GPSdatetimeFormat: str = '%d-%d-%d %d:%d:%d'
        self.SYSdatetimeformat: str = '%Y-%m-%d %H:%M:%S'

        self.dump = dump
        self.counter: int = 0

    def run(self) -> None:
        while True:
            sentence = self.qp.get()
            if len(sentence):
                self.loadSentence(item=sentence)
            else:
                pass

    def loadSentence(self, *, item: List[str]):

        def atRMC() -> bool:

            valid: bool = False

            if item[2] == 'A':
                valid = True
                ymd = item[9]
                hms = item[1]
                utcSring: str = self.GPSdatetimeFormat % (
                    int(ymd[4:6]) + 2000, int(ymd[2:4]), int(ymd[0:2]), int(hms[0:2]), int(hms[2:4]), int(hms[4:6])
                )
                jst = (dt.strptime(utcSring, self.SYSdatetimeformat) + timedelta(hours=9)).strftime(
                    self.SYSdatetimeformat)
                self.location.must.utc = utcSring
                self.location.must.jst = jst

                self.location.must.lat = float(item[3]) if item[3] else 0.0
                self.location.must.ns = item[4]
                self.location.must.lng = float(item[5]) if item[5] else 0.0
                self.location.must.ew = item[6]
                self.location.must.sog = float(item[7]) if item[7] else 0.0
                self.location.must.cog = float(item[8]) if item[8] else 0.0
                self.location.must.mode = item[12]
            else:
                # self.logger.debug(msg='Not valid')
                pass
            return valid

        def atGGA():

            valid: bool = False

            if item[6] != '0':
                valid = True
                self.location.plus.sats = int(item[7]) if item[7] else 0
                self.location.plus.alt = float(item[9]) if item[9] else 0.0

            return valid

        def atVTG():

            valid: bool = False

            if item[9] != 'N':
                valid = True
                self.location.plus.kmh = float(item[7]) if item[7] else 0.0

            return valid

        def atGSA():

            valid: bool = False

            if item[2] != '1':
                valid = True
                self.location.plus.dop.p = float(item[4]) if item[4] else 0.0
                self.location.plus.dop.h = float(item[5]) if item[5] else 0.0
                self.location.plus.dop.v = float(item[6]) if item[6] else 0.0

            return valid

        def atTXT():

            valid: bool = False
            # self.logger.debug(msg=item[4])
            return valid

        def atZDA():

            valid: bool = False
            # self.logger.debug(msg=item[4])
            return valid

        window: Dict[str, any] = {
            'RMC': atRMC,
            'GGA': atGGA,
            'VTG': atVTG,
            'GSA': atGSA,
            'ZDA': atZDA,
            'TXT': atTXT,
        }

        try:
            if self.dump:
                self.logger.debug(msg=item)
            suffix = item[0][2:]
            if suffix in window.keys():
                valid: bool = window[suffix]()
                if suffix == self.cs:
                    if valid:
                        self.counter += 1
        except (IndexError, ValueError) as e:
            self.logger.error(msg=e)
        else:
            pass

    # def checkNMEA(self, *, nmea: str) -> list:
    #
    #     result = []
    #
    #     part: list = nmea.split('*')
    #     if len(part) == 2:
    #         try:
    #             body: str = part[0][1:]
    #             your: int = int(part[1], 16)
    #             mine: int = reduce(xor, body.encode(), 0)
    #         except (IndexError, ValueError) as e:
    #             self.logger.error(msg=e)
    #         else:
    #             if your == mine:
    #                 return body.split(',')
    #
    #     return result


class Sender(Thread):

    def __init__(self, *, url: str, sq: Queue):

        super().__init__()
        self.daemon = True
        self.logger = getLogger('Log')

        self.sq = sq
        self.locker = Lock()
        self.url = url
        self.headers: Dict[str, str] = {
            'Content-Type': 'application/json',
        }
        self.online: bool = True

        self.feedFIFO: List[str] = []
        self.lastFeedAT = dt.now()
        self.retryInterval: int = 15
        self.retryPassedSecs: int = 30
        self.maxHolds: int = 3600

        self.retryThread = Thread(target=self.retryStage, daemon=True)
        self.retryThread.start()

        self.led = LEDController(pin=19)
        self.led.start()

    def upload(self, *, content: str) -> bool:

        # pprint(content)

        success: bool = True
        try:
            response = requests.post(self.url, data=content, headers=self.headers, timeout=1.0)
        except (
                requests.exceptions.Timeout, requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError) as e:
            success = False
            self.online = False
            self.logger.error(msg=e)
        else:
            self.online = True
            if response.status_code == 200:
                # self.logger.debug(msg='send success')
                pass
            else:
                self.logger.error(msg=response.status_code)

        return success

    def retryStage(self):

        while True:
            time.sleep(self.retryInterval)
            if len(self.feedFIFO):
                if (dt.now() - self.lastFeedAT).total_seconds() > self.retryPassedSecs:
                    self.logger.debug('Holding %d record(s)' % len(self.feedFIFO))
                    if self.session():
                        pass
                        # self.logger.debug(msg='Success')

    def session(self) -> bool:
        success: bool = False
        many: int =len(self.feedFIFO)
        with self.locker:
            content: str = json.dumps(self.feedFIFO, indent=0)
            if self.upload(content=content):
                self.feedFIFO.clear()
                success = True
                self.logger.debug(msg='Success (%d)' % many)
        self.led.qp.put('typeA' if success else 'typeB')
        return success

    def run(self) -> None:

        while True:

            src = self.sq.get()
            with self.locker:
                many: int = len(self.feedFIFO)
                if many == self.maxHolds:  # buffer full?
                    del (self.feedFIFO[0])
                    self.logger.critical(msg='feed buffer FULL (%d)' % self.maxHolds)
                self.feedFIFO.append(src.copy())  # notice! use copy
            if self.session():
                # self.logger.debug(msg='Success (%d)' % many)
                pass
            self.lastFeedAT = dt.now()


class Receiver(Thread):

    def __init__(self, *, sp: Serial, qp: Queue):

        super().__init__()
        self.daemon = True
        self.logger = getLogger('Log')

        self.sp = sp
        self.qp = qp

        self.cp = Queue()
        self.checker = Thread(target=self.checkSentence, daemon=True)
        self.checker.start()

    def checkSentence(self):

        while True:
            raw: bytes = self.cp.get()
            if len(raw) > 2:  # CR/LF
                sentence: str = raw[:-2].decode()
                part: list = sentence.split('*')
                if len(part) == 2:
                    try:
                        body: str = part[0][1:]
                        your: int = int(part[1], 16)
                        mine: int = reduce(xor, body.encode(), 0)
                    except (IndexError, ValueError) as e:
                        self.logger.error(msg=e)
                    else:
                        if your == mine:
                            self.qp.put(body.split(','))
                else:
                    self.logger.debug(msg='invalid sentence (%s)' % raw)
                    pass
            else:
                self.logger.debug(msg='invalid sentence (%s)' % raw)
                pass

    def run(self) -> None:

        while True:
            try:
                raw: bytes = self.sp.readline()
            except (SerialException, SerialTimeoutException) as e:
                self.logger.error(msg=e)
            else:
                if raw:
                    self.cp.put(raw)


class GPSFeeder(object):

    def __init__(self, *, port: str, baudrate: int, number: str, url: str, dump: bool, cs: str):

        self.logger = getLogger('Log')

        self.dump = dump
        self.port = port
        self.baudrate = baudrate
        self.url = url
        self.number = number
        self.cs = suffix

        self.ready: bool = True
        self.loopCounter: int = 0
        self.sends: int = 0
        self.report: Dict[str, any] = {
            'number': number,
            'location': '',
        }
        self.qp = Queue()
        self.sq = Queue()

        self.sleepTable: List[dict] = [
            # {'max': 5, 'val': 60 * 1},
            # {'max': 10, 'val': 30 * 1},
            # {'max': 20, 'val': 4},
            # {'max': 40, 'val': 3},
            # {'max': 80, 'val': 2},
            {'max': 5, 'val': 15},
            {'max': 10, 'val': 30},
            {'max': 20, 'val': 4},
            {'max': 40, 'val': 3},
            {'max': 80, 'val': 2},
        ]

        try:
            sp = Serial(port=port, baudrate=baudrate)
        except (SerialException,) as e:
            self.ready = False
            self.logger.error(msg=e)
        else:

            self.receiver = Receiver(sp=sp, qp=self.qp)
            self.driver = Driver(sp=sp, qp=self.qp, dump=self.dump, cs=self.cs)
            self.sender = Sender(url=url, sq=self.sq)
            self.motion = Motion(address=0x1D, threshold=20)  # 歩行ならこの程度だがクルマだと30以上か
            self.led = LEDController(pin=26)

            self.intervalSecs: int = 1

    def sendThis(self):

        self.report['location'] = asdict(self.driver.location)
        self.sq.put(self.report)
        self.sends += 1

    def calcTiming(self, *, kmh: int) -> int:

        value: int = 1  # default

        for s in self.sleepTable:
            if kmh < s['max']:
                value = s['val']
                break

        return value

    def mainLoop(self):

        self.logger.info(msg='Start on %s:%d %s@%s' % (self.port, self.baudrate, self.number, self.url))

        lastCounter: int = 0
        timing: int = 1
        lastTiming: int = 1
        isGPS: bool = False

        self.receiver.start()
        self.driver.start()
        self.sender.start()
        self.motion.start()
        self.led.start()

        while True:

            try:
                # print(self.motion.isMoving)
                thisCounter = self.driver.counter
                if thisCounter != lastCounter:  # changed
                    self.led.qp.put('typeA')
                    isGPS = True
                    if (self.loopCounter % timing) == 0:
                        if self.motion.active:
                            self.sendThis()
                        else:
                            self.logger.debug(msg='not in active ...')
                    else:
                        pass
                    timing = self.calcTiming(kmh=int(self.driver.location.plus.kmh))
                    if timing != lastTiming:
                        self.logger.debug('timing was shifted %d -> %d' % (lastTiming, timing))
                        lastTiming = timing
                    else:
                        pass
                    lastCounter = thisCounter
                else:
                    self.led.qp.put('typeB')
                    if isGPS:
                        isGPS = False
                        timing = 1
                        lastTiming = 1
                        self.logger.critical(msg='GPS lost')
                    else:
                        # self.logger.debug(msg='Waiting (%d)' % (self.loopCounter,))
                        pass

                time.sleep(self.intervalSecs)
                self.loopCounter += 1
            except (KeyboardInterrupt,) as e:
                self.led.end()
                break
            else:
                pass


if __name__ == '__main__':

    version: str = '1.0'
    suffix: str = 'RMC'

    argParser = argparse.ArgumentParser(description='GPS autofeeder')
    argParser.add_argument('-s', '--suffix', help='suffix of cycle period (%s)' % suffix, type=str, default=suffix)
    argParser.add_argument('-d', '--dump', help='dump sentence realtime', action='store_true')
    argParser.add_argument('-v', '--version', help='print version', action='version', version=version)

    args = argParser.parse_args()

    iniParser = configparser.ConfigParser()
    iniParser.read('config.ini')

    number: str = iniParser['Equipment']['serialnumber']
    url: str = iniParser['Setting']['url']
    port: str = iniParser['Setting']['port']
    baudrate: int = int(iniParser['Setting']['baudrate'])

    LogConfigure(file='logs/client.log')

    feeder = GPSFeeder(port=port, baudrate=baudrate, number=number, url=url,
                       dump=args.dump, cs=args.suffix)

    if feeder.ready:
        feeder.mainLoop()
