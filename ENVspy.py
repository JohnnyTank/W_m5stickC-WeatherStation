#ENVspy.py
from machine import Pin, SoftI2C
from time import sleep_ms

class ENV:
    def __init__(self):
        self.i2c =SoftI2C(scl = Pin(26), sda = Pin(0), freq = 50000)
        self.adr1 = 0x10
        self.adr2 = 0x5c
        self.BMP280 = 0x76
        
    def read_spy(self):
        print(self.i2c.readfrom(self.adr2,5))
        buf = (self.i2c.readfrom(self.BMP280,5))

if (__name__ == '__main__'):
    dev=ENV()
    for i in range(10):
        dev.read_spy()
        sleep_ms(500)
              
              
    