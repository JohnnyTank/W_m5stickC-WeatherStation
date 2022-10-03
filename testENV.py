import m5stickc_lcd
import M5Stick
import ui
from time import sleep_ms


lcd = m5stickc_lcd.ST7735()
lcd.set_rotate(m5stickc_lcd.ROTATE_90)
label1 = ui.label(lcd, 'Luftdruck: ', 2, 2, m5stickc_lcd.WHITE, m5stickc_lcd.MONACO12)
label2 = ui.label(lcd, 'Luftfeuchtigkeit: ',2, 20, m5stickc_lcd.WHITE, m5stickc_lcd.MONACO12)
label3 = ui.label(lcd, 'Temperatur: ',2, 40, m5stickc_lcd.WHITE, m5stickc_lcd.MONACO12)

