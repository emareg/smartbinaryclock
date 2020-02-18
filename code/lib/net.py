

import sys
if sys.implementation.name == 'micropython':
    MICROPYTHON = True
    import machine
    import network
else:
    MICROPYTHON = False

import time

# global wlan
wlan = None


def connect_wlan():
    if not MICROPYTHON: return
    global wlan

    # setup as a station (client)
    wlan = network.WLAN(mode=network.WLAN.STA)
    print('Connecting to Private WLAN... ', end='')
    wlan.connect('WLAN SSID', auth=(network.WLAN.WPA2, 'YOUR PASSWORD'))

    timeout_ms = 10000
    wait_ms = 50
    while not wlan.isconnected():
        time.sleep_ms(wait_ms)
        timeout_ms -= wait_ms
        if timeout_ms <= 0:
            print('Timed out!')
            return False

    print('Success!\nipconfig = {}\n'.format(wlan.ifconfig()))
    return True


def ifconfig():
    if MICROPYTHON:
        return wlan.ifconfig()

