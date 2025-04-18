"""
    Utility script for DAQ handeling.
"""

from mcculw import ul
from mcculw.enums import InterfaceType, ULRange, InfoType, BoardInfo, ULRangeEnum
from mcculw.device_info import DaqDeviceInfo

from typing import Dict, List
from enum import IntEnum, Enum

import configparser
config = configparser.ConfigParser()
config.read('daq_config.ini')

class DaqAO(Enum):
    CHAN_LOW    = int(config['DaqAO']['chan_low'])
    CHAN_HIG    = int(config['DaqAO']['chan_hig'])
    AMPLITUDE   = int(config['DaqAO']['amplitude'])
    FREQ_SAMPLE = int(config['DaqAO']['freq_sample'])
    DURAION     = int(config['DaqAO']['duration'])
    AO_RANGE    = ULRange[str(config['DaqAO']['ao_range'])]
    NUM_CHANS   = CHAN_HIG - CHAN_LOW + 1

class DaqAI(Enum):
    CHAN_LOW    = int(config['DaqAI']['chan_low'])
    CHAN_HIG    = int(config['DaqAI']['chan_hig'])
    FREQ_SAMPLE = int(config['DaqAI']['freq_sample'])
    DURAION     = int(config['DaqAI']['duration'])
    AI_RANGE    = ULRange[str(config['DaqAI']['ai_range'])]
    NUM_CHANS   = CHAN_HIG - CHAN_LOW + 1
    BIT_LOW     = float(config['DaqAI']['bit_low'])
    BIT_HIG     = float(config['DaqAI']['bit_hig'])

class LC(Enum):
    V_ON    = float(config['LC']['v_on'])
    V_OFF   = float(config['LC']['v_off'])
    FREQ_LC = int(config['LC']['freq_lc'])

class Sockets(Enum):
    HOST = str(config['Socket']['host'])
    PORT = int(config['Socket']['port'])

def configure_devices(printDevices=False) -> Dict:
    '''
        Assign DAQ's to device nubers.

        MCCULW Python interface (ul) assigns connected devices to board numbers.
        ex/ USB-3101FS (2128658) - Device ID = 224 -> referenced with board num 0.

        DAQ Devices can then be commanded with board number as reference.

        Return:
            list of device names to keep track of assigned board num as index in list.
    '''
    ul.ignore_instacal()
    devices:List[ul.DaqDeviceDescriptor] = ul.get_daq_device_inventory(InterfaceType.USB)

    if not devices:
        raise Exception("ERROR: No USB DAQ devices connected")

    connected_devices = {}
    if printDevices:
        print(f"\nConfiguring {len(devices)} USB DAQs. ")
    for board_num, device in enumerate(devices):
        if printDevices:
            print(f"Board Number: {board_num} | {device.product_name}")
        connected_devices[device.product_name] = board_num
        ul.create_daq_device(board_num, device)
    print()

    return connected_devices

