import numpy as np
from utils import daq
import matplotlib.pyplot as plt

duration = 1
sample_rate = daq.DaqAO.FREQ_SAMPLE.value
frequency = daq.LC.FREQ_LC.value
character = 'H'
a_max = 6 #daq.LC.V_OFF.value
a_min = daq.LC.V_ON.value
mod_period = 0.080

t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
v_step = np.arange(0, a_max, mod_period, dtype=float,)

square_wave = np.sign(np.sin(2 * np.pi * frequency * t))
m_period = int((1/len(v_step)) * sample_rate)
w_start = 0
w_stop = m_period

for v in v_step:
    square_wave[w_start:w_stop] = v * square_wave[w_start:w_stop]
    w_start = w_stop
    w_stop += m_period
    
print(len(v_step))
plt.plot(square_wave)
plt.show()