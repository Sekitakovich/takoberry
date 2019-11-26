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
import RPi.GPIO as GPIO
from pprint import pprint

from log import LogConfigure


@dataclass()
class Must(object):
    lat: float = 0.0
    lng: float = 0.0
    sog: float = 0.0
    cog: float = 0.0
    ns: str = ''
    ew: str = ''
    utc: str = ''
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

        self.at: str = dt.now().strftime(self.SYSdatetimeformat)  # notice!
        self.dump = dump
        self.counter: int = 0

    def run(self) -> None:
        while True:
            nmea: str = self.qp.get()
            sentence = self.checkNMEA(nmea=nmea)
            if len(sentence):
                self.loadSentence(item=sentence)
            else:
                self.logger.critical(msg='invalid sentence (%s)' % nmea.encode())

    def loadSentence(self, *, item: List[str]):

        def atRMC():

            if item[2] == 'A':
                ymd = item[9]
                hms = item[1]
                utcSring: str = self.GPSdatetimeFormat % (
                    int(ymd[4:6]) + 2000, int(ymd[2:4]), int(ymd[0:2]), int(hms[0:2]), int(hms[2:4]), int(hms[4:6])
                )
                jst = (dt.strptime(utcSring, self.SYSdatetimeformat) + timedelta(hours=9)).strftime(
                    self.SYSdatetimeformat)
                self.location.must.utc = utcSring

                self.location.must.lat = float(item[3]) if item[3] else 0.0
                self.location.must.ns = item[4]
                self.location.must.lng = float(item[5]) if item[5] else 0.0
                self.location.must.ew = item[6]
                self.location.must.sog = float(item[7]) if item[7] else 0.0
                self.location.must.cog = float(item[8]) if item[8] else 0.0
                self.location.must.mode = item[12]

                self.at = jst
                # self.counter += 1

        def atGGA():

            if item[6] != '0':
                self.location.plus.sats = int(item[7]) if item[7] else 0
                self.location.plus.alt = float(item[9]) if item[9] else 0.0

        def atVTG():

            if item[9] != 'N':
                self.location.plus.kmh = float(item[7]) if item[7] else 0.0

        def atGSA():

            if item[2] != '1':
                self.location.plus.dop.p = float(item[4]) if item[4] else 0.0
                self.location.plus.dop.h = float(item[5]) if item[5] else 0.0
                self.location.plus.dop.v = float(item[6]) if item[6] else 0.0

        def atTXT():

            # self.logger.debug(msg=item[4])
            pass

        def atZDA():

            # self.logger.debug(msg=item[4])
            pass

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
                window[suffix]()
                if suffix == self.cs:
                    self.counter += 1
        except (IndexError, ValueError) as e:
            self.logger.error(msg=e)
        else:
            pass

    def checkNMEA(self, *, nmea: str) -> list:

        result = []

        part: list = nmea.split('*')
        if len(part) == 2:
            try:
                body: str = part[0][1:]
                your: int = int(part[1], 16)
                mine: int = reduce(xor, body.encode(), 0)
            except (IndexError, ValueError) as e:
                self.logger.error(msg=e)
            else:
                if your == mine:
                    return body.split(',')

        return result


class Receiver(Thread):

    def __init__(self, *, sp: Serial, qp: Queue):

        super().__init__()
        self.daemon = True
        self.logger = getLogger('Log')

        self.sp = sp
        self.qp = qp

    def run(self) -> None:

        while True:
            try:
                raw: bytes = self.sp.readline()
            except (SerialException, SerialTimeoutException) as e:
                self.logger.error(msg=e)
            else:
                if len(raw) >= 2:
                    text: str = raw[:-2].decode()
                    self.qp.put(text)


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
                        self.logger.debug(msg='Success')

    def session(self) -> bool:
        success: bool = False
        with self.locker:
            content: str = json.dumps(self.feedFIFO, indent=0)
            if self.upload(content=content):
                self.lastFeedAT = dt.now()
                self.feedFIFO.clear()
                success = True
        self.led.qp.put('typeA' if success else 'typeB')
        return success

    def run(self) -> None:

        while True:

            src = self.sq.get()
            with self.locker:
                if len(self.feedFIFO) == self.maxHolds:  # buffer full?
                    del (self.feedFIFO[0])
                    self.logger.critical(msg='feed buffer FULL (%d)' % self.maxHolds)
                self.feedFIFO.append(src.copy())  # notice! use copy
            if self.session():
                # self.logger.debug(msg='Success')
                pass


