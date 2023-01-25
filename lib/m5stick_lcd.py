#m5stick_lcd.py (c) by pklazy

import framebuf
import time
from machine import Pin, SPI, I2C

'''
import m5stickc_lcd
lcd = m5stickc_lcd.ST7735()
lcd.text('hello', 10, 10, 0xffff)
lcd.show()
'''
LCD_WIDTH = const(80)
LCD_HEIGHT = const(160)

BLUE = const(0xff00)
YELLOW = const(0x7ff)
MAGENTA = const(0x07ff)
GREEN = const(0xf81f)
LIGHT_GREEN = const(0x911e)
RED = const(0x7e0)
BLACK = const(0x0000)
VIOLET = const(0xfda0)
ORANGE = const(0x001f)
WHITE = const(0xffff)

#WHITE = const(0xff)
#BLACK = const(0x00)
#DRAW_WHITE = const(0)
#DRAW_BLACK = const(1)

ROTATE_0 = const(0)
ROTATE_90 = const(1)
ROTATE_180 = const(2)
ROTATE_270 = const(3)
FONT_20 = const(0)
MONACO12 = const(1)
MONACO16 = const(2)
MONACO16_BOLD = const(3)


class ST7735(framebuf.FrameBuffer):
    def __init__(self):
        self.baudrate = 27000000
        self.cs = Pin(5, Pin.OUT, value=1)
        self.dc = Pin(23, Pin.OUT, value=1)
        self.rst = Pin(18, Pin.OUT, value=1)
        self.spi = SPI(
                1, baudrate=self.baudrate,
                polarity=0, phase=0, bits=8, firstbit=SPI.MSB,
                sck=Pin(13), mosi=Pin(15))

        self.enable_lcd_power()

        self.rst.on()
        time.sleep_ms(5)
        self.rst.off()
        time.sleep_ms(20)
        self.rst.on()
        time.sleep_ms(150)
        self.screen_color = BLACK
        self.rotate = ROTATE_0
        self.width = 80
        self.height = 160
        self.buffer = bytearray(self.width * self.height * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()

    def enable_lcd_power(self):
        i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=100000)
        i2c.writeto_mem(0x34, 0x28, b'\xff')
        axp192_reg12 = i2c.readfrom_mem(0x34, 0x12, 1)[0]
        axp192_reg12 |= 0x0c
        i2c.writeto_mem(0x34, 0x12, bytes([axp192_reg12]))

    def init_display(self):
        for cmd, data, delay in [
            (0x01, None, 150),
            (0x11, None, 500),
            (0xb1, b'\x01\x2c\x2d', None),
            (0xb2, b'\x01\x2c\x2d', None),
            (0xb3, b'\x01\x2c\x2d\x01\x2c\x2d', None),
            (0xb4, b'\x07', None),
            (0xc0, b'\xa2\x02\x84', None),
            (0xc1, b'\xc5', None),
            (0xc2, b'\x0a\x00', None),
            (0xc3, b'\x8a\x2a', None),
            (0xc4, b'\x8a\xee', None),
            (0xc5, b'\x0e', None),
            (0x20, None, None),
            (0x36, b'\xc8', None),
            (0x3a, b'\x05', None),
            (0x2a, b'\x00\x02\x00\x81', None),
            (0x2b, b'\x00\x01\x00\xa0', None),
            (0x21, None, None),
            (0xe0, b'\x02\x1c\x07\x12\x37\x32\x29\x2d\x29\x25\x2b\x39\x00\x01\x03\x10', None),
            (0xe1, b'\x03\x1d\x07\x06\x2e\x2c\x29\x2d\x2e\x2e\x37\x3f\x00\x00\x02\x10', None),
            (0x13, None, 10),
            (0x29, None, 100),
            (0x36, b'\xcc', 10),
        ]:
            self.write_cmd(cmd)
            if data:
                self.write_data(data)
            if delay:
                time.sleep_ms(delay)
        self.fill(0)
        self.show()

    def show(self):
        self.write_cmd(0x2a)
        self.write_data(b'\x00\x1a\x00\x69')
        self.write_cmd(0x2b)
        self.write_data(b'\x00\x01\x00\xa0')
        self.write_cmd(0x2c)
        self.write_data(self.buffer)

    def write_cmd(self, cmd):
        self.dc.off()
        self.cs.off()
        self.spi.write(bytes([cmd]))
        self.cs.on()

    def write_data(self, buf):
        self.dc.on()
        self.cs.off()
        self.spi.write(buf)
        self.cs.on()
        
     # ******** Routines my MCAUSER *********
    def set_rotate(self, rotate):
        if (rotate == ROTATE_0):
            self.rotate = ROTATE_0
            self.width = LCD_WIDTH
            self.height = LCD_HEIGHT
        elif (rotate == ROTATE_90):
            self.rotate = ROTATE_90
            self.width = LCD_HEIGHT
            self.height = LCD_WIDTH
        elif (rotate == ROTATE_180):
            self.rotate = ROTATE_180
            self.width = LCD_WIDTH
            self.height = LCD_HEIGHT
        elif (rotate == ROTATE_270):
            self.rotate = ROTATE_270
            self.width = LCD_HEIGHT
            self.height = LCD_WIDTH

    def set_pixel(self, x, y, color):
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return
        if (self.rotate == ROTATE_0):
            self.pixel(x, y, color)
        elif (self.rotate == ROTATE_90):
            point_temp = x
            x = LCD_WIDTH - y
            y = point_temp
            self.pixel(x, y, color)
        elif (self.rotate == ROTATE_180):
            x = LCD_WIDTH - x
            y = LCD_HEIGHT- y
            self.pixel(x, y, color)
        elif (self.rotate == ROTATE_270):
            point_temp = x
            x = y
            y = LCD_HEIGHT - point_temp
            self.pixel( x, y, color)

    def set_absolute_pixel(self, x, y, colored):
        # To avoid display orientation effects
        # use EPD_WIDTH instead of self.width
        # use EPD_HEIGHT instead of self.height
        if (x < 0 or x >= LCD_WIDTH or y < 0 or y >= LCD_HEIGHT):
            return
        if (colored):
            self.buffer[(x + y * LCD_WIDTH) // 8] &= ~(0x80 >> (x % 8))
        else:
            self.buffer[(x + y * LCD_WIDTH) // 8] |= 0x80 >> (x % 8)

    # ******** Routines by O. Werner *******
    # Version 1.2 - 9.9.2022
    # Version 1.3 - 27.09.2022
    def clear_screen(self):
        self.fill(0)
        #self.show()
        
    def read_char(self, char, font):
        if (font == FONT_20):
            f = open('font20/' + str(ord(char)) + '.bin', 'r')
        elif (font == MONACO12):
            f = open('monaco12/' + str(ord(char)) + '.bin', 'r')
        elif (font == MONACO16):
            f = open('monaco16/' + str(ord(char)) + '.bin', 'r')
        elif (font == MONACO16_BOLD):
           f = open('monaco16bold/' + str(ord(char)) + '.bin', 'r') 
        data = f.read()
        f.close()
        start = 0
        end = data.find('-') 
        #print(data[start:end])
        width = int(data[start:end])
        start = end + 1
        end = data.find('-', start)
        #print(data[start:end])
        height = int(data[start:end])
        bitMap = data[end+1:len(data)]
        return width, height, bitMap
    
    def draw_char(self, char, x, y, color, font):
        data = self.read_char(char, font)
        width = data[0]
        height = data [1]
        bitMap = data[2]
        # print(bitMap)
        x_off = x
        y_off = y
        i = 0
        for bit in bitMap:
            if (bit == '1'):
                self.set_pixel(x_off, y_off, color)
            x_off += 1
            if (x_off >= (x + width)):
                x_off = x
                y_off += 1
                
    def draw_string(self, myStr, x, y, color, font):
        width = self.read_char(myStr[0], font)[0]
        i = 0
        
        x_off = x
        y_off = y
        for char in myStr:
            if (char != ' '):
                self.draw_char(char, x_off + i * width, y_off, color, font)
            i += 1
    
    def draw_vline(self, x, y, l, color):
        for i in range(l):
            self.set_pixel(x, y+i, color)
            
    def draw_line(self, x0, y0, x1, y1, color):
        m=(y1-y0)/(x1-x0)
        if (x0<x1):
            for x in range(x0,x1):
                y = int(m * x + y0-m*x0)
                self.set_pixel(x, y, color)
        else:
            for x in range(x1,x0):
                y = int(m * x + y0-m*x0)
                self.set_pixel(x, y, color)
            
    def draw_rect(self, x, y, w, h, color, filled):
        self.draw_line(x, y, x+w, y, color)
        self.draw_line(x, y+h, x+w, y+h, color)
        self.draw_vline(x, y, h, color)
        self.draw_vline(x+w, y, h, color)        
        if filled:
            for i in range(y+1, y+h):
                self.draw_line(x, i, x + w, i, color)
              
        

if (__name__ == '__main__'):
    c_codes = [BLUE, YELLOW, MAGENTA, GREEN, LIGHT_GREEN, RED, BLACK, VIOLET, ORANGE, WHITE]
    c_text = ['BLUE', 'yellow', 'magenta', 'green', 'light-green', 'red', 'black', 'violet', 'Orange', 'White']
    lcd = ST7735()
    lcd.set_rotate(ROTATE_90)
    i = 0
    for color in c_codes:
         lcd.draw_string(c_text[i], 2, 2, color, MONACO12)
         lcd.show()
         i += 1
         time.sleep_ms(100)
         lcd.clear_screen()
    lcd.draw_rect(10, 10, 10, 10, WHITE, False)
    lcd.draw_rect(30, 10, 10, 10, WHITE, True)
    lcd.draw_line(0,20,159,79, YELLOW)
    lcd.draw_line(159,20,0,79,YELLOW)
    lcd.show()
   