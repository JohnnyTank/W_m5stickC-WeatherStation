# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()
from machine import Pin
import M5Stick
from time import sleep_ms

led = Pin(M5Stick.RED_LED, Pin.OUT)
for i in range (5):
    led.off()
    sleep_ms(100)
    led.on()
    sleep_ms(100)
  

