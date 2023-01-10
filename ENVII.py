#ENV.py
from micropython import const
from ustruct import unpack as unp
from machine import Pin, I2C, SoftI2C
from time import sleep_ms

# Author David Stenwall Wahlund (david at dafnet.se)

# Power Modes
BMP280_POWER_SLEEP = const(0)
BMP280_POWER_FORCED = const(1)
BMP280_POWER_NORMAL = const(3)

BMP280_SPI3W_ON = const(1)
BMP280_SPI3W_OFF = const(0)

BMP280_TEMP_OS_SKIP = const(0)
BMP280_TEMP_OS_1 = const(1)
BMP280_TEMP_OS_2 = const(2)
BMP280_TEMP_OS_4 = const(3)
BMP280_TEMP_OS_8 = const(4)
BMP280_TEMP_OS_16 = const(5)

BMP280_PRES_OS_SKIP = const(0)
BMP280_PRES_OS_1 = const(1)
BMP280_PRES_OS_2 = const(2)
BMP280_PRES_OS_4 = const(3)
BMP280_PRES_OS_8 = const(4)
BMP280_PRES_OS_16 = const(5)

# Standby settings in ms
BMP280_STANDBY_0_5 = const(0)
BMP280_STANDBY_62_5 = const(1)
BMP280_STANDBY_125 = const(2)
BMP280_STANDBY_250 = const(3)
BMP280_STANDBY_500 = const(4)
BMP280_STANDBY_1000 = const(5)
BMP280_STANDBY_2000 = const(6)
BMP280_STANDBY_4000 = const(7)

# IIR Filter setting
BMP280_IIR_FILTER_OFF = const(0)
BMP280_IIR_FILTER_2 = const(1)
BMP280_IIR_FILTER_4 = const(2)
BMP280_IIR_FILTER_8 = const(3)
BMP280_IIR_FILTER_16 = const(4)

# Oversampling setting
BMP280_OS_ULTRALOW = const(0)
BMP280_OS_LOW = const(1)
BMP280_OS_STANDARD = const(2)
BMP280_OS_HIGH = const(3)
BMP280_OS_ULTRAHIGH = const(4)

# Oversampling matrix
# (PRESS_OS, TEMP_OS, sample time in ms)
_BMP280_OS_MATRIX = [
    [BMP280_PRES_OS_1, BMP280_TEMP_OS_1, 7],
    [BMP280_PRES_OS_2, BMP280_TEMP_OS_1, 9],
    [BMP280_PRES_OS_4, BMP280_TEMP_OS_1, 14],
    [BMP280_PRES_OS_8, BMP280_TEMP_OS_1, 23],
    [BMP280_PRES_OS_16, BMP280_TEMP_OS_2, 44]
]

# Use cases
BMP280_CASE_HANDHELD_LOW = const(0)
BMP280_CASE_HANDHELD_DYN = const(1)
BMP280_CASE_WEATHER = const(2)
BMP280_CASE_FLOOR = const(3)
BMP280_CASE_DROP = const(4)
BMP280_CASE_INDOOR = const(5)

_BMP280_CASE_MATRIX = [
    [BMP280_POWER_NORMAL, BMP280_OS_ULTRAHIGH, BMP280_IIR_FILTER_4, BMP280_STANDBY_62_5],
    [BMP280_POWER_NORMAL, BMP280_OS_STANDARD, BMP280_IIR_FILTER_16, BMP280_STANDBY_0_5],
    [BMP280_POWER_FORCED, BMP280_OS_ULTRALOW, BMP280_IIR_FILTER_OFF, BMP280_STANDBY_0_5],
    [BMP280_POWER_NORMAL, BMP280_OS_STANDARD, BMP280_IIR_FILTER_4, BMP280_STANDBY_125],
    [BMP280_POWER_NORMAL, BMP280_OS_LOW, BMP280_IIR_FILTER_OFF, BMP280_STANDBY_0_5],
    [BMP280_POWER_NORMAL, BMP280_OS_ULTRAHIGH, BMP280_IIR_FILTER_16, BMP280_STANDBY_0_5]
]

_BMP280_REGISTER_ID = const(0xD0)
_BMP280_REGISTER_RESET = const(0xE0)
_BMP280_REGISTER_STATUS = const(0xF3)
_BMP280_REGISTER_CONTROL = const(0xF4)
_BMP280_REGISTER_CONFIG = const(0xF5)  # IIR filter config

