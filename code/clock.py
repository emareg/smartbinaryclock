

import sys
if sys.implementation.name == 'micropython':
    MICROPYTHON = True
    from machine import RTC
    from machine import Timer
    import time
    import ntp


def echo_handler(clock):
    print("time: ", to24hformat(clock.time() ) )


# -1 is a placeholder for indexing purposes.
_DAYS_IN_MONTH = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def days_before_year(year):
    "year -> number of days before January 1st of year."
    y = year - 1
    return y*365 + y//4 - y//100 + y//400

def is_leapyear(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def days_in_month(year, month): 
    assert 1 <= month <= 12, 'month must be in 1..12'
    if month == 2 and is_leapyear(year): return 29
    return _DAYS_IN_MONTH[month]

def days_before_month(year, month):
    assert 1 <= month <= 12, 'month must be in 1..12'
    return sum(_DAYS_IN_MONTH[1:month]) + (month > 2 and is_leapyear(year))


def ymd2ord(year, month, day):
    assert 1 <= month <= 12, 'month must be in 1..12'
    dim = days_in_month(year, month)
    assert 1 <= day <= dim, ('day must be in 1..%d' % dim)
    return (days_before_year(year) +
            days_before_month(year, month) +
            day)

def weekday(date):
    assert len(date) > 3, 'not a valid date'
    return (ymd2ord(date[0], date[1], date[2]) + 6) % 7



def summertime(datetime):
    month = datetime[1]
    day = datetime[2]
    wday = (weekday(datetime) + 1) % 7  # make sunday wday = 0
    hour = datetime[3]
    # summertime: March, after last Sunday 2:00 and before oktober, last sunday
    # https://www.mikrocontroller.net/attachment/8391/TIME.C

    if month < 3 or month > 10: return 0
    if 3 < month < 10: return 1
    if( day - wday >= 25 and (wday > 0 or hour >= 2)):  # after last suday 2:00?
        return month == 3  # after sunday in march => summertime
    else:
        return month == 10 # before sunday in okt. => still summertime
 




# ===========================================================
class Clock:

    def __init__(self):
        self.rtc = RTC()
        self.heartbeat_handler = None
        self.alarm = None
        self.inteval = 0
        self.timezone = 1
        self.summertime = 1
        self.rtcdate = (2018, 8, 1)
        self.auto_sync = False

    def register_heartbeat_handler(self, handler, inteval=1.0):
        self.heartbeat_handler = handler
        self.inteval = inteval

    def start_heartbeat(self):
        if self.heartbeat_handler:
            self.alarm = Timer.Alarm(self._alarm_callback, self.inteval, periodic=True)

    def stop_heartbeat(self):
        if self.alarm != None:
            self.alarm.cancel()

    def _alarm_callback(self, alarm):
        self.heartbeat_handler(alarm)


    def date(self):
        self.rtcdate = self.rtc.now()[0:3]
        return self.rtcdate


    def time(self):
        """ returns seconds since 1970-1-1 0:00 """
        # return time.mktime( localtime() )
        return time.time()


    def localtime(self):
        """ returns localtime struct """
        return self.rtc.now()[3:6]
        rtctime = list(self.rtc.now()[3:6])
        rtctime[0] += (self.timezone + self.summertime)
        return tuple(rtctime)


    def datetime(self):
        return self.rtc.now()


    def is_summertime(self):
        return self.summertime


    def enable_auto_sync(self, period_s=3600):
        self.rtc.ntp_sync("pool.ntp.org", period_s)

    def disable_auto_sync(self):
        self.rtc.ntp_sync(None)


    def sync(self):
        secs = ntp.ntptime()
        gmtime = time.localtime(secs)
        gmtime = gmtime[0:6] + (0, self.timezone)
        # check summer time
        date = gmtime[0:3]
        self.summertime = summertime( gmtime )
        hour = gmtime[3] + self.timezone + self.summertime
        ltime = gmtime[0:3] + (hour, ) + gmtime[4:6] + (0, 0)

        self.rtc.init(ltime)
        print("Clock: gmtime: ", gmtime)
        print("Clock: localtime: ", ltime)    


    def synced(self):
        if self.rtc.synced():
            return True
        else:
            # todo: check manual sync
            return False


def to24hformat(time):
    return "{:02d}:{:02d}:{:02d}".format(time[0], time[1], time[2])




print(summertime([2019, 10, 27, 11, 38, 00]))
