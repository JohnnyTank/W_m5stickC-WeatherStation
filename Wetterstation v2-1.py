# Wetterstation V2.1 14.10.2022 by O. Werner
# Wetterstation V2.0 by Olaf Werner
import m5stickc_lcd
import M5Stick
import ui
from time import sleep_ms
from machine import Pin, I2C, reset
import machine
import ENV
import time
import wlan
import _thread
import ubinascii
import BlynkLib as blynklib

lcd = m5stickc_lcd.ST7735()
lcd.set_rotate(m5stickc_lcd.ROTATE_90)
label1 = ui.label(lcd, 'Luftdruck: ', 2, 2, m5stickc_lcd.WHITE, m5stickc_lcd.MONACO12)
label2 = ui.label(lcd, 'Luftfeuchtigkeit: ',2, 20, m5stickc_lcd.WHITE, m5stickc_lcd.MONACO12)
label3 = ui.label(lcd, 'Temperatur: ',2, 40, m5stickc_lcd.WHITE, m5stickc_lcd.MONACO12)

i2c = I2C(1, scl = Pin(26), sda = Pin(0), freq = 100000)
dev1 = ENV.BMP280(i2c)
dev2 =ENV.DHT12(i2c)
BLYNK_AUTH = 'gM9Ab7D_ZraLEVYY-30BzbDvUn3qbD3X'
#define BLYNK_TEMPLATE_ID "TMPL9mWPWJac"
#define BLYNK_DEVICE_NAME "M5 Stick"
#define BLYNK_AUTH_TOKEN "gM9Ab7D_ZraLEVYY-30BzbDvUn3qbD3X"

def get_pressure(dev):
    ret=0
    for i in range(10):
        ret += dev.pressure()
        sleep_ms(200)
    ret = ret / 10.0
    return ret

def get_temperature(dev1, dev2):
    ret = 0
    for i in range(10):
        temp1 = dev1.temperature()
        dev2.measure()
        temp2 = dev2.temperature()
        ot = (temp1 + temp2)/2.0
        sleep_ms(200)
        ret += ot
    ret = ret / 10.0
    return round((ret-6.983),1)

def get_humidity(dev):
    ret = 0
    for i in range(10):
        dev.measure()
        ret += dev.humidity()
        sleep_ms(400)
    ret = ret / 10.0
    return ret

def but_thread():
    global buttons
    while (True):
        if (buttons.all_buttons() == (0, 0)):
            raise Exception ('Programm terminated')


  
buttons=M5Stick.Button()
wlan.do_connect()    # open WLAN


client_id = ubinascii.hexlify(machine.unique_id())
print(client_id)

print ('Connecting to Blynk server...')
blynk = blynklib.Blynk(BLYNK_AUTH)

start = time.ticks_ms()
flag = True
try:
    while flag:
        #print (buttons.all_buttons())
        flag = not (buttons.all_buttons() == (0,0))
        #print (flag)
        now = time.ticks_ms()
        blynk.run()
        if (now-start > 2000):
            print('Messung läuft...')
            p = round(get_pressure(dev1)/100, 1)
            t = get_temperature(dev1, dev2)
            h = round(get_humidity(dev2), 1)
            blynk.virtual_write(10, str(t) + ' °C')
            blynk.virtual_write(11, str(p) + ' hPa')
            blynk.virtual_write(12, str(h) + ' %')
            blynk.virtual_write(5, p)
            label1.set_text('P: ' + str(p))
            label2.set_text('H: ' + str(h))
            label3.set_text('T: ' + str(t))
            start = time.ticks_ms()
        if not(flag):
            label1.set_text('Programmende')
            label2.set_text('-')
            label3.set_text('-')
except:
    reset()
        
    
