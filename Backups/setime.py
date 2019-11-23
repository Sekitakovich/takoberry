from datetime import datetime as dt
import ctypes.util
import time


class TimeSpec(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long), ("tv_nsec", ctypes.c_long)]


class SetSystemDateTime(object):
    def __init__(self):
        # /usr/include/time.h
        #
        # struct TimeSpec
        #  {
        #    __time_t tv_sec;            /* Seconds.  */
        #    long int tv_nsec;           /* Nanoseconds.  */
        #  };
        self.librt = ctypes.CDLL(ctypes.util.find_library("rt"))
        pass

    def linux_set_time(self, *, timeTuple=None):

        # /usr/include/linux/time.h:
        #
        # define CLOCK_REALTIME                     0
        CLOCK_REALTIME = 0

        ts = TimeSpec()
        ts.tv_sec = int(time.mktime(dt(*timeTuple[:6]).timetuple()))
        ts.tv_nsec = timeTuple[6] * 1000000  # Millisecond to nanosecond

        # http://linux.die.net/man/3/clock_settime
        self.librt.clock_settime(CLOCK_REALTIME, ctypes.byref(ts))


if __name__ == '__main__':

    at1999 = '240119 024733.00'
    tt = (
        int(at1999[4:6]) + 2000,
        int(at1999[2:4]),
        int(at1999[0:2]),
        int(at1999[7:9]),
        int(at1999[9:11]),
        int(at1999[11:13]),
        int(at1999[14:16]),
    )
    print(tt)

    timeTuple = tuple([int(c) for c in dt.now().strftime('%Y,%m,%d,%H,%M,%S,%f').split(',')])

    print(timeTuple)

    ooo = SetSystemDateTime()
    ooo.linux_set_time(timeTuple=timeTuple)

    print(dt.now())
