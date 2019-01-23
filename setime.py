from datetime import datetime as dt
import ctypes.util
import time

time_tuple = (2019,  # Year
              9,  # Month
              6,  # Day
              0,  # Hour
              38,  # Minute
              0,  # Second
              0,  # Millisecond
              )


class timespec(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long), ("tv_nsec", ctypes.c_long)]


def _linux_set_time(time_tuple):

    # /usr/include/linux/time.h:
    #
    # define CLOCK_REALTIME                     0
    CLOCK_REALTIME = 0

    # /usr/include/time.h
    #
    # struct timespec
    #  {
    #    __time_t tv_sec;            /* Seconds.  */
    #    long int tv_nsec;           /* Nanoseconds.  */
    #  };
    librt = ctypes.CDLL(ctypes.util.find_library("rt"))

    ts = timespec()
    ts.tv_sec = int(time.mktime(dt(*time_tuple[:6]).timetuple()))
    ts.tv_nsec = time_tuple[6] * 1000000  # Millisecond to nanosecond

    # http://linux.die.net/man/3/clock_settime
    librt.clock_settime(CLOCK_REALTIME, ctypes.byref(ts))


if __name__ == '__main__':

    _linux_set_time(time_tuple)
