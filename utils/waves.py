""" Handler file to generate AO waveoforms for USB DAQ MCCULW """
from utils.daq import McculwUsbDaq
import numpy as np
from scipy.signal import square
from mcculw.ul import from_eng_units
from utils.daq import DaqAI
import ctypes

import matplotlib.pyplot as plt

def waveform(
        waveform_type:str,
        daq:McculwUsbDaq,
        buffer,
        duration:int,
        sample_rate:int,
        amplitude:float,
        frequency:int):
    '''
        Adjust waveform in memory. Currently parameter waveform_type only supports 'sine' and 'square'.
    '''
    if not daq.daq_supports_ao:
        raise f"[ERROR] Daq does not support Analog Output: {daq.daq_product_name}"
    
    t = np.linspace(0, duration, sample_rate * duration, endpoint=False)
    if waveform_type == "sine":
        wave = amplitude * np.sin(2 * np.pi * frequency * t)
    elif waveform_type == "square":
        wave = amplitude * square(2 * np.pi * frequency * t)
    else:
        raise "[ERROR] Waveform only supports string 'sine' and 'square'. \n"

    for i, sample in enumerate(wave):
        raw_value = from_eng_units(board_num=daq.daq_board_num, ul_range=daq.daq_ao_range, eng_units_value=sample)
        buffer[i] = raw_value

def waveform_fast(
        daq:McculwUsbDaq,
        buffer,
        duration:int,
        sample_rate:int,
        a_max:float,
        a_min:float,
        frequency:int,
        mod_period:float):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Generate the original square wave: the square wave alternates between 1 and -1
    square_wave = np.sign(np.sin(2 * np.pi * frequency * t))

    # Create the square wave modulation envelope: alternate between 1.4 and 1.6 every 50 ms
    modulation_envelope = np.sign(np.sin(2 * np.pi * (1 / mod_period) * t))
    # Scale the envelope to oscillate between min_amplitude and max_amplitude
    modulation_envelope = (modulation_envelope + 1) / 2  # scale to [0, 1]
    modulation_envelope = modulation_envelope * (a_max - a_min) + a_min

    # Apply the amplitude modulation to the square wave
    modulated_wave = square_wave * modulation_envelope

    for i, sample in enumerate(modulated_wave):
        raw_value = from_eng_units(board_num=daq.daq_board_num, 
                                   ul_range=daq.daq_ao_range, 
                                   eng_units_value=sample)
        buffer[i] = raw_value

def waveform_single_char(
    daq:McculwUsbDaq,
    buffer,
    duration:int,
    sample_rate:int,
    a_max:float,
    a_min:float,
    frequency:int,
    mod_period:float,
    character:str):
    """ Builds a waveform in the AO buffer to represent a single character """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    square_wave = np.sign(np.sin(2 * np.pi * frequency * t))

    # Goal: build square wave in a way to represent binary value of char
    # We can divide the waveform into time slices representing 
    # the response rate of LC (based off switch speed plot).
    # Based off the plot, we can fit at most 12 bits per second.

    # First 350ms will carry the start bit to begin read
    # Each bit is 70ms wide (multiply by 2 since sample_freq is 20 kS/s)
    bit_width = mod_period # 0.030
    bit_pad = int(2 * bit_width * sample_rate)
    bit_window_start = 0
    bit_window_end = int(sample_rate*bit_width) + bit_pad
    square_wave[bit_window_start:bit_window_end] =a_max * square_wave[bit_window_start:bit_window_end]

    b_msg = bin(ord(character))[2:].zfill(8)
    for _ in range(2):
        for b in b_msg:
            # Shift the bit window by length of start to end
            bit_window_start = bit_window_end
            bit_window_end = bit_window_end + int(sample_rate * bit_width)
            # print(f"Window start: {bit_window_start} | Window end: {bit_window_end}")
            if b == '1':
                square_wave[bit_window_start:bit_window_end] = a_max * square_wave[bit_window_start:bit_window_end]
            else: # b == b'0'
                square_wave[bit_window_start:bit_window_end] = a_min * square_wave[bit_window_start:bit_window_end]
        bit_window_start = bit_window_end
        bit_window_end = bit_window_end + int(sample_rate * bit_width) + bit_pad
        square_wave[bit_window_start:bit_window_end] = a_max * square_wave[bit_window_start:bit_window_end]

        
        # Add start bit between characters
    square_wave[bit_window_start:] = (a_min/a_max) * square_wave[bit_window_start:]

    for i, sample in enumerate(square_wave):
        raw_value = from_eng_units(board_num=daq.daq_board_num, 
                                ul_range=daq.daq_ao_range, 
                                eng_units_value=sample)
        buffer[i] = raw_value

