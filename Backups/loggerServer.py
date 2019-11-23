import json
import os
import socket
import socketserver
import sqlite3
import time
from datetime import datetime as dt
from queue import Empty
from queue import Queue
from threading import Event
from threading import Lock
from threading import Thread
import argparse
import serial


class Common(object):

    class Daily(object):

        log = []
        tsFormat = '%Y-%m-%d %H:%M:%S.%f'
        ymdFormat = '%Y-%m-%d'
        hmsFormat = '%H:%M:%S.%f'

    class SQlite3(object):
        quePoint = Queue()

    class Cloud(object):
        port = 12345
        welcome = Event()

    class Serial(object):

        port = '/dev/ttyACM0'
        baud = 9600
        quePoint = Queue()

    class News(object):

        event = Event()
        lock = Lock()
        quePoint = {}

        # info = {
        #     'id': None,
        #     'ymd': None,
        #     'hms': None,
        #     'nmea': None,
        # }
        #
        @classmethod
        def appendClient(cls, *, port=None):
            with cls.lock:
                cls.quePoint[port] = Queue()

        @classmethod
        def removeClient(cls, *, port=None):
            with cls.lock:
                del (cls.quePoint[port])

        @classmethod
        def put(cls, *, info=None):
            # info = {
            #     'id': id,
            #     'ymd': ymd,
            #     'hms': hms,
            #     'nmea': nmea,
            # }
            #
            with cls.lock:
                for k, v in cls.quePoint.items():
                    v.put(info)

            return

    @classmethod
    def checkSum(cls, body=b''):
        cs = 0
        for v in body:
            cs ^= v
        return cs


class DBThread(Thread):
    def __init__(self, *, commitInterval=0):

        super().__init__()
        self.setDaemon(True)

        self.ymd = dt.utcnow().strftime(Common.Daily.ymdFormat)
        self.counter = 0

        self.commitInterval = commitInterval
        self.db = None
        self.cursor = None

    def run(self):

        print('%s: start' % (self.__class__.__name__,))

        def start():
            file = self.ymd + '.db'
            self.db = sqlite3.connect(file)
            self.cursor = self.db.cursor()
            self.counter = 0

        start()

        while True:
            try:
                src = Common.SQlite3.quePoint.get(timeout=5.0)
            except Empty as e:
                self.db.commit()
                print('%s: timeout (%s)' % (self.__class__.__name__, e,))
                pass
            else:

                id = src['id']
                nmea = src['nmea']
                ymd = src['ymd']
                hms = src['hms']

                if ymd != self.ymd:
                    self.db.commit()
                    self.ymd = ymd
                    start()

                query = 'insert into sentence(id,ymd,hms,nmea) values(?,?,?,?)'
                self.cursor.execute(query, (id, ymd, hms, nmea))
                self.counter += 1

                if self.commitInterval == 0:
                    self.db.commit()

                elif (self.counter % self.commitInterval) == 0:
                    self.db.commit()

        pass


class RoutineHandler(socketserver.BaseRequestHandler):

    def setup(self):

        Common.Cloud.welcome.set()
        # if Common.DBSession.db:
        #     Common.DBSession.commit()

        self.address = self.client_address[0]
        self.port = self.client_address[1]

        Common.News.appendClient(port=self.port)

        # got = self.request.recv(80)
        # name = got.decode()
        print('%s: connect from client address = %s port = %s from %d' % (
        self.__class__.__name__, self.address, self.port, Common.Daily.counter))
        pass

    def finish(self):
        # del(Common.News.quePoint[self.port])
        Common.News.removeClient(port=self.port)
        print('%s: client %d was removed' % (self.__class__.__name__, self.port,))
        pass

    def handle(self):

        client = self.request

        startUp = {
            'mode': 'init',
            'ymd': Common.Daily.ymd,
            'id': Common.Daily.counter,
        }
        ooo = json.dumps(startUp) + '\n'
        client.send(ooo.encode())

        while True:

            # Common.News.event.wait()
            # Common.News.event.clear()
            # info = Common.News.get()

            info = Common.News.quePoint[self.port].get()

            ooo = json.dumps(info) + '\n'  # Notice!
            try:
                client.send(ooo.encode())
            except socket.error as e:
                print('%s: %s' % (self.__class__.__name__, e))
                break
            else:
                pass


