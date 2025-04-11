"""
    Script to send communication for recv.py to process. (subprocess for recv.py)
"""
from utils import daq, waves
from mcculw.ul import a_out_scan, win_buf_alloc, win_buf_free, stop_background
from mcculw.enums import ScanOptions, FunctionType
from ctypes import cast, POINTER, c_ushort
from time import sleep
import sys, zmq

def daq_wf_ao_amplitude(usb_daq:daq.McculwUsbDaq, buffer, amplitude:float):
    ''' Handle function to change amplitude of a waveform ao buffer '''
    waves.waveform(
        waveform_type='square',
        daq=usb_daq,
        buffer=buffer,
        duration=daq.DaqAO.DURAION.value,
        sample_rate=daq.DaqAO.FREQ_SAMPLE.value,
        amplitude=amplitude,
        frequency=daq.LC.FREQ_LC.value
    )
def daq_ao_waveform_single_char_2(usb_daq:daq.McculwUsbDaq, buffer, character:str):
    waves.waveform_single_char_2(
        daq=usb_daq,
        buffer=buffer,
        duration=daq.DaqAO.DURAION.value,
        sample_rate=daq.DaqAO.FREQ_SAMPLE.value,
        a_max=daq.LC.V_OFF.value,
        a_min=daq.LC.V_ON.value,
        frequency=daq.LC.FREQ_LC.value,
        mod_period=0.080, #ms
        character = character
    )

def daq_ao_waveform_bvCurve(usb_daq:daq.McculwUsbDaq, buffer):
    waves.waveform_bvCurve(
        daq=usb_daq,
        buffer=buffer,
        duration=daq.DaqAO.DURAION.value,
        sample_rate=daq.DaqAO.FREQ_SAMPLE.value,
        a_max=6,
        frequency=daq.LC.FREQ_LC.value,
        mod_period=0.080, #ms
    )

def send():
    # Create a TCP/IP socket
    try:
        context = zmq.Context()
        send_socket = context.socket(zmq.REQ)
        send_socket.connect(f"tcp://localhost:{str(daq.Sockets.PORT.value)}")
        print(f"[send.py] Connecting to {daq.Sockets.HOST.value}:{daq.Sockets.PORT.value}")
    except Exception as e:
        print(f"{e}")

    # Initialize devices
    devices    = daq.configure_devices()
    usb_3101fs = daq.McculwUsbDaq(devices['USB-3101FS'])
    
    # Set AO range equal to AI range on read DAQ
    usb_3101fs.set_daq_ao_range(0, daq.DaqAO.AO_RANGE.value)

    # Initialize AO Buffer
    NUM_CHANS    = daq.DaqAO.CHAN_HIG.value - daq.DaqAO.CHAN_LOW.value + 1
    memhandle    = win_buf_alloc(daq.DaqAO.FREQ_SAMPLE.value * daq.DaqAO.DURAION.value * NUM_CHANS)
    ao_buffer    = cast(memhandle, POINTER(c_ushort))
    scan_options = (ScanOptions.BACKGROUND | ScanOptions.CONTINUOUS)

    send_socket.send_string('[send.py] Initialized AO. Begin AO scan.')
    try:
        daq.daq_ao_scan(usb_daq=usb_3101fs,
                        memhandle=memhandle, 
                        options=scan_options
        )
    except Exception as e_ao:
        print(f"[ERROR] [AO] {e_ao}\n")
    
    try:
        SLEEP_STEP = 1
        # messege = ['P', 'P']
        # messege = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        messege = "Hello World"
        # messege = " "
        for c in messege:
            # daq_ao_waveform_single_char_2(usb_3101fs, ao_buffer, c)
            daq_ao_waveform_single_char_2(usb_3101fs, ao_buffer, c)
            sleep(SLEEP_STEP)

        daq_wf_ao_amplitude(usb_3101fs, ao_buffer, 0)
        sleep(SLEEP_STEP)
        
    except KeyboardInterrupt:
        print('Interrupt')
    except Exception as e:
        print(f'[ERROR]: {e}\n')
    finally:
        daq_wf_ao_amplitude(usb_3101fs, ao_buffer, 0)
        sleep(0.3)
        win_buf_free(memhandle)
        stop_background(usb_3101fs.daq_board_num, FunctionType.AOFUNCTION)
        usb_3101fs.release_device()

if __name__ == "__main__":
    send()