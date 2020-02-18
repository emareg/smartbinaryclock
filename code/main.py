# main.py -- put your code here!
# Libs: https://github.com/pycom/pycom-libraries


print('\n===============( /main.py )===============')

import sys
if sys.implementation.name == 'micropython':
    MICROPYTHON = True 
else:
    sys.path.append('dummy')
    sys.path.append('lib')
    MICROPYTHON = False


import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


from app_binaryclock import BinaryClockApp

# mount SD card
# from machine import SD
# import os
# sd = SD()
# os.mount(sd, '/sd')
# logfile = open('/sd/crash.log', 'w')


print("starting application:")
bca = BinaryClockApp()

bca.start()



# LED test
# from display import LedDisplay, ColorRGB
# print('starting Display Test')
# display = LedDisplay()
# display.test()







