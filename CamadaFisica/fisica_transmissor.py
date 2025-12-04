# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 21:43:34 2025

@author: gabri

Modulacao digital e portadora
"""

import numpy as np
import math
from typing import List


def NRZ_polar_modulation(bits: str, A=1) -> List[float]:
    signal = []
    for bit in bits:
        if bit == '1':
            signal.append(1.0)
        else:
            signal.append(-1.0)
    return signal

def manchester_modulation(bits: str) -> List[float]: 
 
    signal = []
    for bit in bits:
        if bit == '1':
            signal.extend([1.0, -1.0])
        else:
            signal.extend([-1.0, 1.0])
    return signal


def bipolar_modulation(bits):
    """
    Modulação Bipolar AMI equivalente à encode_bipolar,
    mas usando a estrutura original da função dada.
    """
    signal = []
    last_pulse = -1  # igual à encode_bipolar: primeiro '1' vira +1

    for b in bits:
        if b == '0':
            level = 0.0
        else:
            last_pulse = -last_pulse  # alterna entre +1 e -1
            level = float(last_pulse)

        signal.append(level)

    return signal

def ASK_modulation(bits: list[float], freq=5, sample_rate=100):
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
                

def FSK_modulation(bits: list[int], f1=10, f2=5, sample_rate=100):
    t = np.linspace(0, 1, sample_rate, endpoint=False)
    signal = []

    for bit in bits:
        freq = f1 if bit == 1 else f2
        wave = np.sin(2 * np.pi * freq * t)
        signal.extend(wave)

    return np.array(signal)

                
def PSK_modulation(bits: list[int], f=5, sample_rate=100):
    t = np.linspace(0, 1, sample_rate, endpoint=False)
    signal = []

    for bit in bits:
        fase = 0 if bit == 1 else np.pi
        wave = np.sin(2 * np.pi * f * t + fase)
        signal.extend(wave)

    return np.array(signal)

def QPSK_modulation(bit_stream, f=1.0):

    # Converte qualquer entrada para bit real (0 ou 1)
    bit_stream = [1 if str(b) in ["1", "1.0", "+1", "True"] else 0 for b in bit_stream]

    # Garantir múltiplo de 2
    if len(bit_stream) % 2 != 0:
        bit_stream.append(0)

    mapping = {
        (0,0): (1,1),
        (0,1): (-1,1),
        (1,1): (-1,-1),
        (1,0): (1,-1)
    }

    num_symbols = len(bit_stream)//2
    signal = np.zeros(num_symbols*100)

    for i in range(num_symbols):

        b0 = bit_stream[2*i]
        b1 = bit_stream[2*i+1]

        I, Q = mapping[(b0, b1)]

        for j in range(100):
            t = j/100
            signal[i*100+j] = I*math.cos(2*math.pi*f*t) + Q*math.sin(2*math.pi*f*t)

    return signal



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
    # Converte bits vindos como str → int
    bits = [1 if str(b) in ["1","1.0"] else 0 for b in bits]
    return inv_gray[tuple(bits)]


def QAM16_modulation(bit_stream, f=1.0, samples_per_symbol=100):

    # Converte string para inteiro (e evita NRZ se vier -1/+1)
    bit_stream = [1 if str(b) in ["1", "1.0"] else 0 for b in bit_stream]

    assert len(bit_stream) % 4 == 0, "16QAM usa 4 bits por símbolo"


    num_symbols = len(bit_stream)//4
    signal = np.zeros(num_symbols * samples_per_symbol)

    t = np.arange(samples_per_symbol) / samples_per_symbol
    cos_carrier = np.cos(2 * np.pi * f * t)
    sin_carrier = np.sin(2 * np.pi * f * t)

    for i in range(num_symbols):
        bits = bit_stream[i*4:(i+1)*4]
        I, Q = bits_to_IQ(bits)

        # Sinal 16QAM
        start = i * samples_per_symbol
        signal[start:start+samples_per_symbol] = (
            I * cos_carrier + Q * sin_carrier
        )

    return signal
