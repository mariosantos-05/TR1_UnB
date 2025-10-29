
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

def encode_16QAM(bits: list[int], A=1.0, freq=8, sample_rate=100) -> list[float]:
    bit_duration = 1  # each symbol lasts 1 second
    t_bit = np.linspace(0, bit_duration, sample_rate, endpoint=False)
    signal = []
    
    # Mapping for 16-QAM (Gray coding)
    mapping = {
        0: (-3, -3), 1: (-3, -1), 2: (-3, 3), 3: (-3, 1),
        4: (-1, -3), 5: (-1, -1), 6: (-1, 3), 7: (-1, 1),
        8: (3, -3), 9: (3, -1), 10: (3, 3), 11: (3, 1),
        12: (1, -3), 13: (1, -1), 14: (1, 3), 15: (1, 1)
    }
    
    for symbol in bits:
        I, Q = mapping[symbol]
        carrier_I = A * I * np.sin(2 * np.pi * freq * t_bit)
        carrier_Q = A * Q * np.cos(2 * np.pi * freq * t_bit)
        combined_signal = carrier_I + carrier_Q
        signal.extend(combined_signal)
    
    return signal

