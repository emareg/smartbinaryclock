## collection of useful date-time commands


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


def fmt24hformat(time):
    return "{:02d}:{:02d}:{:02d}".format(time[0], time[1], time[2])

def fmtISOdatetime(datetime):
    if len(datetime) > 3:
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(datetime[0], datetime[1], datetime[2], datetime[3], datetime[4], datetime[5])
    else:
        return "{:02d}:{:02d}:{:02d}".format(datetime[0], datetime[1], datetime[2])

