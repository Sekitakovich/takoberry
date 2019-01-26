import math
from threading import Event
from threading import Lock
from queue import Queue


class Common(object):

    class Serial(object):

        quePoint = Queue()

    class News(object):

        event = Event()
        info = None
        lockThis = Lock()

        @classmethod
        def send(cls, *, info=None):
            with cls.lockThis:
                cls.info = info
                cls.event.set()
                pass
            return


    @classmethod
    def dm2deg(cls, dm=None):  # GPGGA -> GoogleMaps
        decimal, integer = math.modf(dm / 100.0)
        value = integer + ((decimal / 60.0) * 100.0)
        return value

    @classmethod
    def checkSum(cls, body=b''):
        cs = 0
        for v in body:
            cs ^= v
        return cs

    @classmethod
    def format450(cls, *, sfi=None, seqnum=None):

        header = b'UdPbc\x00'
        params = ','.join([
            's:VD' + sfi,  # SFI
            'n:' + str(seqnum),  # sequence(1-999
        ]).encode()

        cs = ('*%02X' % cls.checkSum(body=params)).encode()

        return header + b'\x5c' + params + b'\x5c' + cs

