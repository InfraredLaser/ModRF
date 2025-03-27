""" Handler file to generate AO waveoforms for USB DAQ MCCULW """
from utils.daq import McculwUsbDaq
from numpy import linspace, pi, sin
from scipy.signal import square
from mcculw.ul import from_eng_units

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
    
    t = linspace(0, duration, sample_rate * duration, endpoint=False)
    if waveform_type == "sine":
        wave = amplitude * sin(2 * pi * frequency * t)
    elif waveform_type == "square":
        wave = amplitude * square(2 * pi * frequency * t)
    else:
        raise "[ERROR] Waveform only supports string 'sine' and 'square'. \n"

    for i, sample in enumerate(wave):
        raw_value = from_eng_units(board_num=daq.daq_board_num, ul_range=daq.daq_ao_range, eng_units_value=sample)
        buffer[i] = raw_value

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