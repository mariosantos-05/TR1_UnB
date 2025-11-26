# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 21:43:34 2025

@author: gabri

Modulacao digital e portadora
"""

import numpy as np
import math
from typing import List


#********************************Demodulation functions (should resist noise)**********************************
def NRZ_polar_demodulation(signal):
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


def manchester_demodulation_correlator(signal):
    """
    Demodula sinal Manchester.
    Assume que sinal é lista de níveis com comprimento par,
    cada bit codificado em dois níveis consecutivos.
    Retorna string de bits.
    """
    bits = []
    if len(signal) % 2 != 0:
        raise ValueError("Sinal Manchester deve ter comprimento par")
    for i in range(0, len(signal), 2):
        first = signal[i]
        second = signal[i + 1]
        # Considerando: transição de alto para baixo = 1, baixo para alto = 0
        if first > second:
            bits.append('1')
        else:
            bits.append('0')
    return ''.join(bits)

def bipolar_demodulation(signal: list[float]) -> str:
    """
    Decodificação Bipolar AMI (1 amostra por bit).
    Níveis:
      0 → bit 0
     +1 → bit 1
     -1 → bit 1
    """
    bits = []
    for s in signal:
        if abs(s) < 0.5:     # tolerância a ruído
            bits.append('0')
        else:
            bits.append('1')

    return ''.join(bits)


def ASK_demodulation(signal, freq=5, sample_rate=100):
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
        amplitude_estimada = (correlacao / sample_rate) *2
        banda_base.append(amplitude_estimada)

    return banda_base


#receiveis a signal sequence that corresponds to one symbol. to online decifration
def FSK_demodulation(signal, f1=5, f2=10, sample_rate=100):
    """
    Demodula um sinal FSK e retorna os bits detectados (0 ou 1).
    """
    num_symbols = len(signal) // sample_rate
    bits = []

    # sinais referencia (portadoras f1 e f2)
    t = np.linspace(0, 1, sample_rate, endpoint=False)
    portadora1 = np.sin(2 * np.pi * f1 * t)  # bit 1
    portadora0 = np.sin(2 * np.pi * f2 * t)  # bit 0

    for i in range(num_symbols):
        segmento = signal[i * sample_rate : (i + 1) * sample_rate]

        # Correlação com cada portadora
        cor1 = np.dot(segmento, portadora1)
        cor0 = np.dot(segmento, portadora0)

        # Decide o bit
        bit = 1 if cor1 > cor0 else 0
        bits.append(bit)

    return bits

        
def PSK_demodulation(signal, f=5, sample_rate=100):

    num_symbols = len(signal) // sample_rate
    bits = []

    t = np.linspace(0, 1, sample_rate, endpoint=False)
    portadora = np.sin(2 * np.pi * f * t)

    for i in range(num_symbols):
        segmento = signal[i * sample_rate : (i + 1) * sample_rate]

        # correlação com a portadora
        corr = np.dot(segmento, portadora)

        # PSK: sinal positivo → fase 0 → bit 1
        #      sinal negativo → fase π → bit 0
        bit = 1 if corr > 0 else 0
        bits.append(bit)

    return bits


    
def QPSK_demodulation(signal, f=1.0):

    num_symbols = len(signal)//100
    bits = []

    for i in range(num_symbols):

        I_hat = 0
        Q_hat = 0

        for j in range(100):
            t = j/100
            sample = signal[i*100+j]
            I_hat += sample * math.cos(2*math.pi*f*t)
            Q_hat += sample * math.sin(2*math.pi*f*t)

        # Decide sinal
        I = 1 if I_hat >= 0 else -1
        Q = 1 if Q_hat >= 0 else -1

        # Desfaz o mapa
        demap = {
            (1,1)   : [0,0],
            (-1,1)  : [0,1],
            (-1,-1) : [1,1],
            (1,-1)  : [1,0]
        }

        bits += demap[(I,Q)]

    return bits



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


def QAM16_demodulation(signal, f=1.0, samples_per_symbol=100):

    num_symbols = len(signal) // samples_per_symbol
    bit_stream = []

    t = np.arange(samples_per_symbol) / samples_per_symbol
    cos_carrier = np.cos(2 * np.pi * f * t)
    sin_carrier = np.sin(2 * np.pi * f * t)

    levels = np.array([-3, -1, 1, 3])

    for i in range(num_symbols):
        start = i * samples_per_symbol
        block = signal[start:start+samples_per_symbol]

        # Correlação para extrair I e Q
        I_hat = np.dot(block, cos_carrier) * 2 / samples_per_symbol
        Q_hat = np.dot(block, sin_carrier) * 2 / samples_per_symbol

        # Decisão por mínima distância
        I_dec = levels[np.argmin(np.abs(levels - I_hat))]
        Q_dec = levels[np.argmin(np.abs(levels - Q_hat))]

        bits = gray_map[(I_dec, Q_dec)]
        bit_stream.extend(bits)

    return bit_stream



    
    
    
    