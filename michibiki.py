import sys
import serial
from threading import Thread
from queue import Queue
from common import Common


class Process(Thread):
    def __init__(self, quePoint=None):
        super().__init__()
        self.setDaemon(True)
        self.q = quePoint
        pass

    def run(self):
        while True:
            raw = self.q.get()
            self.chop(raw=raw)
        pass

    # def dm2deg(self, *, dm=None):  # GPGGA -> GoogleMaps
    #     decimal, integer = math.modf(dm / 100.0)
    #     value = integer + ((decimal / 60.0) * 100.0)
    #     return value
    #
    # def checkSum(self, *, body=b''):
    #     cs = 0
    #     for v in body:
    #         cs ^= v
    #     return cs
    #
    def chop(self, raw=b''):
        try:
            src = raw.decode()
        except UnicodeDecodeError as e:
            print(e)
            pass
        else:

            if len(src) > 82:
                pass
            if len(src) <= 4:  # $*CS
                pass
            elif src[0] not in ('$', '!'):
                pass
            else:
                part = src.split('*')
                if len(part) != 2:
                    pass
                else:
                    # print(part)
                    try:
                        cs = int(part[1][:2], 16)
                        pass
                    except ValueError as e:
                        print(e)
                        pass
                    else:
                        body = part[0][1:]
                        if cs == Common.checkSum(body=body.encode()):
                            item = body.split(',')
                            symbol = item[0]
                            if symbol == 'GPRMC':
                                ooo = item[1].split('.')
                                t = '%s:%s:%s.%s' % (ooo[0][:2], ooo[0][2:4], ooo[0][4:6], ooo[1])
                                lat = Common.dm2deg(dm=float(item[3]))
                                ns = item[4]
                                lon = Common.dm2deg(dm=float(item[5]))
                                ew = item[6]
                                sog = float(item[7])
                                cog = float(item[8])
                                d = '20%s-%s-%s' % (item[9][:2], item[9][2:4], item[9][4:6])
                                mode = item[12]
                                print('+++ %s %f%s:%f%s S:%.2f C:%.2f on %s at %s %s' % (
                                    symbol, lat, ns, lon, ew, sog, cog, mode, d, t))
                                pass
                            elif symbol == 'GPGGA':
                                ooo = item[1].split('.')
                                t = '%s:%s:%s.%s' % (ooo[0][:2], ooo[0][2:4], ooo[0][4:6], ooo[1])
                                lat = Common.dm2deg(dm=float(item[2]))
                                ns = item[3]
                                lon = Common.dm2deg(dm=float(item[4]))
                                ew = item[5]
                                mode = item[6]
                                ss = int(item[7])
                                print('+++ %s %f%s:%f%s on %s (%d) ' % (
                                    symbol, lat, ns, lon, ew, mode, ss))
                                pass
                            else:
                                pass

                        else:
                            print('Checksum Error')
                        pass


def main():

    q = Queue()

    proccessor = Process(quePoint=q)
    proccessor.start()

    device = '/dev/serial0'
    baudrate = 38400

    port = serial.Serial(device, baudrate=baudrate, timeout=1)

    while True:

        try:
            raw = port.readline(1024)
            pass
        except KeyboardInterrupt:
            sys.exit(0)
            pass
        except ValueError as e:
            print(e)
            pass
        else:
            q.put(raw)


if __name__ == '__main__':
    main()
