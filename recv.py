"""
    Script used to receive byte string data from send.py
"""

from utils import daq
from mcculw.enums import ScanOptions, FunctionType, Status
from mcculw import ul
from ctypes import cast, POINTER, c_ulong
from time import sleep
import os, subprocess, binascii

# AI Configuration for USB DAQ
LOW_CHAN = 0
HIG_CHAN = 0 #min(3, ao_info.num_chans - 1)
NUM_CHANS = HIG_CHAN - LOW_CHAN + 1
S_F = 1_00    # Sample rate or freq
D = 1           # Duration
DAQ_RANGE = daq.ULRange.BIP10VOLTS
V1 = 1.40
V2 = 1.60

# Get the current environment and add Python environment variables if needed
env = os.environ.copy()
env['PYTHONPATH'] = r"env\Scripts\python"  # Add current directory to PYTHONPATH

def process_send():
        # Begin subprocess to start recv script
    try:
        process_s = subprocess.Popen(
            [r"env\Scripts\python", "send.py"],
            # stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
            # text=True
            )
    except subprocess.CalledProcessError as e_sub:
        print(f"[ERROR]: Subprocess error: {e_sub}")

    print("\nBeginning subprocess send.py")
    print("Wait some time for send.py script to initialize...")
    sleep(3)

    # for line in process_s.stderr:
    #     print(f"[STDOUT]: {line}")

    return process_s

def recv():
    # Start send.py
    process_s = process_send()

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
    comms = b''
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
                    
                    v_round = round(eng_value, 1)
                    # print(f"AI: {v_round:0.2f}", end="\r")
                    if len(comms) == 8:
                        #print(binascii.b2a_uu(comms))
                        print(f"\rreceived char: {chr(int(comms, 2))}", end='')
                        comms = b''

                    if v_round >= 2.75:
                        #print(f"\rbin: 1", end="")
                        comms += b'1'
                    elif v_round <= 2.75 and v_round >= 2.3:
                        #print(f"\rbin: 0", end="")
                        comms += b'0'
                    else:
                        continue

            # Wait a while before adding more values to the display.
            sleep(0.100)
            status, curr_count, curr_index = ul.get_status(usb_202.daq_board_num, FunctionType.AIFUNCTION)
            i+=1

        ul.stop_background(usb_202.daq_board_num, FunctionType.AIFUNCTION)
        print('Finished Buffer')
        print("Scan end...")
    except Exception as e:
        print(f"[ERROR]: Exception {e}\n")
    except KeyboardInterrupt:
        print("Exit process through interrupt.")
    finally:
        sleep(0.100)
        ul.win_buf_free(memhandle)
        usb_202.release_device()
        process_s.terminate()

if __name__ == '__main__':
    recv()