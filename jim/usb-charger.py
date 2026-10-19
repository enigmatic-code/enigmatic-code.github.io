#!/sw/bin/python2.7 -t
# -*- mode: Python; py-indent-offset: 2; -*-

from __future__ import print_function

import usb.core
import time

ID_VENDOR = 0x1b47
ID_PRODUCT = 0x1

class Charger(object):

  def __init__(self, idVendor=ID_VENDOR, idProduct=ID_PRODUCT):
    self.idVendor = idVendor
    self.idProduct = idProduct
    self.device = None
    self.endpt = None

  def connect(self):
    # find the device
    self.device = usb.core.find(idVendor=self.idVendor, idProduct=self.idProduct)
    if self.device is None: return False
    # use the first/default configuration
    self.device.set_configuration()
    # first endpoint
    self.endpt = self.device[0][(0, 0)][0]
    return True

  def data(self):
    try:
      b = self.device.read(self.endpt.bEndpointAddress, self.endpt.wMaxPacketSize)
    except usb.core.USBError as e:
      return None
    
    # the data is 3, 16 bit values and two 8 bit values
    raw = ((b[0] << 8) + b[1], (b[2] << 8) + b[3], (b[4] << 8) + b[5], b[6], b[7])
    data = { 'raw': raw }
    # charge: slot 1 / slot 2 (possibly in steps of (3.3/1024) volts)
    # AA batteries (2000mAh) charge to about 458.
    # AAA batteries (800mAh) charge to about 459.
    data['ch1'] = raw[0]
    data['ch2'] = raw[1]
    # active: on = 1 / off = 0
    data['active'] = raw[4]
    # battery type: AA / AAA
    if raw[2] == 0xc382: data['type'] = 'AA'
    elif raw[2] == 0x452e: data['type'] = 'AAA'
    else: data['type'] = '<unknown type>'
    # slots: 0 = slot 1 only / 1 = slot 1 + slot 2 (bit 0)
    data['slots'] = (raw[3] & 0b00000001)
    # mode: (not sure about this) 1 = AAA, 0 = AA (or high/low charge?) (bit 1)
    data['mode'] = (raw[3] & 0b00000010) >> 1
    # (bit 2 and 3 always seem to be 0)
    # error: (bit 4)
    data['error'] = (raw[3] & 0b00010000) >> 4
    # (bit 5 always seems to be 0)
    # state: 01 = charging / 10 = full / 11 = error (bit 7 and 6)
    data['state'] = (raw[3] & 0b11000000) >> 6
    # make a useful message
    ms = []
    if data['active']:
      ms.append(('<unknown state>', 'charging', 'charged', 'error')[data['state']])
      ms.append(('slot 1', 'slot 1+2')[data['slots']])
      ms.append(data['type'])
      #ms.append('mode ' + ('0', '1')[data['mode']])
      if data['error']: ms.append('error')
      ms.append('ch1=' + str(data['ch1']))
      if data['slots'] == 1: ms.append('ch2=' + str(data['ch2']))
    else:
      ms = ['inactive']
    data['message'] = '; '.join(ms)
    return data

def main():
  charger = Charger()
  if not charger.connect():
    print("device not found")
    return

  while True:
    data = charger.data()
    if data is None:
      print("device disconnected")
      return
    #print(data['raw'])
    print(time.strftime('[%H:%M:%S]'), data['message'])
    time.sleep(10.0)

if __name__ == '__main__':
  main()
