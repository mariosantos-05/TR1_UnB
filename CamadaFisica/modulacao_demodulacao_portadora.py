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

def ASK_modulation(bit_stream, A=1.0, f=1.0):
    sig_size = len(bit_stream)
    signal = np.zeros(sig_size*100)
    
    for i in range(0,sig_size):
        if(bit_stream[i] == 1):
            for j in range(0,100):
                signal[(i)*100+j] = A *  math.sin(2*math.pi*f*j/100)
        else:
            for j in range(0,100):
                signal[(i)*100+j] = 0
    
    return signal
                

def FSK_modulation(bit_stream, A=1.0, f1=1.0, f2=2.0):
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

def QAM16_demodulation(signal, f):

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


    
    
    
    