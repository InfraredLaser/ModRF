"""
    Script used to receive byte string data from send.py
"""

from utils import daq, waves
from mcculw.enums import ScanOptions, FunctionType, Status
from mcculw import ul

from time import sleep
import subprocess, ctypes
import numpy as np
import zmq

# BIT_THRESH = daq.DaqAI.BIT_LOW.value + (daq.DaqAI.BIT_HIG.value - daq.DaqAI.BIT_LOW.value) / 2
BIT_THRESH = 1.35

def process_send():
        # Begin subprocess to start recv script
    try:
        process_s = subprocess.Popen(
            [r"env\Scripts\python", "send.py"]
            # stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE
            # text=True
            )
    except subprocess.CalledProcessError as e_sub:
        print(f"[ERROR]: Subprocess error: {e_sub}")

    print("[recv.py] Begin send.py subprocess.")
    # sleep(5)
    return process_s

def process_buf(buf:np.array):
    proc_buf = np.where(buf <= BIT_THRESH, 0, 1)
    s_f = daq.DaqAI.FREQ_SAMPLE.value
    b_str = b''
                    #  0     1     0     0     1     0     0     0 for H
    finite_window = [0.23, 0.31, 0.39, 0.46, 0.55, 0.63, 0.71, 0.79]
    for t in finite_window:
        b_str += b'1' if proc_buf[int(t*s_f)] == 1 else b'0'

    print(f'Received: {b_str} | {chr(int(b_str, 2))}')
    return proc_buf

def recv():
    # Create a TCP/IP socket
    try:
        context = zmq.Context()
        recv_socket = context.socket(zmq.REP)
        recv_socket.bind(f"tcp://*:{str(daq.Sockets.PORT.value)}")
        print(f"[recv.py] Created TCP/IP on {daq.Sockets.HOST.value}:{daq.Sockets.PORT.value}")
        process_s = process_send()

    except KeyboardInterrupt:
        print("Interrupt.")

    # Initialize devices
    devices = daq.configure_devices()
    usb_202 = daq.McculwUsbDaq(devices['USB-202'])

    # Set AI Range equal to AO range of send DAQ
    usb_202.set_daq_ai_range(0, daq.DaqAI.AI_RANGE.value)

    # Allocate buffer size for AI ADC
    memhandle_ai = ul.scaled_win_buf_alloc(daq.DaqAI.FREQ_SAMPLE.value)
    buff_ai = (ctypes.c_double * daq.DaqAI.FREQ_SAMPLE.value)()
    scan_options = (ScanOptions.BACKGROUND | ScanOptions.CONTINUOUS | ScanOptions.SCALEDATA)

    # Start background scan
    response = recv_socket.recv_string()
    print(f'{response}')

    try:
        daq.daq_ai_scan(usb_202, memhandle_ai, scan_options)
    except Exception as e_ai:
        print(f"[ERROR] [AI] {e_ai}\n")

    # Wait for USB_DAQ to initialize read
    status_ai = Status.RUNNING
    while status_ai == Status.IDLE:
        status_ai, _, _ = ul.get_status(usb_202.daq_board_num, FunctionType.AIFUNCTION)

    try:
        # Read buffer and parse for characters
        num_buf_processed = 0
        POINTS_TO_COPY = 0
        buf = []
        # messege = ['-', 'H', 'E', 'L', 'L', 'O', 'W']
        messege = 12
        while status_ai != Status.IDLE:
            for c in range(messege):
                # print(response)
                status_ai, num_pts_scanned, curr_idx = ul.get_status(usb_202.daq_board_num, FunctionType.AIFUNCTION)
                ul.scaled_win_buf_to_array(memhandle_ai, buff_ai, POINTS_TO_COPY, daq.DaqAI.FREQ_SAMPLE.value - POINTS_TO_COPY)
                buf = np.copy(buff_ai)
                buf = process_buf(buf)
                sleep(1)
            status_ai = Status.IDLE
        
        ul.stop_background(usb_202.daq_board_num, FunctionType.AIFUNCTION)
    except Exception as e:
        print(f"[recv.py] [ERROR]: Exception {e}\n")
    except KeyboardInterrupt:
        print("[recv.py] Exit process through interrupt.")
    finally:
        sleep(0.500)
        ul.win_buf_free(memhandle_ai)
        ul.stop_background(usb_202.daq_board_num, FunctionType.AIFUNCTION)
        usb_202.release_device()
        waves.plot_ai_buffer(f'buffer', buf)

if __name__ == '__main__':
    recv()