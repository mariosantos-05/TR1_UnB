# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 21:43:34 2025

@author: gabri

Modulacao digital
"""

import numpy as np
import math
from typing import List


#***********************************************DIGITAL DEMODULATION******************************************
def decode_NRZ(signal):
    """
    Demodula sinal NRZ-Polar.
    Assume que sinal é lista de níveis (ex: +1, -1)
    Retorna string de bits.
    """
    bits = []
    for level in signal:
        if level > 0:
            bits.append('1')
        else:
            bits.append('0')
    return ''.join(bits)

def decode_manchester(received_signal, samples_per_symbol=100, A_ref=1.0):
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

def decode_bipolar(A,signal, samples_per_bit=100):
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

def decode_ASK(signal, freq=5, sample_rate=100):
    """
    Demodula um sinal ASK e retorna a sequência de bits.
    """
    num_symbols = len(signal) // sample_rate
    banda_base = []

    # Para cada símbolo, correlaciona com a portadora para extrair amplitude
    t = np.linspace(0, 1, sample_rate, endpoint=False)
    portadora = np.sin(2 * np.pi * freq * t)

    for i in range(num_symbols):
        segmento = signal[i * sample_rate : (i + 1) * sample_rate]
        # Produto interno (correlação) para estimar amplitude
        correlacao = np.dot(segmento, portadora)
        # Normaliza (opcional)
        amplitude_estimada = correlacao / sample_rate
        banda_base.append(amplitude_estimada)

    return banda_base


#receiveis a signal sequence that corresponds to one symbol. to online decifration
def decode_FSK(signal, A = 1,f1 = 5 ,f2=10):
    samples_per_bit = 100
    signal1 = np.zeros(samples_per_bit)
    signal2 = np.zeros(samples_per_bit)
    
    corf1 = 0
    corf2 = 0
    for i in range(samples_per_bit):
        signal1[i] = A *  math.sin(2*math.pi*f1*i/samples_per_bit)
        signal2[i] = A *  math.sin(2*math.pi*f2*i/samples_per_bit)
        
        corf1 += signal1[i] * signal[i]
        corf2 += signal2[i] * signal[i]
    
    if corf1 > corf2:
        bit = 1
    else:
        bit = 0
        
    return bit 
        
def PSK_demodulation(signal, f=5):
    sig_size = len(signal)
    
    t = np.arange(sig_size)/sig_size
    reference = np.sin(2*np.pi*f*t)
    
    corr = np.sum(np.array(signal)*reference)
    
    if corr > 0:
        bit = 1 
    else:
        bit = 0
    
    return bit

    
def QPSK_demodulation(rx_signal, f=5.0, samples_per_symbol=100):
    """
    QPSK demodulator (coherent correlator):
      - rx_signal: received samples (numpy array)
      - f: carrier frequency (same units as modulator's f)
      - samples_per_symbol: samples per symbol (must match modulator)
    Returns: list of recovered bits [b0,b1,b0,b1,...]
    """
    N = samples_per_symbol
    num_symbols = len(rx_signal) // N

    t = np.arange(N) / N
    cos_carrier = np.cos(2 * np.pi * f * t)
    sin_carrier = np.sin(2 * np.pi * f * t)

    bits_out = []

    for k in range(num_symbols):
        block = rx_signal[k*N : (k+1)*N]

        # Correlate with cos to get I*energy (approx)
        I_corr = np.dot(block, cos_carrier)

        # Because transmitter used "- Q*sin", correlate with -sin to get Q positive when Q_sym>0:
        Q_corr = -np.dot(block, sin_carrier)

        # Decide sign -> map back to bits using same mapping used in modulation
        # We didn't normalize by energy because we only need sign, not magnitude.
        I_pos = 1 if I_corr > 0 else -1
        Q_pos = 1 if Q_corr > 0 else -1

        # inverse of mapping:
        # (I,Q) -> bits:
        # (+1, +1) -> (0,0)
        # (-1, +1) -> (0,1)
        # (-1, -1) -> (1,1)
        # (+1, -1) -> (1,0)
        if (I_pos, Q_pos) == (1, 1):
            bits_out.extend([0, 0])
        elif (I_pos, Q_pos) == (-1, 1):
            bits_out.extend([0, 1])
        elif (I_pos, Q_pos) == (-1, -1):
            bits_out.extend([1, 1])
        elif (I_pos, Q_pos) == (1, -1):
            bits_out.extend([1, 0])
        else:
            # fallback - shouldn't happen
            bits_out.extend([0,0])

    return bits_out


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


def decode_16QAM(signal, f = 5.0):

    num_symbols = len(signal)//100
    bit_stream = []

    # Níveis possíveis
    levels = np.array([-3, -1, 1, 3])

    for i in range(num_symbols):

        # correlação
        I_hat = 0
        Q_hat = 0

        for j in range(100):
            t = j/100
            sample = signal[i*100+j]

            I_hat += sample * math.cos(2*math.pi*f*t)
            Q_hat += sample * math.sin(2*math.pi*f*t)
        
        I_hat = I_hat/50
        Q_hat = Q_hat/50
        print(I_hat)
        print(Q_hat)
        # Decide para qual nível está mais próximo
        I_dec = levels[np.argmin(abs(levels - I_hat))]
        Q_dec = levels[np.argmin(abs(levels - Q_hat))]

        # Convert back to bits
        bits = gray_map[(I_dec, Q_dec)]
        bit_stream += bits

    return bit_stream


    
    
    
    