"""
    Script used to receive byte string data from send.py
"""

from utils import daq
from mcculw.enums import ScanOptions, FunctionType, Status
from mcculw import ul
from ctypes import cast, POINTER, c_ulong
from time import sleep

# AI Configuration for USB DAQ
LOW_CHAN = 0
HIG_CHAN = 0 #min(3, ao_info.num_chans - 1)
NUM_CHANS = HIG_CHAN - LOW_CHAN + 1
S_F = 1_00    # Sample rate or freq
D = 1           # Duration
DAQ_RANGE = daq.ULRange.BIP10VOLTS
V1 = 1.4
V2 = 1.6
def recv():
    devices = daq.configure_devices()
    usb_202 = daq.McculwUsbDaq(devices['USB-202'])
    usb_202.set_daq_ai_range(0, DAQ_RANGE)

    memhandle = ul.win_buf_alloc(S_F * D * NUM_CHANS)
    ctypes_array = cast(memhandle, POINTER(c_ulong))
    scan_options = (ScanOptions.BACKGROUND | ScanOptions.CONTINUOUS)

    # Start scan
    ul.a_in_scan(
        board_num=usb_202.daq_board_num,
        low_chan=LOW_CHAN,
        high_chan=HIG_CHAN,
        num_points=S_F*D*NUM_CHANS,
        rate=S_F,
        ul_range=usb_202.daq_ai_range,
        memhandle=memhandle,
        options=scan_options
    )
    i=0
    status, curr_count, curr_index = ul.get_status(usb_202.daq_board_num, FunctionType.AIFUNCTION)
    print('Start Scan...')
    try:
        while status != Status.IDLE:
            if curr_count > 0:
                for data_index in range(0, curr_index + NUM_CHANS):
                    if ScanOptions.SCALEDATA in scan_options:
                        # If the SCALEDATA ScanOption was used, the values
                        # in the array are already in engineering units.
                        eng_value = ctypes_array[data_index]
                    else:
                        # If the SCALEDATA ScanOption was NOT used, the
                        # values in the array must be converted to
                        # engineering units using ul.to_eng_units().
                        eng_value = ul.to_eng_units(
                            usb_202.daq_board_num, 
                            usb_202.daq_ai_range,
                            ctypes_array[data_index]
                        )
                    if round(eng_value, 1) >= V1 and round(eng_value, 1) <= V2:
                        print(f"{i} V1 | AI: {eng_value}")
                    
                    if round(eng_value, 1) >= V2:
                        print(f"{i} V2 | AI: {eng_value}")
            # Wait a while before adding more values to the display.
            sleep(0.100)
            status, curr_count, curr_index = ul.get_status(usb_202.daq_board_num, FunctionType.AIFUNCTION)
            i+=1

        ul.stop_background(usb_202.daq_board_num, FunctionType.AIFUNCTION)
        print('Finished Buffer')
        print("Scan end...")
    except Exception as e:
        print(f"[ERROR]: Exception {e}\n")
    finally:
        sleep(0.100)
        ul.win_buf_free(memhandle)
        usb_202.release_device()

if __name__ == '__main__':
    recv()