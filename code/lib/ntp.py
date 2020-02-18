""" Synchronizes with NTP server.
"""

import socket
import struct

# setup logging
import logging
log = logging.getLogger(__name__)

# check micropython
import sys
MICROPYTHON = True if sys.implementation.name == 'micropython' else False
if MICROPYTHON:
    import machine


# NTP reports seconds since 1900-01-01!
# time.localtime requires secons since 1970-01-01! => 70 years off (+ 17 leap days)
NTP_DELTA = 2208988800   # 70years + 17 leap years: (70*365 + 17)*24*60*60


host = "de.pool.ntp.org"  # or "pool.ntp.org"


def ntptime():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1b
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    res = s.sendto(NTP_QUERY, addr)
    try:
        msg = s.recv(48)
    except TimeoutError as exc:
        log.error(host+" timed out! NTP sync failed.")
        s.close()
        return 0
    s.close()
    secs = struct.unpack("!I", msg[40:44])[0]
    return secs - NTP_DELTA


# There's currently no timezone support in MicroPython, so
# utime.localtime() will return UTC time (as if it was .gmtime())
def settime( timezone = 1 ):
    t = ntptime()
    import time
    tm = time.localtime(t)   # tm = (year, month, mday, hour, minute, second, weekday, yearday)
    tm = tm[0:6] + (0, timezone)
    if MICROPYTHON:
        machine.RTC().init(tm)

