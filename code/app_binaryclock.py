""" BinaryClock 0.6

Todo:
- Years Bug
- correct summer time
- Write exception to file
- Automatic brightness based on time

Done:
- Startime
- WebIface with buttons

"""

import sys
if sys.implementation.name == 'micropython':
    MICROPYTHON = True 
else:
    sys.path.append('dummy')
    sys.path.append('lib')
    MICROPYTHON = False

# pycom modules
import pycom

# own modules
from display import LedDisplay, ColorRGB
from clock import Clock, echo_handler
from nano_srv import WebSrv

# own libraries
import ntp
import net
import time

import logging
log = logging.getLogger('root')
log.setLevel(logging.DEBUG)



STATE_TIME_MIN='minutes'
STATE_TIME_SEC='seconds'
STATE_TIME_UPTIME='uptime'
STATE_BOOTDATE='bootdate'
STATE_TEMPERATURE='temperature'
STATE_DATE='date'
STATE_OFF='off'
STATE_ON='on'

API_RE_COLORS=r'(?:time|date)colors=\[(?:\(\d+,\d+,\d+\),?){3}]'
API_RE_COLOR=r'(?:year|month|day|hour|minute|second)color=\(\d+,\d+,\d+\)'


HEADER_OK = 'HTTP/1.1 200 OK\r\nContent-Type: {}\r\n\r\n'

HTML = """<!DOCTYPE html>\n<html>
        <head><title>{title}</title> </head>
        <body><h1>{title}</h1>
        {content}
        </body>
</html>"""

HTML_START = HTML.format(title='BinaryClock Web interface', content='<ip')

HTML_OK = HTML.format(title='Ok', content='')
HTTP_404 = b'HTTP/1.1 404 Not Found\r\n\r\n'+bytes( HTML.format(title='Not Found', content='Your requested location is unknown.'), 'utf-8' )


# colors
CYAN=ColorRGB(0,128,128)
YELLOW=ColorRGB(128,128,0)
MAGENTA=ColorRGB(128,0,128)
GREEN=ColorRGB(0,128,0)
BLUE=ColorRGB(0,0,128)


# tum colors
TUM_BLUE=ColorRGB(0, 99, 189)   # (0, 101, 189)
TUM_TEAL=ColorRGB(0, 119, 138)   # (0, 119, 138)
TUM_FOREST=ColorRGB(0, 151,  51)  # (0, 124,  48)


# error states
ERROR_WIFI_TIMEOUT=15


class EventLog:
    def __init__(self, length):
        self.log = []
        self.maxlength = length

    def push(self, msg):
        datetime = time.localtime()
        self.log.insert(0, toISOdatetime(datetime)+": "+msg)
        if len(self.log) > self.maxlength: del self.log[-1]

    def get(self):
        return self.log




