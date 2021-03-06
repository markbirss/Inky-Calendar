#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Drivers file for Inky-Calendar software.
Handles E-Paper display related tasks
"""

from PIL import Image
import RPi.GPIO as GPIO
from settings import display_type
import numpy
import spidev
import RPi.GPIO as GPIO
from time import sleep

RST_PIN = 17
DC_PIN = 25
CS_PIN = 8
BUSY_PIN = 24

EPD_WIDTH = 640
EPD_HEIGHT = 384

SPI = spidev.SpiDev(0, 0)

def epd_digital_write(pin, value):
  GPIO.output(pin, value)

def epd_digital_read(pin):
  return GPIO.input(BUSY_PIN)

def epd_delay_ms(delaytime):
  sleep(delaytime / 1000.0)

def spi_transfer(data):
  SPI.writebytes(data)

def epd_init():
  GPIO.setmode(GPIO.BCM)
  GPIO.setwarnings(False)
  GPIO.setup(RST_PIN, GPIO.OUT)
  GPIO.setup(DC_PIN, GPIO.OUT)
  GPIO.setup(CS_PIN, GPIO.OUT)
  GPIO.setup(BUSY_PIN, GPIO.IN)
  SPI.max_speed_hz = 4000000
  SPI.mode = 0b00
  return 0;

# EPD7IN5 commands
PANEL_SETTING                               = 0x00
POWER_SETTING                               = 0x01
POWER_OFF                                   = 0x02
POWER_OFF_SEQUENCE_SETTING                  = 0x03
POWER_ON                                    = 0x04
POWER_ON_MEASURE                            = 0x05
BOOSTER_SOFT_START                          = 0x06
DEEP_SLEEP                                  = 0x07
DATA_START_TRANSMISSION_1                   = 0x10
DATA_STOP                                   = 0x11
DISPLAY_REFRESH                             = 0x12
IMAGE_PROCESS                               = 0x13
LUT_FOR_VCOM                                = 0x20
LUT_BLUE                                    = 0x21
LUT_WHITE                                   = 0x22
LUT_GRAY_1                                  = 0x23
LUT_GRAY_2                                  = 0x24
LUT_RED_0                                   = 0x25
LUT_RED_1                                   = 0x26
LUT_RED_2                                   = 0x27
LUT_RED_3                                   = 0x28
LUT_XON                                     = 0x29
PLL_CONTROL                                 = 0x30
TEMPERATURE_SENSOR_COMMAND                  = 0x40
TEMPERATURE_CALIBRATION                     = 0x41
TEMPERATURE_SENSOR_WRITE                    = 0x42
TEMPERATURE_SENSOR_READ                     = 0x43
VCOM_AND_DATA_INTERVAL_SETTING              = 0x50
LOW_POWER_DETECTION                         = 0x51
TCON_SETTING                                = 0x60
TCON_RESOLUTION                             = 0x61
SPI_FLASH_CONTROL                           = 0x65
REVISION                                    = 0x70
GET_STATUS                                  = 0x71
AUTO_MEASUREMENT_VCOM                       = 0x80
READ_VCOM_VALUE                             = 0x81
VCM_DC_SETTING                              = 0x82

class EPD:
  def __init__(self):
    self.reset_pin = RST_PIN
    self.dc_pin = DC_PIN
    self.busy_pin = BUSY_PIN
    self.width = EPD_WIDTH
    self.height = EPD_HEIGHT

  def digital_write(self, pin, value):
    epd_digital_write(pin, value)

  def digital_read(self, pin):
    return epd_digital_read(pin)

  def delay_ms(self, delaytime):
    epd_delay_ms(delaytime)

  def send_command(self, command):
    self.digital_write(self.dc_pin, GPIO.LOW)
    spi_transfer([command])

  def send_data(self, data):
    self.digital_write(self.dc_pin, GPIO.HIGH)
    spi_transfer([data])

  def init(self):
    if (epd_init() != 0):
        return -1
    self.reset()
    self.send_command(POWER_SETTING)
    self.send_data(0x37)
    self.send_data(0x00)
    self.send_command(PANEL_SETTING)
    self.send_data(0xCF)
    self.send_data(0x08)
    self.send_command(BOOSTER_SOFT_START)
    self.send_data(0xc7)
    self.send_data(0xcc)
    self.send_data(0x28)
    self.send_command(POWER_ON)
    self.wait_until_idle()
    self.send_command(PLL_CONTROL)
    self.send_data(0x3c)
    self.send_command(TEMPERATURE_CALIBRATION)
    self.send_data(0x00)
    self.send_command(VCOM_AND_DATA_INTERVAL_SETTING)
    self.send_data(0x77)
    self.send_command(TCON_SETTING)
    self.send_data(0x22)
    self.send_command(TCON_RESOLUTION)
    self.send_data(0x02)     #source 640
    self.send_data(0x80)
    self.send_data(0x01)     #gate 384
    self.send_data(0x80)
    self.send_command(VCM_DC_SETTING)
    self.send_data(0x1E)      #decide by LUT file
    self.send_command(0xe5)           #FLASH MODE
    self.send_data(0x03)

  def wait_until_idle(self):
    while(self.digital_read(self.busy_pin) == 0):      # 0: busy, 1: idle
      self.delay_ms(100)

  def reset(self):
    self.digital_write(self.reset_pin, GPIO.LOW)         # module reset
    self.delay_ms(200)
    self.digital_write(self.reset_pin, GPIO.HIGH)
    self.delay_ms(200)

  def calibrate_display(self, no_of_cycles):
    """Function for Calibration"""
    
    if display_type == 'colour':
      packets = int(self.width / 2 * self.height)
    if display_type == 'black_and_white':
      packets = int(self.width / 4 * self.height)
    
    white, red, black = 0x33, 0x04, 0x00
    
    self.init()
    print('----------Started calibration of E-Paper display----------')
    for _ in range(no_of_cycles):
      self.send_command(DATA_START_TRANSMISSION_1)
      print('Calibrating black...')
      [self.send_data(black) for i in range(packets)]
      self.send_command(DISPLAY_REFRESH)
      self.wait_until_idle()
      
      if display_type == 'colour':
        print('Calibrating red...')
        self.send_command(DATA_START_TRANSMISSION_1)
        [self.send_data(red) for i in range(packets)]
        self.send_command(DISPLAY_REFRESH)
        self.wait_until_idle()

      print('Calibrating white...')
      self.send_command(DATA_START_TRANSMISSION_1)
      [self.send_data(white) for i in range(packets)]
      self.send_command(DISPLAY_REFRESH)
      self.wait_until_idle()

      print('Cycle {0} of {1} complete'.format(_+1, no_of_cycles))
      
    print('-----------Calibration complete----------')
    self.sleep()

  def reduce_colours(self, image):
    buffer = numpy.array(image)
    r,g,b = buffer[:,:,0], buffer[:,:,1], buffer[:,:,2]

    if display_type == "colour":
      buffer[numpy.logical_and(r <= 180, r == g)] = [0,0,0] #black
      buffer[numpy.logical_and(r >= 150, g >= 150)] = [255,255,255] #white
      buffer[numpy.logical_and(r >= 150, g <= 90)] = [255,0,0] #red

    image = Image.fromarray(buffer)
    return image

  def clear(self, colour='white'):
    if display_type == 'colour':
      packets = int(self.width / 2 * self.height)
    if display_type == 'black_and_white':
      packets = int(self.width / 4 * self.height)
    
    if colour == 'white': data = 0x33
    if colour == 'red': data = 0x04
    if colour == 'black': data = 0x00

    self.init()
    self.send_command(DATA_START_TRANSMISSION_1)
    [self.send_data(data) for _ in range(packets)]
    self.send_command(DISPLAY_REFRESH)
    print('waiting until E-Paper is not busy')
    self.delay_ms(100)
    self.wait_until_idle()
    print('E-Paper free')
    self.sleep()

  def get_frame_buffer(self, image):
    imwidth, imheight = image.size
    if imwidth == self.height and imheight == self.width:
      image = image.rotate(270, expand = True)
      print('Rotated image by 270 degrees...', end= '')
    elif imwidth != self.width or imheight != self.height:
      raise ValueError('Image must be same dimensions as display \
      ({0}x{1}).' .format(self.width, self.height))
    else:
      print('Image size OK')
    imwidth, imheight = image.size

    if display_type == 'colour':
      buf = [0x00] * int(self.width * self.height / 4)
      image_grayscale = image.convert('L')
      pixels = image_grayscale.load()

      for y in range(self.height):
        for x in range(self.width):
          # Set the bits for the column of pixels at the current position.
          if pixels[x, y] == 0: # black
            buf[int((x + y * self.width) / 4)] &= ~(0xC0 >> (x % 4 * 2))
          elif pixels[x, y] == 76: # convert gray to red
            buf[int((x + y * self.width) / 4)] &= ~(0xC0 >> (x % 4 * 2))
            buf[int((x + y * self.width) / 4)] |= 0x40 >> (x % 4 * 2)
          else:                           # white
            buf[int((x + y * self.width) / 4)] |= 0xC0 >> (x % 4 * 2)

    if display_type == 'black_and_white':
      buf = [0x00] * int(self.width * self.height / 8)
      image_monocolor = image.convert('1', dither = True)

      pixels = image_monocolor.load()
      for y in range(self.height):
        for x in range(self.width):
            # Set the bits for the column of pixels at the current position.
          if pixels[x, y] != 0:
            buf[int((x + y * self.width) / 8)] |= 0x80 >> (x % 8)

    return buf

  def display_frame(self, frame_buffer):
    self.send_command(DATA_START_TRANSMISSION_1)
    if display_type == 'colour':
      for i in range(0, int(self.width / 4 * self.height)):
        temp1 = frame_buffer[i]
        j = 0
        while (j < 4):
          if ((temp1 & 0xC0) == 0xC0):
            temp2 = 0x03 #white
          elif ((temp1 & 0xC0) == 0x00):
            temp2 = 0x00 #black
          else:
            temp2 = 0x04 #red
          temp2 = (temp2 << 4) & 0xFF
          temp1 = (temp1 << 2) & 0xFF
          j += 1
          if((temp1 & 0xC0) == 0xC0):
            temp2 |= 0x03 #white
          elif ((temp1 & 0xC0) == 0x00):
            temp2 |= 0x00 #black
          else:
            temp2 |= 0x04 #red
          temp1 = (temp1 << 2) & 0xFF
          self.send_data(temp2)
          j += 1

    if display_type == 'black_and_white':
      for i in range(0, 30720):
        temp1 = frame_buffer[i]
        j = 0
        while (j < 8):
          if(temp1 & 0x80):
            temp2 = 0x03 #white
          else:
            temp2 = 0x00 #black
          temp2 = (temp2 << 4) & 0xFF
          temp1 = (temp1 << 1) & 0xFF
          j += 1
          if(temp1 & 0x80):
            temp2 |= 0x03 #white
          else:
            temp2 |= 0x00 #black
          temp1 = (temp1 << 1) & 0xFF
          self.send_data(temp2)
          j += 1

    self.send_command(DISPLAY_REFRESH)
    self.delay_ms(100)
    self.wait_until_idle()

  def show_image(self, image, reduce_colours = True):
    print('Initialising E-Paper Display...', end='')
    self.init()
    sleep(5)
    print('Done')
    
    if reduce_colours == True:
      print('Optimising Image for E-Paper displays...', end = '')
      image = self.reduce_colours(image)
      print('Done')
    else:
      print('No colour optimisation done on image')

    print('Creating image buffer and sending it to E-Paper display...', end='')
    data = self.get_frame_buffer(image)
    print('Done')
    print('Refreshing display...', end = '')
    self.display_frame(data)
    print('Done')
    print('Sending E-Paper to deep sleep mode...',end='')
    self.sleep()
    print('Done')

  def sleep(self):
    self.send_command(POWER_OFF)
    self.wait_until_idle()
    self.send_command(DEEP_SLEEP)
    self.send_data(0xa5)
