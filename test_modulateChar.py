import numpy as np
import matplotlib.pyplot as plt

# Constants
freq_square_wave = 200  # Hz
sampling_freq = 20000  # Hz
duration = 1  # second
low_voltage = -0.1  # low amplitude (bipolar)
high_voltage = 0.1  # high amplitude (bipolar)
binary_string = '01001000'  # Binary representation of character 'H'
modulation_start = 0.4  # Start modulation at 400ms
modulation_end = 1.0  # End modulation at 1 second

# Generate time vector for the entire 1-second duration at 20,000 Hz sampling frequency
t = np.arange(0, duration, 1/sampling_freq)

# Generate the basic square wave at 200 Hz
square_wave = np.sign(np.sin(2 * np.pi * freq_square_wave * t))

# Normalize the square wave to have values between -0.1 and 0.1 (bipolar)
square_wave = square_wave * 0.1  # Convert range from [-1, 1] to [-0.1, 0.1]

# Create an array to store the modulated waveform
modulated_wave = np.copy(square_wave)

# Convert the binary string to a list of integers (0 and 1)
binary_values = [int(bit) for bit in binary_string]

# Calculate how many samples correspond to 400ms to 1 second range
modulation_start_idx = int(modulation_start * sampling_freq)
modulation_end_idx = int(modulation_end * sampling_freq)

# Iterate through the samples in the modulation range (400ms to 1 second)
for i in range(modulation_start_idx, modulation_end_idx):
    # Determine which part of the binary string we're in
    bin_idx = (i - modulation_start_idx) // (modulation_end_idx - modulation_start_idx) * len(binary_values)
    # Use the binary value (0 or 1) to modulate the amplitude
    if binary_values[(i - modulation_start_idx) % len(binary_values)] == 1:
        modulated_wave[i] = high_voltage
    else:
        modulated_wave[i] = low_voltage

# Plot the result
plt.figure(figsize=(10, 6))
plt.plot(t, modulated_wave, label='Modulated Bipolar Square Wave')
plt.title('Bipolar Modulated Square Wave with Frequency 200 Hz')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude [V]')
plt.xlim(0, 1)
plt.ylim(-0.15, 0.15)
plt.grid(True)
plt.legend()
plt.show()
