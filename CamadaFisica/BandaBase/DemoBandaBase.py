def decodenNRZ(signal):
    decoded = []
    for bit in signal:
        if bit == 1:
            decoded.append(1)
        else:
            decoded.append(0)
    return decoded

def decodeManchester(signal):
    decoded = []
    for i in range(0, len(signal), 2):
        if signal[i] == 1 and signal[i+1] == -1:
            decoded.append(1)
        elif signal[i] == -1 and signal[i+1] == 1:
            decoded.append(0)
    return decoded


def decodeBipolar(signal):
    decoded = []
    for level in signal:
        if level == 0:
            decoded.append(0)
        elif level in (1, -1):
            decoded.append(1)
    return decoded
