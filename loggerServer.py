from datetime import datetime as dt
from threading import Thread
from threading import Event
from threading import Lock
import serial
from queue import Queue
import socketserver
import socket
import json


class Common(object):

    class DateTime(object):
        tsFormat = '%Y-%m-%d %H:%M:%S.%f'
        ymdFormat = '%Y-%m-%d'
        hmsFormat = '%H:%M:%S.%f'

    class Cloud(object):
        port = 12345

    class Serial(object):

        device = '/dev/ttyACM0'
        baudrate = 9600
        quePoint = Queue()

    class News(object):

        event = Event()
        lock = Lock()
        quePoint = {}

        info = {
            'id': None,
            'ymd': None,
            'hms': None,
            'nmea': None,
        }

        @classmethod
        def appendClient(cls, *, port=None):
            with cls.lock:
                cls.quePoint[port] = Queue()

        @classmethod
        def removeClient(cls, *, port=None):
            with cls.lock:
                del(cls.quePoint[port])

        @classmethod
        def put(cls, *, id=None, ymd=None, hms=None, nmea=None):

            info = {
                'id': id,
                'ymd': ymd,
                'hms': hms,
                'nmea': nmea,
            }

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


class SampleHandler(socketserver.BaseRequestHandler):

    def setup(self):

        self.address = self.client_address[0]
        self.port = self.client_address[1]

        Common.News.appendClient(port=self.port)

        # got = self.request.recv(80)
        # name = got.decode()
        print('%s: connect from client address = %s port = %s' % (self.__class__.__name__, self.address, self.port))
        pass

    def finish(self):
        # del(Common.News.quePoint[self.port])
        Common.News.removeClient(port=self.port)
        print('%s: client %d was removed' % (self.__class__.__name__, self.port,))
        pass

    def handle(self):

        client = self.request

        while True:

            # Common.News.event.wait()
            # Common.News.event.clear()
            # info = Common.News.get()

            info = Common.News.quePoint[self.port].get()

            ooo = json.dumps(info)
            try:
                client.send(ooo.encode())
            except socket.error as e:
                print('%s: %s' % (self.__class__.__name__, e))
                break
            else:
                pass


class SampleServer(socketserver.ThreadingTCPServer):

    def __init__(self, host='', port=0):
        super().__init__((host, port), SampleHandler)

    def server_bind(self):

        self.timeout = 0
        self.allow_reuse_address = True

        # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


class Sender(Thread):
    def __init__(self):

        super().__init__()
        self.setDaemon(True)

        self.server = SampleServer(host='', port=12345)

    def run(self):
        self.server.serve_forever()


class Receiver(Thread):

    def __init__(self, device=Common.Serial.device, baudrate=Common.Serial.baudrate):

        super().__init__()

        self.setDaemon(True)
        self.port = serial.Serial(device, baudrate=baudrate, timeout=1)

    def run(self):

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

    def __init__(self):

        self.counter = 0
        self.ymd = dt.utcnow().strftime(Common.DateTime.ymdFormat)

        self.receiver = Receiver()
        self.receiver.start()

        self.sender = Sender()
        self.sender.start()

        print('%s: start' % (self.__class__.__name__,))

    def loop(self):

        while True:

            try:
                nmea = Common.Serial.quePoint.get()
            except KeyboardInterrupt as e:
                print('%s: %s' % (self.__class__.__name__, e))
                break
            else:
                now = dt.utcnow()
                ymd = now.strftime(Common.DateTime.ymdFormat)

                if ymd != self.ymd:
                    self.ymd = ymd
                    self.counter = 0

                self.counter += 1

                Common.News.put(
                    id=self.counter,
                    ymd=now.strftime(Common.DateTime.ymdFormat),
                    hms=now.strftime(Common.DateTime.hmsFormat),
                    nmea=nmea)

                # self.counter += 1


if __name__ == '__main__':

    main = Main()

    main.loop()
