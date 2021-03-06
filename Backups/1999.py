import sys
import serial
from threading import (Thread)
from queue import Queue
import sqlite3
from datetime import datetime as dt

from Backups.common import Common


class Process(Thread):
    def __init__(self, quePoint=None):

        super(Process, self).__init__()

        self.setDaemon(True)
        self.q = quePoint
        self.seqnum = 1

        pass

    def run(self):
        while True:
            raw = self.q.get()
            self.chop(raw=raw)
        pass

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
                            if symbol == 'GPRMC' and len(item) >= 12:
                                if item[2] == 'A':

                                    try:
                                        ooo = item[1].split('.')
                                        t = '%s:%s:%s.%s' % (ooo[0][:2], ooo[0][2:4], ooo[0][4:6], ooo[1])
                                        lat = Common.dm2deg(dm=float(item[3])) if item[3] else 0
                                        ns = item[4]
                                        lon = Common.dm2deg(dm=float(item[5])) if item[5] else 0
                                        ew = item[6]
                                        sog = float(item[7]) if item[7] else 0
                                        cog = float(item[8]) if item[8] else 0
                                        d = '20%s-%s-%s' % (item[9][:2], item[9][2:4], item[9][4:6])
                                        mode = item[12]

                                        hhmmssff = item[1]
                                        ddmmyy = item[9]

                                        pass
                                    except ValueError as e:
                                        print(e)
                                        pass
                                    else:
                                        # tt = (
                                        #     int(ddmmyy[4:6]) + 2000,
                                        #     int(ddmmyy[2:4]),
                                        #     int(ddmmyy[0:2]),
                                        #     int(hhmmssff[0:2]),
                                        #     int(hhmmssff[2:4]),
                                        #     int(hhmmssff[4:6]),
                                        #     int(hhmmssff[7:9]),
                                        # )
                                        # print('RMC: tt = %s' % (tt,))
                                        print('+++ %s %f%s:%f%s S:%.2f C:%.2f on %s at %s %s' % (
                                         symbol, lat, ns, lon, ew, sog, cog, mode, d, t))
                                        # header = Common.format450(sfi='1234', seqnum=self.seqnum)
                                        # self.seqnum += 1
                                        # if self.seqnum == 1000:
                                        #     self.seqnum = 1
                                        # print(header + raw)

                                        info = {
                                            'at': str(dt.utcnow().timestamp()),
                                            'nmea': raw.decode()[:-2],
                                        }
                                        Common.News.send(info=info)
                                        # print(json.dumps(ooo))
                                    pass
                                else:
                                    print('RMC: invalid')
                                    pass
                            # elif symbol == 'GPGGA':
                            #     ooo = item[1].split('.')
                            #     t = '%s:%s:%s.%s' % (ooo[0][:2], ooo[0][2:4], ooo[0][4:6], ooo[1])
                            #     lat = Common.dm2deg(dm=float(item[2]))
                            #     ns = item[3]
                            #     lon = Common.dm2deg(dm=float(item[4]))
                            #     ew = item[5]
                            #     mode = item[6]
                            #     ss = int(item[7])
                            #     print('+++ %s %f%s:%f%s on %s (%d) ' % (
                            #         symbol, lat, ns, lon, ew, mode, ss))
                            #     pass
                            else:
                                pass

                        else:
                            print('Checksum Error')
                        pass


def main():

    q = Queue()

    proccessor = Process(quePoint=q)
    proccessor.start()

    device = '/dev/ttyACM0'
    baudrate = 9600

    port = serial.Serial(device, baudrate=baudrate, timeout=1)

    query = "CREATE TABLE 'sentence' ( `id` INTEGER NOT NULL DEFAULT 0 PRIMARY KEY AUTOINCREMENT, `at` TEXT NOT NULL DEFAULT '', `nmea` TEXT NOT NULL DEFAULT '' )"

    db = sqlite3.connect('logger.db')
    cursor = db.cursor()
    counter = 0

    while True:

        try:
            raw = port.readline(1024)
            pass
        except KeyboardInterrupt:
            db.commit()
            db.close()
            sys.exit(0)
            pass
        except ValueError as e:
            print(e)
            pass
        else:
            q.put(raw)
            nmea = raw.decode()[:-2]
            at = dt.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            query = 'insert into sentence(at,nmea) values(?,?)'
            cursor.execute(query, (at, nmea))
            counter += 1
            if (counter % 100) == 0:
                db.commit()

            # print('%s %s' % (at, nmea))

if __name__ == '__main__':
    main()
