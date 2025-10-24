import numpy as np
import matplotlib.pyplot as plt
import random
from ModuPortadora import encode_ASK, encode_FSK, encode_PSK

# --- Random bit sequence ---
bits = [random.randint(0, 1) for _ in range(10)]

sample_rate = 1000  # amostras por segundo

# --- ASK parameters ---
carrier_freq = 5
sample_rate_ASK = sample_rate
ask_signal = encode_ASK(bits, freq=carrier_freq, sample_rate=sample_rate)
t_ask = np.linspace(0, len(bits), len(ask_signal), endpoint=False)

# --- FSK parameters ---
fsk_signal, t_fsk = encode_FSK(bits, A=1.0, freq1=8, freq0=4, sample_rate=sample_rate)

# --- PSK parameters ---
psk_signal = encode_PSK(bits, A=1.0, freq=8, sample_rate=500)
t_psk = np.linspace(0, len(bits), len(psk_signal), endpoint=False)

# --- Plot all three signals ---
plt.figure(figsize=(12, 8))

# ASK
plt.subplot(3, 1, 1)
plt.plot(t_ask, ask_signal, color='tab:blue')
plt.title("Amplitude Shift Keying (ASK)")
plt.ylabel("Amplitude")
plt.grid(True)

# FSK
plt.subplot(3, 1, 2)
plt.plot(t_fsk, fsk_signal, color='tab:orange')
plt.title("Frequency Shift Keying (FSK)")
plt.ylabel("Amplitude")
plt.grid(True)

# PSK
plt.subplot(3, 1, 3)
plt.plot(t_psk, psk_signal, color='tab:green')
plt.title("Phase Shift Keying (PSK)")
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.grid(True)

plt.tight_layout()
plt.show()
