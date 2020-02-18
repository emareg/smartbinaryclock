# boot.py -- run on boot-up
print('===============( /boot.py )===============')

# imports
import time
import machine
import sys
import ubinascii



# constants
MAINFILE    = 'main.py'    # runs after boot.py
SAFETY_TIME = 3            # in seconds
VERBOSE     = True         # Show output


# probe PySense Extension
def probe_pysense():
	try:
		i2c = machine.I2C(0, mode=machine.I2C.MASTER, pins=('P22', 'P21'))
		resp = i2c.readfrom_mem(30, 0x0F, 1) # check accel, should be 0x41
	except OSError:
		return False
	return resp[0] == 0x41



# wait for button press
def wait_button():
	t_safety = SAFETY_TIME
	# Determine Button
	# Exp Board: G17=P10, Pysense: G4=P14
	if probe_pysense():
		print('Found Pysense Extension.')
		button = machine.Pin("G4", machine.Pin.IN, machine.Pin.PULL_UP)
	else:	
		button = machine.Pin("G17", machine.Pin.IN, machine.Pin.PULL_UP)

	print('waiting {}s for button press...'.format(t_safety), end=' ')

	while t_safety > 0:
		time.sleep(0.1)
		t_safety -= 0.1
		if button() == 0:
			print('PRESSED\nreturn to console.')
			machine.main('none.py')
			sys.exit(0)
	else:
		print("DONE")


def show_info():
	print("ID:   {}".format(ubinascii.hexlify(machine.unique_id())))
	print("MAIN: {}".format(MAINFILE))
	print("Freq: {}".format(machine.freq()))
	# print("DEV:  {}".format(machine.info()))


# ===============================================

if SAFETY_TIME > 0:
	wait_button()

if VERBOSE:
	show_info()


# duplicate console output on UART
# import os
# from machine import UART
# uart = UART(0, 115200)
# os.dupterm(uart)

machine.main(MAINFILE)
#print('Boot finished. Jumping to {}.'.format(MAINFILE))