class RoutineServer(socketserver.ThreadingTCPServer):

    def __init__(self, host='', port=0):
        super().__init__((host, port), RoutineHandler)

    def server_bind(self):
        self.timeout = 0
        self.allow_reuse_address = True

        # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while True:
            try:
                self.socket.bind(self.server_address)
            except socket.error as e:
                print('%s: %s' % (self.__class__.__name__, e))
                time.sleep(1)
                pass
            else:
                break


class Sender(Thread):
    def __init__(self):
        super().__init__()
        self.setDaemon(True)

        self.server = RoutineServer(host='', port=12345)

    def run(self):
        print('%s: start' % (self.__class__.__name__,))
        self.server.serve_forever()


class Receiver(Thread):

    def __init__(self, *, port=Common.Serial.port, baud=Common.Serial.baud):

        super().__init__()

        self.setDaemon(True)
        self.port = serial.Serial(port, baudrate=baud, timeout=1)

    def run(self):
        print('%s: start' % (self.__class__.__name__,))

        while True:
            raw = self.port.readline(1024)
            if len(raw) > 6:
                if chr(raw[0]) in ('$', '!'):
                    nmea = raw.decode()[:-2]
                    part = nmea.split('*')
                    if len(part) == 2:
                        cs = int(part[1][:2], 16)
                        body = part[0][1:]
                        if cs == Common.checkSum(body=body.encode()):
                            Common.Serial.quePoint.put(nmea)
                        else:
                            print('%s: checksum not match' % (self.__class__.__name__,))
                            pass
                    else:
                        print('%s: checksum not found' % (self.__class__.__name__,))
                        pass
                else:
                    print('%s: sentence is invalid' % (self.__class__.__name__,))
                    pass
            else:
                print('%s: sentence is too short' % (self.__class__.__name__,))
                pass


class Main(object):

    def __init__(self, *, port=Common.Serial.port, baud=Common.Serial.baud):

        self.ymd = dt.utcnow().strftime(Common.Daily.ymdFormat)
        self.hms = dt.utcnow().strftime(Common.Daily.hmsFormat)
        self.counter = 0

        '''
        prepare section
        '''
        file = self.ymd + '.db'
        exists = os.path.exists(file)
        db = sqlite3.connect(file)
        cursor = db.cursor()
        if exists:
            query = "select max(id) from sentence"
            cursor.execute(query)
            ooo = cursor.fetchone()
            self.counter = int(ooo[0])
            print('%s: session was restarted from %d' % (self.__class__.__name__, self.counter,))
            pass
        else:
            query = "CREATE TABLE 'sentence' ( `id` INTEGER NOT NULL DEFAULT 0 PRIMARY KEY, `ymd` TEXT NOT NULL DEFAULT '', `hms` TEXT NOT NULL DEFAULT '',`nmea` TEXT NOT NULL DEFAULT '' )"
            cursor.execute(query)
            db.commit()
            pass

        db.close()
        '''
        prepare section
        '''

        self.ds = DBThread(commitInterval=0)
        self.ds.start()

        self.receiver = Receiver(port=port, baud=baud)
        self.receiver.start()

        self.sender = Sender()
        self.sender.start()

    def loop(self):

        while True:

            try:
                nmea = Common.Serial.quePoint.get()
            except KeyboardInterrupt as e:
                print('%s: %s' % (self.__class__.__name__, e))
                break
            else:
                now = dt.utcnow()

                ymd = now.strftime(Common.Daily.ymdFormat)
                self.hms = now.strftime(Common.Daily.hmsFormat)

                if ymd != self.ymd:
                    self.ymd = ymd
                    self.counter = 0

                self.counter += 1
                Common.Daily.ymd = ymd
                Common.Daily.counter = self.counter

                info = {
                    'mode': 'info',
                    'id': self.counter,
                    'ymd': self.ymd,
                    'hms': self.hms,
                    'nmea': nmea,
                }
                Common.News.put(info=info)
                Common.SQlite3.quePoint.put(info)
                Common.Daily.log.append(info)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='AIS logger',
        add_help=True,
    )

    parser.add_argument('--port', help='name of serial port', default=Common.Serial.port, type=str)
    parser.add_argument('--baud', help='baud rate', default=Common.Serial.baud, type=int)
    args = parser.parse_args()

    main = Main(port=args.port, baud=args.baud)

    main.loop()
