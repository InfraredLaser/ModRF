"""
    Script to send communication for recv.py to process.
"""
from utils import daq, waves
from mcculw.ul import a_out_scan, win_buf_alloc, win_buf_free
from mcculw.enums import ScanOptions
from ctypes import cast, POINTER, c_ushort
from time import sleep

MSG = "H"       # Message
LOW_CHAN = 0
HIG_CHAN = 0 #min(3, ao_info.num_chans - 1)
NUM_CHANS = HIG_CHAN - LOW_CHAN + 1
A = 1           # Amplitude
F =  200        # Frequency
S_F = 20_000    # Sample rate or freq
D = 1           # Duration
DAQ_RANGE = daq.ULRange.BIP10VOLTS

# LC Drive
V1 = 1.40 # High, 1
V2 = 1.60 # Low, 0

def send():

    # Initialize devices
    print("initialize AO Device...")
    devices    = daq.configure_devices()
    usb_3101fs = daq.McculwUsbDaq(devices['USB-3101FS'])

    # Set AO range equal to AI range on read DAQ
    usb_3101fs.set_daq_ao_range(0, DAQ_RANGE)

    # Initialize AO Buffer
    memhandle    = win_buf_alloc(S_F * D * NUM_CHANS)
    ao_buffer    = cast(memhandle, POINTER(c_ushort))
    scan_options = (ScanOptions.BACKGROUND | ScanOptions.CONTINUOUS)

    waves.waveform('square', usb_3101fs, ao_buffer, D, S_F, 0, F)
    sleep(0.2)
    print('Beginning scan...')

    try:
        a_out_scan(
            board_num=usb_3101fs.daq_board_num,
            low_chan=LOW_CHAN, 
            high_chan=HIG_CHAN, 
            num_points=S_F * D * NUM_CHANS, 
            rate=S_F, 
            ul_range=usb_3101fs.daq_ao_range, 
            memhandle=memhandle, 
            options=scan_options
        )
        try:
            while(True):
                b_msg = bin(ord(MSG))[2:]
                for b in b_msg:
                    if b == str(1):
                        waves.waveform('square', usb_3101fs, ao_buffer, D, S_F, V1, F)
                    else: # b == 0
                        waves.waveform('square', usb_3101fs, ao_buffer, D, S_F, V2, F)
                    sleep(0.100)
                sleep(0.5)
        except KeyboardInterrupt:
            print('Interrupt')

    except Exception as e:
        print(f'[ERROR]: {e}\n')
    finally:
        waves.waveform('square', usb_3101fs, ao_buffer, D, S_F, 0, F)
        sleep(0.1)
        win_buf_free(memhandle)
        usb_3101fs.release_device()

if __name__ == "__main__":
    send()