_BMP280_REGISTER_DATA = const(0xF7)


class BMP280:
    def __init__(self, i2c, use_case=BMP280_CASE_HANDHELD_DYN):
        #self._bmp_i2c = SoftI2C(scl=Pin(26), sda = Pin(0), freq = 100000)
        self._bmp_i2c = i2c
        self._i2c_addr = 0x76

        # read calibration data
        # < little-endian
        # H unsigned short
        # h signed short
        self._T1 = unp('<H', self._read(0x88, 2))[0]
        self._T2 = unp('<h', self._read(0x8A, 2))[0]
        self._T3 = unp('<h', self._read(0x8C, 2))[0]
        self._P1 = unp('<H', self._read(0x8E, 2))[0]
        self._P2 = unp('<h', self._read(0x90, 2))[0]
        self._P3 = unp('<h', self._read(0x92, 2))[0]
        self._P4 = unp('<h', self._read(0x94, 2))[0]
        self._P5 = unp('<h', self._read(0x96, 2))[0]
        self._P6 = unp('<h', self._read(0x98, 2))[0]
        self._P7 = unp('<h', self._read(0x9A, 2))[0]
        self._P8 = unp('<h', self._read(0x9C, 2))[0]
        self._P9 = unp('<h', self._read(0x9E, 2))[0]

        # output raw
        self._t_raw = 0
        self._t_fine = 0
        self._t = 0

        self._p_raw = 0
        self._p = 0

        self.read_wait_ms = 0  # interval between forced measure and readout
        self._new_read_ms = 200  # interval between
        self._last_read_ts = 0

        if use_case is not None:
            self.use_case(use_case)

    def _read(self, addr, size=1):
        return self._bmp_i2c.readfrom_mem(self._i2c_addr, addr, size)

    def _write(self, addr, b_arr):
        if not type(b_arr) is bytearray:
            b_arr = bytearray([b_arr])
        return self._bmp_i2c.writeto_mem(self._i2c_addr, addr, b_arr)

    def _gauge(self):
        # TODO limit new reads
        # read all data at once (as by spec)
        d = self._read(_BMP280_REGISTER_DATA, 6)

        self._p_raw = (d[0] << 12) + (d[1] << 4) + (d[2] >> 4)
        self._t_raw = (d[3] << 12) + (d[4] << 4) + (d[5] >> 4)

        self._t_fine = 0
        self._t = 0
        self._p = 0

    def reset(self):
        self._write(_BMP280_REGISTER_RESET, 0xB6)

    def load_test_calibration(self):
        self._T1 = 27504
        self._T2 = 26435
        self._T3 = -1000
        self._P1 = 36477
        self._P2 = -10685
        self._P3 = 3024
        self._P4 = 2855
        self._P5 = 140
        self._P6 = -7
        self._P7 = 15500
        self._P8 = -14600
        self._P9 = 6000

    def load_test_data(self):
        self._t_raw = 519888
        self._p_raw = 415148

    def print_calibration(self):
        print("T1: {} {}".format(self._T1, type(self._T1)))
        print("T2: {} {}".format(self._T2, type(self._T2)))
        print("T3: {} {}".format(self._T3, type(self._T3)))
        print("P1: {} {}".format(self._P1, type(self._P1)))
        print("P2: {} {}".format(self._P2, type(self._P2)))
        print("P3: {} {}".format(self._P3, type(self._P3)))
        print("P4: {} {}".format(self._P4, type(self._P4)))
        print("P5: {} {}".format(self._P5, type(self._P5)))
        print("P6: {} {}".format(self._P6, type(self._P6)))
        print("P7: {} {}".format(self._P7, type(self._P7)))
        print("P8: {} {}".format(self._P8, type(self._P8)))
        print("P9: {} {}".format(self._P9, type(self._P9)))

    def _calc_t_fine(self):
        # From datasheet page 22
        self._gauge()
        if self._t_fine == 0:
            var1 = (((self._t_raw >> 3) - (self._T1 << 1)) * self._T2) >> 11
            var2 = (((((self._t_raw >> 4) - self._T1)
                      * ((self._t_raw >> 4)
                         - self._T1)) >> 12)
                    * self._T3) >> 14
            self._t_fine = var1 + var2

    #@property
    def temperature(self):
        self._calc_t_fine()
        if self._t == 0:
            self._t = ((self._t_fine * 5 + 128) >> 8) / 100.
        return self._t

   # @property
    def pressure(self):
        # From datasheet page 22
        self._calc_t_fine()
        if self._p == 0:
            var1 = self._t_fine - 128000
            var2 = var1 * var1 * self._P6
            var2 = var2 + ((var1 * self._P5) << 17)
            var2 = var2 + (self._P4 << 35)
            var1 = ((var1 * var1 * self._P3) >> 8) + ((var1 * self._P2) << 12)
            var1 = (((1 << 47) + var1) * self._P1) >> 33

            if var1 == 0:
                return 0

            p = 1048576 - self._p_raw
            p = int((((p << 31) - var2) * 3125) / var1)
            var1 = (self._P9 * (p >> 13) * (p >> 13)) >> 25
            var2 = (self._P8 * p) >> 19

            p = ((p + var1 + var2) >> 8) + (self._P7 << 4)
            self._p = p / 256.0
        return self._p

    def _write_bits(self, address, value, length, shift=0):
        d = self._read(address)[0]
        m = int('1' * length, 2) << shift
        d &= ~m
        d |= m & value << shift
        self._write(address, d)

    def _read_bits(self, address, length, shift=0):
        d = self._read(address)[0]
        return d >> shift & int('1' * length, 2)

    @property
    def standby(self):
        return self._read_bits(_BMP280_REGISTER_CONFIG, 3, 5)

    @standby.setter
    def standby(self, v):
        assert 0 <= v <= 7
        self._write_bits(_BMP280_REGISTER_CONFIG, v, 3, 5)

    @property
    def iir(self):
        return self._read_bits(_BMP280_REGISTER_CONFIG, 3, 2)

    @iir.setter
    def iir(self, v):
        assert 0 <= v <= 4
        self._write_bits(_BMP280_REGISTER_CONFIG, v, 3, 2)

    @property
    def spi3w(self):
        return self._read_bits(_BMP280_REGISTER_CONFIG, 1)

    @spi3w.setter
    def spi3w(self, v):
        assert v in (0, 1)
        self._write_bits(_BMP280_REGISTER_CONFIG, v, 1)

    @property
    def temp_os(self):
        return self._read_bits(_BMP280_REGISTER_CONTROL, 3, 5)

    @temp_os.setter
    def temp_os(self, v):
        assert 0 <= v <= 5
        self._write_bits(_BMP280_REGISTER_CONTROL, v, 3, 5)

    @property
    def press_os(self):
        return self._read_bits(_BMP280_REGISTER_CONTROL, 3, 2)

    @press_os.setter
    def press_os(self, v):
        assert 0 <= v <= 5
        self._write_bits(_BMP280_REGISTER_CONTROL, v, 3, 2)

    @property
    def power_mode(self):
        return self._read_bits(_BMP280_REGISTER_CONTROL, 2)

    @power_mode.setter
    def power_mode(self, v):
        assert 0 <= v <= 3
        self._write_bits(_BMP280_REGISTER_CONTROL, v, 2)

    @property
    def is_measuring(self):
        return bool(self._read_bits(_BMP280_REGISTER_STATUS, 1, 3))

    @property
    def is_updating(self):
        return bool(self._read_bits(_BMP280_REGISTER_STATUS, 1))

    @property
    def chip_id(self):
        return self._read(_BMP280_REGISTER_ID, 2)

    @property
    def in_normal_mode(self):
        return self.power_mode == BMP280_POWER_NORMAL

    def force_measure(self):
        self.power_mode = BMP280_POWER_FORCED

    def normal_measure(self):
        self.power_mode = BMP280_POWER_NORMAL

    def sleep(self):
        self.power_mode = BMP280_POWER_SLEEP

    def use_case(self, uc):
        assert 0 <= uc <= 5
        pm, oss, iir, sb = _BMP280_CASE_MATRIX[uc]
        p_os, t_os, self.read_wait_ms = _BMP280_OS_MATRIX[oss]
        self._write(_BMP280_REGISTER_CONFIG, (iir << 2) + (sb << 5))
        self._write(_BMP280_REGISTER_CONTROL, pm + (p_os << 2) + (t_os << 5))

    def oversample(self, oss):
        assert 0 <= oss <= 4
        p_os, t_os, self.read_wait_ms = _BMP280_OS_MATRIX[oss]
        self._write_bits(_BMP280_REGISTER_CONTROL, p_os + (t_os << 3), 2)

