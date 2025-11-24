import numpy as np
import matplotlib.pyplot as plt
import random
from ModuPortadora import encode_ASK, encode_FSK, encode_PSK, encode_16QAM

# --- Random bit sequence ---
bits = [random.randint(0, 1) for _ in range(16)]  # 16 bits → 4 symbols for 16-QAM

sample_rate = 1000  # amostras por segundo

# --- ASK ---
ask_signal = encode_ASK(bits, freq=5, sample_rate=sample_rate)
t_ask = np.linspace(0, len(bits), len(ask_signal), endpoint=False)

# --- FSK ---
fsk_signal, t_fsk = encode_FSK(bits, A=1.0, freq1=8, freq0=4, sample_rate=sample_rate)

# --- PSK ---
psk_signal = encode_PSK(bits, A=1.0, freq=8, sample_rate=sample_rate)
t_psk = np.linspace(0, len(bits), len(psk_signal), endpoint=False)


qam16_signal = encode_16QAM(bits, A=0.25, freq=8, sample_rate=sample_rate)
t_qam = np.linspace(0, len(bits)/4, len(qam16_signal), endpoint=False)

# --- Plot all signals ---
plt.figure(figsize=(12, 10))

plt.subplot(4, 1, 1)
plt.plot(t_ask, ask_signal, color='tab:blue')
plt.title("Amplitude Shift Keying (ASK)")
plt.ylabel("Amplitude")
plt.grid(True)

plt.subplot(4, 1, 2)
plt.plot(t_fsk, fsk_signal, color='tab:orange')
plt.title("Frequency Shift Keying (FSK)")
plt.ylabel("Amplitude")
plt.grid(True)

plt.subplot(4, 1, 3)
plt.plot(t_psk, psk_signal, color='tab:green')
plt.title("Phase Shift Keying (PSK)")
plt.ylabel("Amplitude")
plt.grid(True)

plt.subplot(4, 1, 4)
plt.plot(t_qam, qam16_signal, color='tab:red')
plt.title("16-QAM (Quadrature Amplitude Modulation)")
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.grid(True)

plt.tight_layout()
plt.show()
