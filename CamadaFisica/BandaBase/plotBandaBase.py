import matplotlib.pyplot as plt
import numpy as np
import random 
from ModuBandaBase import encode_NRZ, encode_Manchester, encode_Bipolar

# Example bit sequence
bits = [random.randint(0, 1) for _ in range(10)]

bits = str().join(map(str, bits))

# Parameters
bit_duration = 0.5  # Duration of each bit in seconds
fs = 100            # Samples per second (for smooth plot)

# Function to expand a signal to continuous time
def expand_signal(signal, samples_per_bit):
    expanded = []
    for s in signal:
        expanded.extend([s]*samples_per_bit)
    return expanded

samples_per_bit = int(fs * bit_duration)

# Encode signals
nrz = expand_signal(encode_NRZ(bits), samples_per_bit)
manchester = expand_signal(encode_Manchester(bits), samples_per_bit//2)  # 2 samples per bit internally
bipolar = expand_signal(encode_Bipolar(bits), samples_per_bit)

# Time vectors
t_nrz = np.arange(len(nrz)) / fs
t_manchester = np.arange(len(manchester)) / fs
t_bipolar = np.arange(len(bipolar)) / fs

# Plot
plt.figure(figsize=(12, 6))

plt.subplot(3,1,1)
plt.plot(t_nrz, nrz, drawstyle='steps-post')
plt.title("NRZ Signal")
plt.ylim(-1.5, 1.5)
plt.grid(True)

plt.subplot(3,1,2)
plt.plot(t_manchester, manchester, drawstyle='steps-post')
plt.title("Manchester Signal")
plt.ylim(-1.5, 1.5)
plt.grid(True)

plt.subplot(3,1,3)
plt.plot(t_bipolar, bipolar, drawstyle='steps-post')
plt.title("Bipolar AMI Signal")
plt.ylim(-1.5, 1.5)
plt.grid(True)

plt.tight_layout()
plt.show()