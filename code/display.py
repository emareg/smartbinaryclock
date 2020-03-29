# binary clock display module

from lib.ws2801 import WS2801
import time

class ColorRGB:
    def __init__(self, r, g, b):
        self.red = r & 0xFF
        self.green = g & 0xFF
        self.blue = b & 0xFF

    def __str__(self):
        return "rgb({}, {}, {})".format(self.red, self.green, self.blue)

    def to_int(self, brightness=1.0):
        if brightness != 1.0:
            red = int(self.red * brightness) & 0xFF
            green = int(self.green * brightness) & 0xFF
            blue = int(self.blue * brightness) & 0xFF
            return (red << 16) | (green << 8) | blue
        else:
            return (self.red << 16) | (self.green << 8) | self.blue




HourColor = ColorRGB(0, 32, 0)
MinuteColor = ColorRGB(0, 0, 32)
SecondColor = ColorRGB(32, 0, 0)
TestColor = ColorRGB(0, 16, 0)


# CLK: P10 or P19,  MOSI: P11 or P20
SPI_PIN_CLK = 'P10'  # WiPy 3.0  GPIO-13,  
SPI_PIN_MOSI = 'P11'  # WiPy 3.0 GPIO-22
SPI_PIN_MISO = 'P14'  # WiPy 3.0

# The mapping of expansion board to WiPy 3.0 is wrong! Here ist the correct mapping:
# Most of the lines from WiPy to Expansion board are straight!

# P10 = G13 (MOSI)
# P11 = G22 (CLK)
# P12 = G21



class LedDisplay:

    OFF_COLOR = ColorRGB(0, 0, 0)
    RED = ColorRGB(21, 1, 1)
    GREEN = ColorRGB(1, 21, 1)
    BLUE = ColorRGB(1, 1, 21)

    def __init__(self, row_lengths=(5,6), row_colors=(HourColor, MinuteColor) ):
        self.color_minutes = MinuteColor
        self.rows = len(row_lengths)
        self.row_lengths=row_lengths
        self.row_colors=row_colors
        self.total_pixels = sum(row_lengths)
        self.brightness = 0.2
        
        self.pixels = WS2801(SPI_PIN_CLK, SPI_PIN_MOSI, self.total_pixels, brightness=1.0, auto_write=False)  # sum(pixels)
        time.sleep(0.5)
        self.clear()


    def clear(self):
        self.show( (0,0) )


    def set_pixel(self, idx, color):
        self.pixels[idx] = color.to_int( self.brightness )

    def set_buf(self, colors):
        if len(colors) > self.total_pixels:
            colors = colors[:self.total_pixels]
        for pxl_idx, pxl_color in enumerate(colors):
            self.set_pixel(pxl_idx, pxl_color)

    def set_row(self, row_idx, value, row_color=None):
        #print("set_row: ", row_idx, ", ", value, ", ", row_color)
        if row_color == None:
            row_color = self.row_colors[row_idx]
        row_length = self.row_lengths[row_idx]
        row_value = min(max(value, 0), 2**(row_length)-1)

        for col_idx in range(row_length):
            state = (row_value >> col_idx) & 1
            pxl_color = row_color if (state == 1) else self.OFF_COLOR
            pxl_idx = sum(self.row_lengths[:row_idx])
            pxl_idx = pxl_idx+row_length-col_idx-1 if row_idx == 1 else pxl_idx+col_idx
            self.set_pixel(pxl_idx, pxl_color)

    def set_rows(self, row_values=(0,0), row_colors=None):
        #print("set_rows: ", row_values, ", ", row_colors)
        if row_colors == None:
            row_colors = self.row_colors
        for row_idx in range(len(self.row_lengths)):
            self.set_row(row_idx, row_values[row_idx], row_colors[row_idx])


    def show(self, row_values=None, row_colors=None):
        if row_values == None:
            #self.clear_remaining()
            self.pixels.show()
            return True

        if row_colors == None:
            row_colors = self.row_colors
        for row_idx, row_length in enumerate(self.row_lengths):
            row_value = min(max(row_values[row_idx], 0), 2**(row_length)-1)
            row_color = row_colors[row_idx]
            #print("row: {}, value: {}, color: {}".format(row_idx, row_value, row_color))

            for col_idx in range(row_length):
                state = (row_value >> col_idx) & 1
                #print("setting pixel {} to {}".format(pxl_idx, state))
                pxl_color = row_color if (state == 1) else self.OFF_COLOR
                pxl_idx = sum(self.row_lengths[:row_idx])
                pxl_idx = pxl_idx+row_length-col_idx-1 if row_idx == 1 else pxl_idx+col_idx
                self.set_pixel(pxl_idx, pxl_color)

        #print("pixel states: ",self.pixels)
        self.pixels.show()

    def clear_remaining( self, remaining=0 ):
        for pxl_idx in range( self.total_pixels, self.total_pixels+remaining ):
            self.pixels[pxl_idx] = self.OFF_COLOR.to_int()

    # deprecated
    def sync(self):
        self.pixels.show()


    def set_brightness(self, val):
        self.brightness = val


    def test(self):
        time.sleep(0.5)
        for i in range(self.total_pixels):
            for color in [self.RED, self.GREEN, self.BLUE]:
                self.pixels[i] = color.to_int()
                self.pixels.show()
                time.sleep(0.5)
            print("pixel states: ",self.pixels)
            self.pixels[i] = self.OFF_COLOR.to_int()
            self.pixels.show()
            #self.pixels.show()
        
        #self.show( (3,3,3) )
        time.sleep(3)
        self.clear()


    def start(self):
        print("starting up binary clock")
        print("second color is: ", hex(SecondColor.to_int()) )
        self.test()



# Writing text idea: 
#   •    •    •••  •••   ••••  •••  •••   •  •    •      •   • ••   •     •• ••  ••  •  ••••  •••  •••  •••   •••   •••••   •  •  •   •  •   •  •• ••  •• ••  •••••
#  •••   •••  •    • ••  •••   ••   •  •  ••••    •    • •   •••    •     • • •  • • •  •  •  •••  •••  •••   ••••    •     •  •   • •   • • •    •      •      ••
# •   •  •••  •••  •••   ••••  •    ••••  •  •   •••   •••   • ••   •••   •   •  •  ••  ••••  •      •  •  •   •••    •     ••••    •     • •   •• ••    •     ••••


