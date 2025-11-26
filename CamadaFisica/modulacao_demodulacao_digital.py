# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 21:43:34 2025

@author: gabri

Modulacao digital
"""

import numpy as np
import math
from typing import List

#***********************************************DIGITAL MODULATION*******************************************
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

def QAM16_modulation(bit_stream, f=1.0):
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

#********************************Demodulation functions (should resist noise)**********************************

#receiveis a signal sequence that corresponds to one symbol. to online decifration
def ASK_demodulation(A,signal):
    sig_size = len(signal)
    
    quadratic_sum = 0
    for i in range(0,sig_size):
        quadratic_sum += signal[i]**2
        
    if math.sqrt(quadratic_sum/sig_size) > A/4:
        bit = 1
    else:
        bit = 0
    
    return bit


#receiveis a signal sequence that corresponds to one symbol. to online decifration
def FSK_demodulation(A,f1,f2,signal):
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
        
def PSK_demodulation(A,f,signal):
    sig_size = len(signal)
    
    t = np.arange(sig_size)/sig_size
    reference = np.sin(2*np.pi*f*t)
    
    corr = np.sum(np.array(signal)*reference)
    
    if corr > 0:
        bit = 1 
    else:
        bit = 0
    
    return bit

    
def QPSK_demodulation(rx_signal, f, samples_per_symbol=100):
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

def encode_8QAM(signal, f):

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


    
    
    
    


    # -*- coding: utf-8 -*-
"""
Created on Fri Nov 14 15:28:55 2025

@author: gabri

MODULACAO POR PORTADORA
"""
import numpy as np
import math

#modulation functions

#remember to add noise here on the function (final shape)
#all functions should be on 

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

def encode_8QAM(bit_stream, f=1.0):
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

#********************************Demodulation functions (should resist noise)**********************************

#receiveis a signal sequence that corresponds to one symbol. to online decifration
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
def decode_FSK(A,f1,f2,signal):
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
        
def PSK_demodulation(A,f,signal):
    sig_size = len(signal)
    
    t = np.arange(sig_size)/sig_size
    reference = np.sin(2*np.pi*f*t)
    
    corr = np.sum(np.array(signal)*reference)
    
    if corr > 0:
        bit = 1 
    else:
        bit = 0
    
    return bit

    
def QPSK_demodulation(rx_signal, f, samples_per_symbol=100):
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

def decode_8QAM(signal, f):

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


    
    
    
    