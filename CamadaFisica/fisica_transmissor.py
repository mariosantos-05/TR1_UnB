# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 21:43:34 2025

@author: gabri

Modulacao digital
"""

import numpy as np
import math
from typing import List


def encode_NRZ(bits: str) -> List[float]:
    """
    NRZ Polar: 1 → +1, 0 → -1
    """
    signal = []
    for bit in bits:
        if bit == '1':
            signal.append(1.0)
        else:
            signal.append(-1.0)
    return signal

def encode_manchester(bit_stream, A=1.0, samples_per_symbol=100):
    """
    Modula uma sequência de bits usando Manchester.
    Convenção: bit 1 -> [ +A (primeira metade) , -A (segunda metade) ]
                bit 0 -> [ -A (primeira metade) , +A (segunda metade) ]
    samples_per_symbol deve ser par (divisível por 2).
    Retorna: numpy.array de amostras (float)
    """
    if samples_per_symbol % 2 != 0:
        raise ValueError("samples_per_symbol deve ser par para Manchester")
    num_bits = len(bit_stream)
    s = np.zeros(num_bits * samples_per_symbol)
    half = samples_per_symbol // 2

    for i, b in enumerate(bit_stream):
        start = i * samples_per_symbol
        if b == 1:
            s[start : start + half] = A           # primeira metade +A
            s[start + half : start + samples_per_symbol] = -A  # segunda metade -A
        else:
            s[start : start + half] = -A
            s[start + half : start + samples_per_symbol] = A

    return s

def encode_bipolar(bit_stream, A=1.0, samples_per_bit=100):
    """
    Modulação Bipolar AMI com 100 amostras por bit.
    
    Escolher amplitudes maiores aumenta resistencia a ruidos maiores na demodulacao como esta implementada.
    """
    signal = []
    last_pulse = -1  # para que o primeiro 1 seja +1

    for b in bit_stream:
        if b == 0:
            level = 0
        else:
            last_pulse = -last_pulse  # alterna entre +1 e -1
            level = last_pulse

        # Repete o valor 'level' por 100 amostras
        signal.extend([level * A] * samples_per_bit)

    return np.array(signal)


def encode_ASK(bits: list[float], freq=5, sample_rate=100):
    """
    Amplitude Shift Keying: codifica bits em uma onda com amplitude variável.
    Recebe uma lista de floats e retorna uma lista de floats
    """
    t = np.linspace(0, 1, sample_rate, endpoint=False)
    signal = []
    print(bits)
    for amplitude in bits:
        wave = amplitude * np.sin(2 * np.pi * freq * t)
        signal.extend(wave)

    return np.array(signal)
                

def encode_FSK(bit_stream, A=1.0, f1=1.0, f2=2.0):
    sig_size = len(bit_stream)
    signal = np.zeros(sig_size*100)
    
    for i in range(0,sig_size):
        if(bit_stream[i] == 1):
            for j in range(0,100):
                signal[(i)*100+j] = A *  math.sin(2*math.pi*f1*j/100)
        else:
            for j in range(0,100):
                signal[(i)*100+j] = A *  math.sin(2*math.pi*f2*j/100)
    
    return signal
                
def PSK_modulation(bit_stream, A=1.0, f=1.0):
    sig_size = len(bit_stream)
    signal = np.zeros(sig_size*100)
    
    for i in range(0,sig_size):
        if(bit_stream[i] == 1):
            for j in range(0,100):
                signal[i*100+j] = A*math.sin(2*math.pi*f*j/100)
        else:
            for j in range(0,100):
                signal[i*100+j] = A*math.sin(2*math.pi*f*j/100 + math.pi)
    
    return signal

def QPSK_modulation(bit_stream, A=1.0, f=1.0, samples_per_symbol=100):
    """
    QPSK modulator:
      - bit_stream: list/array of 0/1 bits (length even; if odd, will be padded with 0)
      - A: amplitude scale
      - f: carrier frequency (in cycles per symbol)
      - samples_per_symbol: how many samples represent one QPSK symbol (default 100)
    Returns: 1D numpy array of samples (float)
    """
    bits = list(bit_stream)
    # pad if needed
    if len(bits) % 2 != 0:
        bits.append(0)

    # Gray mapping: (b_i, b_q) -> (I, Q)
    # (0,0) -> (+1, +1)
    # (0,1) -> (-1, +1)
    # (1,1) -> (-1, -1)
    # (1,0) -> (+1, -1)
    mapping = {
        (0,0): (1.0,  1.0),
        (0,1): (-1.0, 1.0),
        (1,1): (-1.0,-1.0),
        (1,0): (1.0, -1.0)
    }

    num_symbols = len(bits) // 2
    sig = np.zeros(num_symbols * samples_per_symbol)

    # time vector for one symbol (normalized 0..1)
    t = np.arange(samples_per_symbol) / samples_per_symbol
    cos_carrier = np.cos(2 * np.pi * f * t)
    sin_carrier = np.sin(2 * np.pi * f * t)

    # Optionally normalize I/Q so average symbol power = A^2
    # Here I and Q values are +/-1; combined power per symbol = 2.
    # We'll scale final I/Q by A / sqrt(2) so average power ~ A^2.
    scale = A / math.sqrt(2.0)

    for k in range(num_symbols):
        b0 = bits[2*k]     # I-bit
        b1 = bits[2*k + 1] # Q-bit
        I_sym, Q_sym = mapping[(b0, b1)]
        I_sym *= scale
        Q_sym *= scale
        start = k * samples_per_symbol
        # s(t) = I*cos - Q*sin
        sig[start:start + samples_per_symbol] = I_sym * cos_carrier - Q_sym * sin_carrier

    return sig

# Gray table 16-QAM
gray_map = {
    ( -3, -3): [0,0,0,0],
    ( -3, -1): [0,0,0,1],
    ( -3,  1): [0,0,1,1],
    ( -3,  3): [0,0,1,0],
    ( -1, -3): [0,1,0,0],
    ( -1, -1): [0,1,0,1],
    ( -1,  1): [0,1,1,1],
    ( -1,  3): [0,1,1,0],
    (  1, -3): [1,1,0,0],
    (  1, -1): [1,1,0,1],
    (  1,  1): [1,1,1,1],
    (  1,  3): [1,1,1,0],
    (  3, -3): [1,0,0,0],
    (  3, -1): [1,0,0,1],
    (  3,  1): [1,0,1,1],
    (  3,  3): [1,0,1,0],
}

# Inverso para demodulação
inv_gray = {tuple(v): k for k,v in gray_map.items()}

def bits_to_IQ(bits):
    return inv_gray[tuple(bits)]

def encode_16QAM(bit_stream, f=1.0):
    assert len(bit_stream) % 4 == 0, "16QAM usa 4 bits por símbolo"

    num_symbols = len(bit_stream)//4
    signal = np.zeros(num_symbols*100)

    for i in range(num_symbols):
        bits = bit_stream[i*4:(i+1)*4]
        I, Q = bits_to_IQ(bits)

        for j in range(100):
            t = j/100
            signal[i*100+j] = I*math.cos(2*math.pi*f*t) + Q*math.sin(2*math.pi*f*t)

    return signal