def waveform_single_char_2(
    daq:McculwUsbDaq,
    buffer,
    duration:int,
    sample_rate:int,
    a_max:float,
    a_min:float,
    frequency:int,
    mod_period:float,
    character:str):
    """ Builds a waveform in the AO buffer to represent a single character """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    square_wave = np.sign(np.sin(2 * np.pi * frequency * t))

    # Begin window
    bit_ini_wind = 0.05
    bit_ini = int(bit_ini_wind * sample_rate) # initialization bit
    mod_period = int(sample_rate * mod_period)
    square_wave[0:bit_ini] = a_min * square_wave[0:bit_ini]
    square_wave[bit_ini:(bit_ini + int(bit_ini_wind * sample_rate))] = a_max * square_wave[bit_ini:(bit_ini + int(bit_ini_wind * sample_rate))]
    bit_ini += int(bit_ini_wind * sample_rate)
    square_wave[bit_ini:(bit_ini + int(bit_ini_wind * sample_rate))] = a_min * square_wave[bit_ini:(bit_ini + int(bit_ini_wind * sample_rate))]
    
    bit_ini += int(bit_ini_wind * sample_rate)
    bit_start = bit_ini
    bit_stop = bit_start + mod_period

    b_msg = bin(ord(character))[2:].zfill(8)
    for b in b_msg:
        # print(bit_start , ' ', bit_stop)
        if b == '1':
            square_wave[bit_start:bit_stop] = a_min * square_wave[bit_start:bit_stop]
        else:
            square_wave[bit_start:bit_stop] = a_max * square_wave[bit_start:bit_stop]
        
        bit_start = bit_stop
        bit_stop = bit_start + mod_period

    # Add start bit between characters
    square_wave[bit_start:] = a_min * square_wave[bit_start:]

    for i, sample in enumerate(square_wave):
        raw_value = from_eng_units(board_num=daq.daq_board_num, 
                                ul_range=daq.daq_ao_range, 
                                eng_units_value=sample)
        buffer[i] = raw_value

def waveform_bvCurve(        
        daq:McculwUsbDaq,
        buffer,
        duration:int,
        sample_rate:int,
        a_max:float,
        frequency:int,
        mod_period:float):
    ''' Create a buffer which sweeps between a voltage range for BV Curve plots. '''

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    square_wave = np.sign(np.sin(2 * np.pi * frequency * t))
    v_step = np.arange(0, a_max, mod_period, dtype=float,)
    m_period = int(mod_period * sample_rate)

    square_wave = np.sign(np.sin(2 * np.pi * frequency * t))
    m_period = int((1/len(v_step)) * sample_rate)
    w_start = 0
    w_stop = m_period

    for v in v_step:
        square_wave[w_start:w_stop] = v * square_wave[w_start:w_stop]
        w_start = w_stop
        w_stop += m_period

    for i, sample in enumerate(square_wave):
        raw_value = from_eng_units(board_num=daq.daq_board_num, 
                                ul_range=daq.daq_ao_range, 
                                eng_units_value=sample)
        buffer[i] = raw_value
    # ctypes.memmove(buffer, square_wave.ctypes.data, square_wave.nbytes)


def plot_bvCurve(title:str, voltages, intensity:list):
    '''
        Plots Birefringence vs Voltage curve.
        NOTE: First collect AO and AI DAQ readings.

        Args:
            title: plot title
            voltages: np.linspace voltage array
            intensty: list of intensity values collected by AI
    '''
    plt.figure(figsize=(10, 4))
    plt.plot(voltages, intensity, marker='o')
    plt.title(title)
    plt.xlabel('Voltage')
    plt.ylabel('Intensity')
    plt.grid(True)
    plt.show()
    plt.xticks()

def plot_bvCurve_buffer(title:str, buffer:np.array):
    ''' Make sure to adjust voltage to max amplitude from buffer creation. '''
    v = np.arange(0, 6, 6/(len(buffer)), dtype=float)
    print(f"Len v: {len(v)} | Len Buff: {len(buffer)}")
    plt.figure(figsize=(10, 4))
    plt.scatter(v, buffer)
    plt.title(title)
    plt.xlabel('Voltage')
    plt.ylabel('Intensity')
    plt.grid(True)
    plt.show()
    plt.xticks()


def plot_switchSpeed(title:str, ao, ai):
    '''
    Args:
        title: Plot title
        ao: Analog output reading of a DAQ as measured by a ai channel of another DAQ
        ai: Intensity reading mesured by the Analog Input channel of a DAQ
    '''
    plt.figure(figsize=(10, 4))
    plt.plot(ao)
    plt.plot(ai)
    plt.title(title)
    plt.xlabel('Voltage')
    plt.ylabel('Intensity')
    plt.legend(['AO', 'LC'])
    plt.grid(True)
    plt.show()
    plt.xticks()

def plot_ai_buffer(title, ai_buffer:np.array, window=10):
    # rolling_avg = np.convolve(ai_buffer, np.ones(window), mode='valid') / window

    # t = np.linspace(0, DaqAI.DURAION.value, len(rolling_avg) * DaqAI.DURAION.value)
    t = np.linspace(0, DaqAI.DURAION.value, len(ai_buffer) * DaqAI.DURAION.value)

    plt.figure(figsize=(10, 4))
    plt.scatter(t, ai_buffer)
    plt.title(title)
    plt.xlabel('Time')
    plt.ylabel('Buffer Output')
    plt.grid(True)
    plt.show()
    plt.xticks()