# from mcauser
class DHTBaseI2C:
    def __init__(self, i2c, addr=0x5c):
        self.i2c = i2c
        self.addr = addr
        self.buf = bytearray(5)
    def measure(self):
        buf = self.buf
        self.i2c.readfrom_mem_into(self.addr, 0, buf)
        if (buf[0] + buf[1] + buf[2] + buf[3]) & 0xff != buf[4]:
            raise Exception("checksum error")

class DHT12(DHTBaseI2C):
    def humidity(self):
        return self.buf[0] + self.buf[1] * 0.1

    def temperature(self):
        t = self.buf[2] + (self.buf[3] & 0x7f) * 0.1
        if self.buf[3] & 0x80:
            t = -t
        return t


class SHT30():
    """
    SHT30 sensor driver in pure python based on I2C bus
    
    References: 
    * https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/2_Humidity_Sensors/Sensirion_Humidity_Sensors_SHT3x_Datasheet_digital.pdf
    * https://www.wemos.cc/sites/default/files/2016-11/SHT30-DIS_datasheet.pdf
    * https://github.com/wemos/WEMOS_SHT3x_Arduino_Library
    * https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/11_Sample_Codes_Software/Humidity_Sensors/Sensirion_Humidity_Sensors_SHT3x_Sample_Code_V2.pdf
    """
    POLYNOMIAL = 0x131  # P(x) = x^8 + x^5 + x^4 + 1 = 100110001

    ALERT_PENDING_MASK = 0x8000 # 15
    HEATER_MASK = 0x2000        # 13
    RH_ALERT_MASK = 0x0800		# 11
    T_ALERT_MASK = 0x0400		# 10
    RESET_MASK = 0x0010	        # 4
    CMD_STATUS_MASK = 0x0002	# 1
    WRITE_STATUS_MASK = 0x0001	# 0

    # MSB = 0x2C LSB = 0x06 Repeatability = High, Clock stretching = enabled
    MEASURE_CMD = b'\x2C\x10'
    STATUS_CMD = b'\xF3\x2D'
    RESET_CMD = b'\x30\xA2'
    CLEAR_STATUS_CMD = b'\x30\x41'
    ENABLE_HEATER_CMD = b'\x30\x6D'
    DISABLE_HEATER_CMD = b'\x30\x66'

    def __init__(self, i2c, delta_temp = 0, delta_hum = 0):
        self.i2c = i2c
        self.i2c_addr = 0x44
        self.set_delta(delta_temp, delta_hum)
        sleep_ms(50)
    
    def init(self, scl_pin=5, sda_pin=4):
        """
        Init the I2C bus using the new pin values
        """
        self.i2c.init(scl=Pin(scl_pin), sda=Pin(sda_pin))
    
    def is_present(self):
        """
        Return true if the sensor is correctly conneced, False otherwise
        """
        return self.i2c_addr in self.i2c.scan()
    
    def set_delta(self, delta_temp = 0, delta_hum = 0):
        """
        Apply a delta value on the future measurements of temperature and/or humidity
        The units are Celsius for temperature and percent for humidity (can be negative values)
        """
        self.delta_temp = delta_temp
        self.delta_hum = delta_hum
    
    def _check_crc(self, data):
        # calculates 8-Bit checksum with given polynomial
        crc = 0xFF
        
        for b in data[:-1]:
            crc ^= b;
            for _ in range(8, 0, -1):
                if crc & 0x80:
                    crc = (crc << 1) ^ SHT30.POLYNOMIAL;
                else:
                    crc <<= 1
        crc_to_check = data[-1]
        return crc_to_check == crc
    
    def send_cmd(self, cmd_request, response_size=6, read_delay_ms=100):
        """
        Send a command to the sensor and read (optionally) the response
        The responsed data is validated by CRC
        """
        try:
            #self.i2c.start(); 
            self.i2c.writeto(self.i2c_addr, cmd_request); 
            if not response_size:
                #self.i2c.stop(); 	
                return
            sleep_ms(read_delay_ms)
            data = self.i2c.readfrom(self.i2c_addr, response_size) 
            #self.i2c.stop(); 
            for i in range(response_size//3):
                if not self._check_crc(data[i*3:(i+1)*3]): # pos 2 and 5 are CRC
                    raise SHT30Error(SHT30Error.CRC_ERROR)
            if data == bytearray(response_size):
                raise SHT30Error(SHT30Error.DATA_ERROR)
            return data
        except OSError as ex:
            if 'I2C' in ex.args[0]:
                raise SHT30Error(SHT30Error.BUS_ERROR)
            raise ex

    def clear_status(self):
        """
        Clear the status register
        """
        return self.send_cmd(SHT30.CLEAR_STATUS_CMD, None); 

    def reset(self):
        """
        Send a soft-reset to the sensor
        """
        return self.send_cmd(SHT30.RESET_CMD, None); 

    def status(self, raw=False):
        """
        Get the sensor status register. 
        It returns a int value or the bytearray(3) if raw==True
        """
        data = self.send_cmd(SHT30.STATUS_CMD, 3, read_delay_ms=20); 

        if raw:
            return data

        status_register = data[0] << 8 | data[1]
        return status_register
    
    def measure(self, raw=False):
        """
        If raw==True returns a bytearrya(6) with sensor direct measurement otherwise
        It gets the temperature (T) and humidity (RH) measurement and return them.
        
        The units are Celsius and percent
        """
        data = self.send_cmd(SHT30.MEASURE_CMD, 6); 

        if raw:
            return data

        t_celsius = (((data[0] << 8 |  data[1]) * 175) / 0xFFFF) - 45 + self.delta_temp;
        rh = (((data[3] << 8 | data[4]) * 100.0) / 0xFFFF) + self.delta_hum;
        return t_celsius, rh

    def measure_int(self, raw=False):
        """
        Get the temperature (T) and humidity (RH) measurement using integers.
        If raw==True returns a bytearrya(6) with sensor direct measurement otherwise
        It returns a tuple with 4 values: T integer, T decimal, H integer, H decimal
        For instance to return T=24.0512 and RH= 34.662 This method will return
        (24, 5, 34, 66) Only 2 decimal digits are returned, .05 becomes 5
        Delta values are not applied in this method
        The units are Celsius and percent.
        """
        data = self.send_cmd(SHT30.MEASURE_CMD, 6); 
        if raw: 
            return data
        aux = (data[0] << 8 | data[1]) * 175
        t_int = (aux // 0xffff) - 45;
        t_dec = (aux % 0xffff * 100) // 0xffff
        aux = (data[3] << 8 | data[4]) * 100
        h_int = aux // 0xffff
        h_dec = (aux % 0xffff * 100) // 0xffff
        return t_int, t_dec, h_int, h_dec


class SHT30Error(Exception):
    """
    Custom exception for errors on sensor management
    """
    BUS_ERROR = 0x01 
    DATA_ERROR = 0x02
    CRC_ERROR = 0x03

    def __init__(self, error_code=None):
        self.error_code = error_code
        super().__init__(self.get_message())
    
    def get_message(self):
        if self.error_code == SHT30Error.BUS_ERROR:
            return "Bus error"
        elif self.error_code == SHT30Error.DATA_ERROR:
            return "Data error"
        elif self.error_code == SHT30Error.CRC_ERROR:
            return "CRC error"
        else:
            return "Unknown error"



            

if (__name__ == '__main__'):
    i2c = I2C(1, scl = Pin(26), sda = Pin(0), freq = 100000)
    print(i2c.scan())
    dev = BMP280(i2c)
    #dev2 = DHT12(i2c)
    dev2 = SHT30(i2c, delta_temp=0, delta_hum=0)
    for i in range(10):
        p = (dev.pressure())
        t = dev.temperature()
        #dev2.measure()
        t2, h = dev2.measure()
        print('Druck: ' + str(p))
        print('Temperatur: ' + str(t))
        print('Luftfeuchte: ' + str(h))
        print('Temperatur 2: ' + str(t2))
        #print("{:.2f}".format(p))
        sleep_ms(1000)
    