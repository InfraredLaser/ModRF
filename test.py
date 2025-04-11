import numpy as np
from utils import daq
import matplotlib.pyplot as plt

duration = 1
sample_rate = daq.DaqAO.FREQ_SAMPLE.value
frequency = daq.LC.FREQ_LC.value
character = 'H'
a_max = daq.LC.V_OFF.value
a_min = daq.LC.V_ON.value

t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
square_wave = np.sign(np.sin(2 * np.pi * frequency * t))

# Goal: build square wave in a way to represent binary value of char
# We can divide the waveform into time slices representing 
# the response rate of LC (based off switch speed plot).
# Based off the plot, we can fit at most 12 bits per second.

# First 350ms will carry the start bit to begin read
# Each bit is 70ms wide (multiply by 2 since sample_freq is 20 kS/s)
# Begin window
bit_ini = int(0.100 * sample_rate) # initialization bit
mod_period = int(sample_rate * 0.080)
square_wave[0:bit_ini] = a_min * square_wave[0:bit_ini]
bit_start = bit_ini
bit_stop = bit_start + mod_period

b_msg = bin(ord(character))[2:].zfill(8)
for b in b_msg:
    print(bit_start , ' ', bit_stop)
    if b == '1':
        square_wave[bit_start:bit_stop] = a_min * square_wave[bit_start:bit_stop]
    else:
        square_wave[bit_start:bit_stop] = a_max * square_wave[bit_start:bit_stop]
    
    bit_start = bit_stop
    bit_stop = bit_start + mod_period

# Add start bit between characters
square_wave[bit_start:] = a_min * square_wave[bit_start:]

plt.plot(square_wave)
plt.show()