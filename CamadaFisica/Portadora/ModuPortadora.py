
import numpy as np
import matplotlib.pyplot as plt


def encode_ASK(bits: list[float], freq=8, sample_rate= 100) -> list[float]:
    t_bit = 1 / freq  # Duração de cada bit
    t = np.linspace(0, t_bit, sample_rate, endpoint=False)  # Vetor de tempo para um bit
    carrier = np.sin(2 * np.pi * freq * t)  # Sinal da portadora

    ask_signal = []
    for bit in bits:
        if bit == 1.0:
            ask_signal.extend(carrier)  # Transmite a portadora para '1'
        else:
            ask_signal.extend([0.0] * sample_rate)  # Silêncio para '0'
    
    return ask_signal

def encode_FSK(bits: list[float], A=1.0, freq1=8, freq0=4, sample_rate=100) -> tuple[list[float], np.ndarray]:
    bit_duration = 1  # each bit lasts 1 second
    t_bit = np.linspace(0, bit_duration, sample_rate, endpoint=False)
    signal = []
    
    for bit in bits:
        freq = freq1 if bit == 1.0 else freq0
        carrier = A * np.sin(2 * np.pi * freq * t_bit)
        signal.extend(carrier)
    
    # Build global time vector
    total_time = bit_duration * len(bits)
    t = np.linspace(0, total_time, len(signal), endpoint=False)
    return np.array(signal), t

def encode_PSK(bits: list[float], A=1.0, freq=8, sample_rate=100) -> list[float]:
    bit_duration = 1  # each bit lasts 1 second
    t_bit = np.linspace(0, bit_duration, sample_rate, endpoint=False)
    signal = []
    
    for bit in bits:
        phase = 0 if bit == 1.0 else np.pi  # 0 for '1', π for '0'
        carrier = A * np.sin(2 * np.pi * freq * t_bit + phase)
        signal.extend(carrier)
    
    return signal