class McculwUsbDaq():
    ''' 
        Handler class for USB DAQ Devices.
        After running configure_devices, pass board_num to initialize class.
    '''
    def __init__(self, daq_board_num:int):
        self._daq_dev_info = DaqDeviceInfo(daq_board_num)
        # Sometimes USB DAQ's do not have AO or AI
        # Used for universal range getter.
        if (
            self._daq_dev_info.supports_analog_output and
            self._daq_dev_info.supports_analog_input
            ):
            self._daq_ao_info  = self._daq_dev_info.get_ao_info()
            self._daq_ai_info  = self._daq_dev_info.get_ai_info()
            self._daq_ao_range = self._daq_ao_info.supported_ranges[0]
            self._daq_ai_range = self._daq_ai_info.supported_ranges[0]
        elif self._daq_dev_info.supports_analog_output:
            self._daq_ao_info  = self._daq_dev_info.get_ao_info()
            self._daq_ao_range = self._daq_ao_info.supported_ranges[0]
            self._daq_ai_info  = None
            self._daq_ai_range = None
        else: # supports only AI
            self._daq_ao_info  = None
            self._daq_ao_range = None
            self._daq_ai_info  = self._daq_dev_info.get_ai_info()
            self._daq_ai_range = self._daq_ai_info.supported_ranges[0]
    
    @property
    def daq_board_num(self):
        return self._daq_dev_info.board_num
    
    @property
    def daq_product_name(self):
        return self._daq_dev_info.product_name
    
    @property
    def daq_unique_id(self):
        return self._daq_dev_info.unique_id
    
    @property
    def daq_supports_ao(self):
        return self._daq_dev_info.supports_analog_output
    
    @property
    def daq_supports_ai(self):
        return self._daq_dev_info.supports_analog_input
    
    @property
    def daq_ao_range(self):
        if self.daq_supports_ao:
            return self._daq_ao_range
        else:
            raise f"[ERROR] DAQ {self.daq_product_name} does not support AO.\n"
        
    def set_daq_ao_range(self, daq_chan:int, new_range:ULRange, verbose=False):
        """
            Change DAQ range to new range value.
            NOTE: First read DAQ manual to know of configurable ranges.

            Args:
                daq_chan: Channel number on DAQ to modify range.
                new_range: Enum value from mcculw enums module.

            Example:
                Want to change range from unipolar 10V to bipolar 10V on channel 0.
                daq_chan = 0
                new_range = enums.ULRange.BIP10VOLTS
        """
        if daq_chan > self._daq_ao_info.num_chans or daq_chan < 0:
            raise f"[ERROR] Can't assign range to daq_chan: {daq_chan} | {self.daq_product_name} has {self._daq_ao_info.num_chans} chans.\n"
        
        if verbose:
            print(f"Current {self.daq_product_name} range: {ULRange(self.daq_ao_range).name}")
        ul.set_config(
            info_type=InfoType.BOARDINFO,
            board_num=self.daq_board_num,
            dev_num=daq_chan,
            config_item=BoardInfo.DACRANGE,
            config_val=new_range
        )
        if verbose:
            print(f"New DAQ range: {ULRange(self.daq_ao_range).name}")
    
    @property
    def daq_ai_range(self):
        if self.daq_supports_ai:
            return self._daq_ai_range
        else:
            raise f"[ERROR] DAQ {self.daq_product_name} does not support AI.\n"
    
    #@daq_ai_range.setter
    def set_daq_ai_range(self, daq_chan:int, new_range:ULRange, verbose=False) -> None:
        """
            Change DAQ range to new range value.
            NOTE: First read DAQ manual to know of configurable ranges.

            Args:
                daq_chan: Channel number on DAQ to modify range.
                new_range: Enum value from mcculw enums module.

            Example:
                Want to change range from unipolar 10V to bipolar 10V on channel 0.
                daq_chan = 0
                new_range = enums.ULRange.BIP10VOLTS
        """
        if daq_chan > self._daq_ai_info.num_chans or daq_chan < 0:
            raise f"[ERROR] Can't assign range to daq_chan: {daq_chan} | {self.daq_product_name} has {self._daq_ai_info.num_chans} chans.\n"
        
        if verbose:
            print(f"Current {self.daq_product_name} range: {ULRange(self.daq_ai_range).name}")
        ul.set_config(
            info_type=InfoType.BOARDINFO,
            board_num=self.daq_board_num,
            dev_num=daq_chan,
            config_item=BoardInfo.DACRANGE,
            config_val=new_range
        )
        if verbose:
            print(f"New DAQ range: {ULRange(self.daq_ai_range).name}")

    def release_device(self):
        """ Safely release device from script exit. """
        print(f"Released device {self.daq_product_name}")
        ul.release_daq_device(self.daq_board_num)

#__________________ Scan Operations ______________________________________________

def daq_ao_scan(usb_daq:McculwUsbDaq, memhandle, options):
    ''' Handle function to begin an output scan '''
    ul.a_out_scan(
        board_num=usb_daq.daq_board_num,
        low_chan=DaqAO.CHAN_LOW.value,
        high_chan=DaqAO.CHAN_HIG.value,
        num_points=DaqAO.FREQ_SAMPLE.value * DaqAO.DURAION.value * DaqAO.NUM_CHANS.value,
        rate=DaqAO.FREQ_SAMPLE.value,
        ul_range=DaqAO.AO_RANGE.value,
        memhandle=memhandle,
        options=options
    )

def daq_ai_scan(usb_daq:McculwUsbDaq, memhandle, options):
    ''' Handle function to begin AI scan '''
    ul.a_in_scan(
        board_num=usb_daq.daq_board_num,
        low_chan=DaqAI.CHAN_LOW.value,
        high_chan=DaqAI.CHAN_HIG.value,
        num_points=DaqAI.FREQ_SAMPLE.value * DaqAI.DURAION.value * DaqAI.NUM_CHANS.value,
        rate=DaqAI.FREQ_SAMPLE.value,
        ul_range=DaqAI.AI_RANGE.value,
        memhandle=memhandle,
        options=options
    )

if __name__ == "__main__":
    d = configure_devices()
    usb_3101fs = d['USB-3101FS']