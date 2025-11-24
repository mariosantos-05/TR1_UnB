def encode_NRZ(bits : str) -> list[float]:
    nrz_signal = []
    for bit in bits:
        if bit == '1':
            nrz_signal.append(1.0)  # Representa nível alto
        else:
            nrz_signal.append(-1.0)  # Representa nível baixo
    return nrz_signal

def encode_Manchester(bits : str) -> list[float]:
    manchester_signal = []
    for bit in bits:
        if bit == '1':
            manchester_signal.extend([1.0, -1.0])  # Transição de alto para baixo
        else:
            manchester_signal.extend([-1.0, 1.0])  # Transição de baixo para alto
    return manchester_signal   

def encode_Bipolar(bits : str) -> list[float]:
    bipolar_ami_signal = []
    last_level = -1.0  # Começa com nível negativo para o primeiro '1'
    for bit in bits:
        if bit == '1':
            last_level *= -1  # Alterna entre +1 e -1
            bipolar_ami_signal.append(last_level)
        else:
            bipolar_ami_signal.append(0.0)  # Representa nível zero para '0'
    return bipolar_ami_signal