class GPSFeeder(object):

    def __init__(self, *, port: str, baudrate: int, account: str, url: str, dump: bool, cs: str):

        self.logger = getLogger('Log')

        self.dump = dump
        self.port = port
        self.baudrate = baudrate
        self.url = url
        self.account = account
        self.cs = suffix

        self.ready: bool = True
        self.loopCounter: int = 0
        self.sends: int = 0
        self.report: Dict[str, any] = {
            'counter': 0,
            'at': '',
            'status': True,
            'account': account,
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
            self.led = LEDController(pin=26)

            self.intervalSecs: int = 1

    def sendThis(self, *, status: bool = True):

        self.report['status'] = status
        self.report['counter'] = self.sends
        self.report['location'] = asdict(self.driver.location)
        self.report['at'] = self.driver.at
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

        self.logger.info(msg='Start on %s:%d %s@%s' % (self.port, self.baudrate, self.account, self.url))

        lastCounter: int = 0
        timing: int = 1
        lastTiming: int = 1
        isGPS: bool = False

        self.receiver.start()
        self.driver.start()
        self.sender.start()
        self.led.start()

        # time.sleep(self.intervalSecs)

        # self.sendThis()

        while True:

            try:
                measuredCunter = self.driver.counter
                if measuredCunter != lastCounter:  # changed
                    self.led.qp.put('typeA')
                    isGPS = True
                    if (self.loopCounter % timing) == 0:
                        self.sendThis()
                    else:
                        pass
                    timing = self.calcTiming(kmh=int(self.driver.location.plus.kmh))
                    if timing != lastTiming:
                        self.logger.debug('timing was shifted %d -> %d' % (lastTiming, timing))
                        lastTiming = timing
                    else:
                        pass
                    lastCounter = measuredCunter
                else:
                    self.led.qp.put('typeB')
                    if isGPS:
                        isGPS = False
                        timing = 1
                        lastTiming = 1
                        # self.sendThis(status=False)
                        self.logger.debug(msg='GPS lost')
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

    account: str = 'sekitakovich'
    # url: str = 'http://127.0.0.1:8080/post'
    url: str = 'http://192.168.3.6/post'
    # port: str = '/dev/ttyACM0'
    port: str = '/dev/ttyUSB0'
    baudrate: int = 9600
    suffix: str = 'RMC'

    parser = argparse.ArgumentParser(description='GPS autofeeder')
    parser.add_argument('-p', '--port', help='port name for sensor service (%s)' % port, type=str, default=port)
    parser.add_argument('-b', '--baudrate', help='baudrate for sensor service (%d)' % baudrate, type=int,
                        default=baudrate)
    parser.add_argument('-u', '--url', help='url for locationserver (%s)' % url, type=str, default=url)
    parser.add_argument('-a', '--account', help='account for locationserver (%s)' % account, type=str, default=account)
    parser.add_argument('-s', '--suffix', help='suffix of cycle period (%s)' % suffix, type=str, default=suffix)
    parser.add_argument('-d', '--dump', help='dump sentence realtime', action='store_true')
    parser.add_argument('-v', '--version', help='print version', action='version', version=version)

    args = parser.parse_args()

    LogConfigure(file='logs/client.log')

    feeder = GPSFeeder(port=args.port, baudrate=args.baudrate,
                       account=args.account, url=args.url, dump=args.dump, cs=args.suffix)

    if feeder.ready:
        feeder.mainLoop()
