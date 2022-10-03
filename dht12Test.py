import dht12
from machine import I2C, Pin


i2c = I2C(scl=Pin(26), sda=Pin(0))
sensor = dht12.DHT12(i2c)
sensor.measure()

print(sensor.temperature())
print(sensor.humidity())