"""
    Script is used to to test the buffer of USB DAQ 202
"""

from utils import daq
import numpy as np
import ctypes, time
from mcculw import ul
from mcculw.enums import ScanOptions, FunctionType, Status

# AI Configuration for USB DAQ
S_F = 100    # Sample rate or freq, ul_buffer_count
DAQ_RANGE = daq.ULRange.BIP10VOLTS
BIT_HIGH = 1.10
BIT_LOW  = 0.10
BIT_THRESH = BIT_LOW + (BIT_HIGH - BIT_LOW) / 2

def buff():
    devices = daq.configure_devices()
    usb_202 = daq.McculwUsbDaq(devices['USB-202'])
    usb_202.set_daq_ai_range(0, DAQ_RANGE)
    memhandle = ul.scaled_win_buf_alloc(S_F)
    c_array = (ctypes.c_double * S_F)()
    scan_options = (ScanOptions.BACKGROUND | ScanOptions.CONTINUOUS | ScanOptions.SCALEDATA)

    ul.a_in_scan(
        board_num=usb_202.daq_board_num,
        low_chan=0,
        high_chan=0,
        num_points=S_F,
        rate=S_F,
        ul_range=usb_202.daq_ai_range,
        memhandle=memhandle,
        options=scan_options
    )
    status = Status.IDLE
    # Wait for the scan to start fully
    while status == Status.IDLE:
        status, _, _ = ul.get_status(usb_202.daq_board_num, FunctionType.AIFUNCTION)

    try:    
        prev_index, prev_count = 0, 0
        points_to_check = 0
        b_msg = b''
        SAMPLES_TO_WRITE = S_F - 1
        while status != Status.IDLE:
            status, curr_count, curr_idx = ul.get_status(usb_202.daq_board_num, FunctionType.AIFUNCTION)

            if curr_idx == 0:
                # print(f"data | curr_count: {curr_count}, curr_idx: {curr_idx}, prev_idx: {prev_index}")
                ul.scaled_win_buf_to_array(memhandle, c_array, curr_idx, S_F)
                # print(f"Buff values:\n{np.round(c_array[0:SAMPLES_TO_WRITE], 2)}")
                processed_buff = [1 if x > BIT_THRESH else 0 for x in c_array]

                if processed_buff[0] == 1:
                    b_msg += b'1'
                else:
                    b_msg += b'0'
            
                if len(b_msg) == 8:
                    print(f"{b_msg} | char: {chr(int(b_msg, 2))}", end='\n')
                    b_msg = b''

                time.sleep(0.2)

    except KeyboardInterrupt:
        print("Exit via interrupt.\n")
    finally:
        ul.win_buf_free(memhandle)
        usb_202.release_device()


if __name__ == "__main__":
    buff()