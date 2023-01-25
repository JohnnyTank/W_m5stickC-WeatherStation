# M5Stick.py - constants
from machine import Pin
from time  import sleep_ms

RED_LED = const(10)
BUT_A = const(37)
BUT_B = const(39)
GROVE_SCL = const(33)
GROVE_SDA = const(32)


class Button:
    def __init__(self):
        self.BTN_A = Pin(BUT_A, Pin.IN)
        self.BTN_B = Pin(BUT_B, Pin.IN)
        
    def all_buttons(self):
        alle = (self.BTN_A.value(), self.BTN_B.value())
        #print(alle)
        return alle
    
    def a_pressed(self):
        but = self.all_buttons()
        return not(but[0])
    
    def b_pressed(self):
        but = self.all_buttons()
        return not(but[1])
        
if (__name__ == '__main__'):
    buttons = Button()
    but_arr = buttons.all_buttons()
    while (but_arr != (0, 0)):
        but_arr = buttons.all_buttons()
        print('button A: ' +  str(buttons.a_pressed()))
        print('button B: ' +  str(buttons.b_pressed()))
        sleep_ms(100)
