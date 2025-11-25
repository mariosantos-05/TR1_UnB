# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 21:43:34 2025

@author: gabri

Modulacao digital
"""

import numpy as np
import math

#***********************************************DIGITAL MODULATION*******************************************
def NRZ_polar_modulation(bit_stream, A=1.0):
    signal = np.zeros(len(bit_stream) * 100)

    for i, bit in enumerate(bit_stream):
        level = A if bit == 1 else -A
        signal[i*100:(i+1)*100] = level  # 100 examples of the same value

    return signal

def manchester_modulation(bit_stream, A=1.0, samples_per_symbol=100):
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

def bipolar_modulation(bit_stream, A=1.0, samples_per_bit=100):
    """
    Modulação Bipolar AMI com 100 amostras por bit.
    
    Escolher amplitudes maiores aumenta resistencia a ruidos maiores na demodulacao como esta implementada.
    """
    signal = []
    last_pulse = -1  # para que o primeiro 1 seja +1

    for b in bits:
        if b == 0:
            level = 0
        else:
            last_pulse = -last_pulse  # alterna entre +1 e -1
            level = last_pulse

        # Repete o valor 'level' por 100 amostras
        signal.extend([level * A] * samples_per_bit)

    return np.array(signal)


#***********************************************DIGITAL DEMODULATION******************************************
def NRZ_polar_demodulation(signal):
    """
    Demodulação NRZ-Polar por limiar (threshold)
    """
    num_bits = len(signal) // 100
    bit_stream = []

    for i in range(num_bits):
        segment = signal[i*100:(i+1)*100]
        avg = np.mean(segment)

        bit = 1 if avg >= 0 else 0
        bit_stream.append(bit)

    return bit_stream

def manchester_demodulation_correlator(received_signal, samples_per_symbol=100, A_ref=1.0):
    """
    Demodula usando correlação com formas de onda de referência Manchester.
    Gera duas formas de referência (para bit=1 e bit=0) e calcula correlação.
    Escolhe o bit que dá correlação maior.
    - A_ref: amplitude de referência das formas (não precisa ser igual ao A do TX, apenas escala)
    """
    if samples_per_symbol % 2 != 0:
        raise ValueError("samples_per_symbol deve ser par para Manchester")

    N = samples_per_symbol
    half = N // 2
    # forma referência para bit=1: [+1 ... +1, -1 ... -1] (amplitude A_ref)
    ref1 = np.concatenate((np.ones(half)*A_ref, np.ones(half)*(-A_ref)))
    # forma referência para bit=0: [-1 ... -1, +1 ... +1]
    ref0 = np.concatenate((np.ones(half)*(-A_ref), np.ones(half)*(A_ref)))

    num_bits = len(received_signal) // N
    bits = []
    for k in range(num_bits):
        block = received_signal[k*N : (k+1)*N]
        corr1 = np.dot(block, ref1)  # correlação com ref1
        corr0 = np.dot(block, ref0)  # correlação com ref0
        bit = 1 if corr1 > corr0 else 0
        bits.append(bit)
    return bits

def bipolar_demodulation(A,signal, samples_per_bit=100):
    """
    Demodulação AMI: integra 100 amostras por bit e detecta 0 ou 1.
    
    usar mesma amplitude, ou similar a usada na modulacao (pode estimar na recepcao do sinal)
    """
    num_bits = len(signal) // samples_per_bit
    bits = []

    for i in range(num_bits):
        segment = signal[i*samples_per_bit:(i+1)*samples_per_bit]
        avg = np.mean(segment)

        if abs(avg) < 0.3 * A:  # tolerância para ruído
            bits.append(0)
        else:
            bits.append(1)

    return bits
