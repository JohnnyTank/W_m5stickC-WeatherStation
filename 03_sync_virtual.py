"""
Blynk is a platform with iOS and Android apps to control
Arduino, Raspberry Pi and the likes over the Internet.
You can easily build graphic interfaces for all your
projects by simply dragging and dropping widgets.

  Downloads, docs, tutorials: http://www.blynk.cc
  Sketch generator:           http://examples.blynk.cc
  Blynk community:            http://community.blynk.cc
  Social networks:            http://www.fb.com/blynkapp
                              http://twitter.com/blynk_app
"""
import wlan
import BlynkLib
from time import sleep_ms

BLYNK_AUTH = 'gM9Ab7D_ZraLEVYY-30BzbDvUn3qbD3X'

# initialize Blynk
blynk = BlynkLib.Blynk(BLYNK_AUTH)

@blynk.on("V*")
def blynk_handle_vpins(pin, value):
    global _pin
    global _value
    _pin = pin
    _value = value
    print("V{} value: {}".format(pin, value))
    if (pin == 1):
        print('Pin1')

@blynk.on("connected")
def blynk_connected():
    # You can also use blynk.sync_virtual(pin)
    # to sync a specific virtual pin
    print("Updating V1,V2,V3 values from the server...")
    blynk.sync_virtual(1,2,3)

wlan.do_connect()
_pin = 0
_value = '0'

while True:
    blynk.run()
    print(str(_pin) + '-' + _value[0] )
    sleep_ms(1000)
   