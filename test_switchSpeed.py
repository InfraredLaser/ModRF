"""
    Script to test switch speed of Liquid Crystal's (LC)
    using Measurement Computing DAC and ADC (both are abbriviated general to DAQ).
"""
from utils.daq import configure_devices, daq_ao_scan, daq_ai_scan, McculwUsbDaq, DaqAO, DaqAI, LC
from utils import waves
from mcculw import ul
from mcculw.enums import ScanOptions, FunctionType, Status
import ctypes
from time import sleep
import threading
import numpy as np

def daq_wf_ao_amplitude(usb_daq:McculwUsbDaq, buffer, amplitude:float):
    ''' Handle function to change amplitude of a waveform ao buffer '''
    waves.waveform(
        waveform_type='square',
        daq=usb_daq,
        buffer=buffer,
        duration=DaqAO.DURAION.value,
        sample_rate=DaqAO.FREQ_SAMPLE.value,
        amplitude=amplitude,
        frequency=LC.FREQ_LC.value
    )

def daq_ao_waveform_fast(usb_daq:McculwUsbDaq, buffer):
    waves.waveform_fast(
        daq=usb_daq,
        buffer=buffer,
        duration=DaqAO.DURAION.value,
        sample_rate=DaqAO.FREQ_SAMPLE.value,
        a_max=LC.V_OFF.value,
        a_min=LC.V_ON.value,
        frequency=LC.FREQ_LC.value,
        mod_period=0.080 #ms 
    )

def daq_ao_waveform_single_char(usb_daq:McculwUsbDaq, buffer, character:str):
    waves.waveform_single_char_2(
        daq=usb_daq,
        buffer=buffer,
        duration=DaqAO.DURAION.value,
        sample_rate=DaqAO.FREQ_SAMPLE.value,
        a_max=LC.V_OFF.value,
        a_min=LC.V_ON.value,
        frequency=LC.FREQ_LC.value,
        mod_period=0.080, #ms
        character = character
    )

def lc_modulation(usb_daq:McculwUsbDaq, buffer_ao):
    SLEEP_TIME = 2
    try:
        for _ in range(3):
            daq_ao_waveform_single_char(usb_daq, buffer_ao, "H")
            sleep(SLEEP_TIME)

    except KeyboardInterrupt or Exception:
        print(f"[ERROR] [Thred] Interrupt\n")
        daq_wf_ao_amplitude(usb_daq, buffer_ao, 0)
    daq_wf_ao_amplitude(usb_daq, buffer_ao, 0)

def bvCurve():
    # Initialize devices
    devices    = configure_devices()
    usb_202    = McculwUsbDaq(devices['USB-202'])
    usb_3101fs = McculwUsbDaq(devices['USB-3101FS'])

    # Set both device to the same range
    usb_202.set_daq_ai_range(0, DaqAI.AI_RANGE.value)
    usb_3101fs.set_daq_ao_range(0, DaqAO.AO_RANGE.value)

    # Initialize memory buffers and windows buffer handling
    memhandle_ao = ul.win_buf_alloc(DaqAO.FREQ_SAMPLE.value)
    memhandle_ai = ul.scaled_win_buf_alloc(DaqAI.FREQ_SAMPLE.value)
    if not memhandle_ao:
        raise Exception('[Error] [AO] Memory allocation.')
    if not memhandle_ai:
        raise Exception('[Error] [AI] Memory allocation.')
    
    buff_ai = (ctypes.c_double * DaqAI.FREQ_SAMPLE.value)()
    buff_ao = ctypes.cast(memhandle_ao, ctypes.POINTER(ctypes.c_ushort))

    # Set device scan options to constantly scan for background
    options_ao = (ScanOptions.BACKGROUND | ScanOptions.CONTINUOUS)
    options_ai = (ScanOptions.BACKGROUND | ScanOptions.CONTINUOUS | ScanOptions.SCALEDATA)

    # Initialize AO buffer handle
    # Amplitude first set to 0 as DAQ inital voltage is set to lowest value in range (-10 V)
    daq_wf_ao_amplitude(usb_3101fs, buff_ao, 0)
    sleep(0.1)
    thread_lc_mod = threading.Thread(target=lc_modulation, args=(usb_3101fs, buff_ao,))

    # Begin AO scan
    try:
        daq_ao_scan(usb_3101fs, memhandle_ao, options_ao)
    except Exception as e_ao:
        print(f"[ERROR] [AO] {e_ao}\n")

    # Begin AI scan
    try:
        daq_ai_scan(usb_202, memhandle_ai, options_ai)
    except Exception as e_ai:
        print(f"[ERROR] [AI] {e_ai}\n")

    # Begin taking data from AI device
    status_ai = Status.RUNNING
    while status_ai == Status.IDLE:
        status_ai, _, _ = ul.get_status(usb_202.daq_board_num, FunctionType.AIFUNCTION)

    # Start cell modulation
    thread_lc_mod.start()
    try:
        num_buf_processed = 0
        POINTS_TO_COPY = 0
        buf = []
        while status_ai != Status.IDLE:
            status_ai, num_pts_scanned, curr_idx = ul.get_status(usb_202.daq_board_num, FunctionType.AIFUNCTION)

            # A single buffer is the size of the sample frequency
            if (num_pts_scanned % DaqAI.FREQ_SAMPLE.value) == 0:
                num_buf_processed += 1
                if num_buf_processed == 2:
                    # Copy entire buffer into the AI buffer 
                    ul.scaled_win_buf_to_array(memhandle_ai, buff_ai, POINTS_TO_COPY, DaqAI.FREQ_SAMPLE.value - POINTS_TO_COPY)
                    buf = np.copy(buff_ai)
                    print(len(buf))
                    status_ai = Status.IDLE

    except KeyboardInterrupt:
        print('Interrupt')
    except Exception as e_daq:
        print(f"[Error] [DAQ] {e_daq}\n")
    finally:
        thread_lc_mod.join()
        daq_wf_ao_amplitude(usb_3101fs, buff_ao, 0)
        sleep(0.1)
        ul.win_buf_free(memhandle_ai)
        ul.win_buf_free(memhandle_ao)
        sleep(0.1)
        usb_202.release_device()
        usb_3101fs.release_device()
        waves.plot_ai_buffer(f'Switch Speed: Sample LC', buf, window=5)
    
if __name__ == "__main__":
    bvCurve()