class BinaryClockApp:
    def __init__(self):
        self.display = None
        self.clock = None
        self.websrv = None

        self.state = STATE_TIME_MIN
        self.laststate = STATE_TIME_MIN
        self.error = None
        self.errorcnt = 0 # error count
        self.bootdatetime = None
        self.autobright = False

        # colors
        self.timecolors=(TUM_BLUE, TUM_FOREST, TUM_TEAL)
        self.datecolors=(ColorRGB(0,128,0), ColorRGB(0,0,128))
        self.ipcolor=ColorRGB(64,0,0)
        self.errorcolor=ColorRGB(64,32,0)

        self.html = ""
        self.API = {
            STATE_ON: self.on,
            STATE_OFF: self.off,
            STATE_TIME_SEC: self.show_time,
            STATE_TIME_MIN: self.show_time_min,
            STATE_DATE: self.show_date,
            STATE_BOOTDATE: self.show_bootdate,
            'fullbright': self.fullbright,
            'bright': self.bright,
            'dimm': self.dimm,
        }
        self.log = EventLog(10)




    def update_display(self, alarm = None):
        try:
            # estimate display brighness based on time
            # curtime = self.clock.localtime()
            # curdate = self.clock.date()
            # darkfactor = abs(curdate[1] - 6)/2
            # if curtime[0] <= 5 or 22 <= curtime[0]-darkfactor:
            #     if curtime[1] == 0 and curtime[2] == 0:
            #         self.dimm()

            # write info to disply
            if self.state == STATE_TIME_SEC:
                curtime = self.clock.localtime()
                self.display.set_row( 0, curtime[0], self.timecolors[0] )
                self.display.set_row( 1, curtime[2], self.timecolors[2] )
                #a = 1/0
                #self.display.show( curtime, self.timecolors)


            elif self.state == STATE_TIME_MIN:
                curtime = self.clock.localtime()
                self.display.set_row( 0, curtime[0], self.timecolors[0] )
                self.display.set_row( 1, curtime[1], self.timecolors[1] )


            elif self.state == STATE_DATE:
                curdate = list(self.clock.date())
                curdate[0] = curdate[0] % 100 # year in 100s
                curdate = tuple(curdate[1:])
                self.display.set_rows( curdate, self.datecolors)

            elif self.state == STATE_TEMPERATURE:
                pass  # todo

            elif self.state == STATE_OFF:
                self.display.clear()

            # show
            self.display.show()

            print("time: ", to24hformat(self.clock.localtime() ) )

        # any error
        except Exception as e:
            timestr = toISOdatetime( list(self.clock.date()) + list(self.clock.localtime()) )
            print("== going to log exception:")
            logfile = open('crash.log', 'w')
            logfile.write(timestr+":\n")
            if hasattr(sys, 'print_exception'): sys.print_exception(e, logfile)
            logfile.close()
            print("== file closed")


            # try to display error
            self.display.set_row( 0, 15, ColorRGB(101,0,0))
            self.errorcnt += 1
            self.display.set_row( 1, self.errorcnt, ColorRGB(101,0,0))
            self.display.show()
            print("== updated display")
            sys.exit(0)




    def web_handler(self, path):
        path = path.decode("utf-8") 
        print("webif: requested '{}'".format(path))
        reply = HTTP_404
        if path == '/':
            reply = bytes( HEADER_OK.format('text/html') + self.html_with_log(), 'utf-8' )
        elif path[1:] in list(self.API.keys()):
            self.API[path[1:]]() # call API
            self.log.push("API call "+path)
            reply = bytes( HEADER_OK.format('text/html') + self.html_with_log(), 'utf-8' )
        else:
            self.log.push("invalid request: "+path)
        return reply




    # API functions
    def show_time(self):     self.state = STATE_TIME_SEC
    def show_time_min(self): self.state = STATE_TIME_MIN
    def show_date(self):     self.state = STATE_DATE
    def show_bootdate(self): self.state = STATE_BOOTDATE

    def off(self):  self.laststate = self.state; self.state = STATE_OFF
    def on(self):   self.state = self.laststate

    def autobright(self): self.autobright = True
    def dimm(self):       self.autobright = False; self.display.set_brightness(0.02)
    def bright(self):     self.autobright = False; self.display.set_brightness(0.08)  
    def fullbright(self): self.autobright = False; self.display.set_brightness(0.2)  




    def start_web_iface(self):
        ip = net.ifconfig()[0]

        ipbytes = ip.split('.')
        ipbytes = [int(x) for x in ipbytes]
        if ipbytes[3] > 100: ipbytes[3] -= 100

        # display ip
        self.display.set_row( 0, ipbytes[2], self.ipcolor )
        self.display.set_row( 1, ipbytes[3], self.ipcolor )
        self.display.show()

        self.websrv = WebSrv( self.web_handler )
        self.websrv.start()

        # load html
        f = open('./html/index.html', 'r')
        self.html = f.read()
        f.close()

        time.sleep(2)



    def html_with_log(self):
        html_log = "<ul>\n"
        logs = self.log.get()
        for enry in logs:
            html_log += "<li>"+str(enry)+"</li>"
        html_log += "</ul>"
        html = self.html
        html = html.replace("{{ commandlog }}", html_log)
        html = html.replace("{{ utctime }}", str(self.clock.utctime()))
        html = html.replace("{{ localtime }}", str(self.clock.localtime()))
        html = html.replace("{{ timezone }}", str(self.clock.timezone))
        html = html.replace("{{ summertime }}", str(self.clock.summertime))
        html = html.replace("{{ rtcsynced }}", str(self.clock.synced()))
        return html




    def start(self):
        print("Welcome to BinaryClock!\nstarting...")

        log.debug('starting Display')
        self.display = LedDisplay()
        
        log.debug('starting Network')
        succ = net.connect_wlan()
        if not succ:
            time.sleep(3)
            succ = net.connect_wlan()
            if not succ:
                self.error = ERROR_WIFI_TIMEOUT
                self.update_display()
                return False

        log.debug('starting Web interface...')
        self.start_web_iface()

        log.debug('initialize Clock')
        self.clock = Clock()
        time.sleep(0.2)
        log.debug('synchronize clock')
        self.clock.sync()

        log.debug('starting Clock')
        self.clock.register_heartbeat_handler(self.update_display, 1.0)
        self.clock.start_heartbeat()
           
        time.sleep(1)
        log.debug('log bootdate')
        self.bootdatetime = time.localtime()
        self.html = self.html.replace("{{ boottime }}", toISOdatetime(self.bootdatetime))

        log.debug('disable heartbeat LED')
        pycom.heartbeat(False)



    def stop(self):
        log.debug("stopping clock")
        self.clock.stop_heartbeat()

    def resume(self):
        log.debug("resuming clock")
        self.clock.start_heartbeat()



def to24hformat(time):
    return "{:02d}:{:02d}:{:02d}".format(time[0], time[1], time[2])

def toISOdatetime(datetime):
    if len(datetime) > 3:
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(datetime[0], datetime[1], datetime[2], datetime[3], datetime[4], datetime[5])
    else:
        return "{:02d}:{:02d}:{:02d}".format(datetime[0], datetime[1], datetime[2])

