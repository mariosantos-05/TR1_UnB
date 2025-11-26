# -*- coding: utf-8 -*-
"""
Arquivo: enlace_transmissor.py

Módulo que contém todas as funções da Camada de Enlace (Lado do Transmissor)
para a simulação de redes.

Funções incluídas:
- Enquadramento: Contagem de Caracteres, Bit Stuffing, Byte Stuffing.
- Detecção de Erros: Paridade Par, Checksum, CRC32.
- Correção de Erros: Hamming.
"""

# -------------------------------------------------------------------
# Seção 1: FUNÇÕES AUXILIARES INTERNAS
# -------------------------------------------------------------------

def _bits_para_lista_de_bytes(bits_dados: str) -> list[int]:
    """
    Função auxiliar interna para converter string de bits em lista de bytes (inteiros).
    Adiciona padding de '0' à ESQUERDA se o comprimento total não for múltiplo de 8.
    """
    if len(bits_dados) % 8 != 0:
        padding = 8 - (len(bits_dados) % 8)
        bits_dados = '0' * padding + bits_dados
    
    lista_bytes = []
    for i in range(0, len(bits_dados), 8):
        byte_str = bits_dados[i:i+8]
        lista_bytes.append(int(byte_str, 2))
    return lista_bytes

def _lista_de_bytes_para_bits(lista_bytes: list[int]) -> str:
    """Função auxiliar interna para converter lista de bytes (inteiros) em string de bits."""
    return ''.join(format(byte, '08b') for byte in lista_bytes)

def _e_potencia_de_2(n: int) -> bool:
    """Função auxiliar interna para verificar se um número é potência de 2."""
    if n == 1:
        return True
    elif n < 2:
        return False
    return (n > 0) and (n & (n - 1) == 0)


# -------------------------------------------------------------------
# Seção 2: ENQUADRAMENTO (FRAMING)
# -------------------------------------------------------------------

def enquadrar_contagem_caracteres(bits_dados: str) -> str:
    """
    Enquadra os dados usando o método de Contagem de Caracteres.
    [HEADER (1 byte)] + [DADOS (N bytes)]
    
    A função auxiliar '_bits_para_lista_de_bytes' garante o alinhamento de bytes.
    """
    print(f"[TX-Enquadramento] Contagem de Caracteres")
    
    lista_bytes_dados = _bits_para_lista_de_bytes(bits_dados)
    num_bytes = len(lista_bytes_dados)
    
    if num_bytes > 255:
        raise ValueError("Quadro excede 255 bytes para Contagem de Caracteres.")
        
    cabecalho = format(num_bytes, '08b')
    dados_formatados = _lista_de_bytes_para_bits(lista_bytes_dados)
    
    return cabecalho + dados_formatados


# --- Constantes para Byte Stuffing ---
FLAG_BYTE_INT = 0x7E  # 126 (binário: 01111110)
ESC_BYTE_INT  = 0x7D  # 125 (binário: 01111101)

def enquadrar_byte_stuffing(bits_dados: str) -> str:
    """
    Enquadra dados usando a técnica de Inserção de Bytes (Byte Stuffing).
    Escapa bytes FLAG ou ESC que aparecem nos dados.
    [FLAG] + [DADOS_COM_STUFFING] + [FLAG]
    """
    print("[TX-Enquadramento] Byte Stuffing")
    lista_bytes_dados = _bits_para_lista_de_bytes(bits_dados)
    
    bytes_stuffed = []
    
    # Adiciona ESC antes de FLAG ou ESC nos dados
    for byte in lista_bytes_dados:
        if byte == FLAG_BYTE_INT:
            bytes_stuffed.extend([ESC_BYTE_INT, FLAG_BYTE_INT])
        elif byte == ESC_BYTE_INT:
            bytes_stuffed.extend([ESC_BYTE_INT, ESC_BYTE_INT])
        else:
            bytes_stuffed.append(byte)
            
    # Adiciona as flags delimitadoras
    quadro_final_bytes = [FLAG_BYTE_INT] + bytes_stuffed + [FLAG_BYTE_INT]
    
    return _lista_de_bytes_para_bits(quadro_final_bytes)


# --- Constante para Bit Stuffing ---
FLAG_BITS = '01111110'

def enquadrar_bit_stuffing(bits_dados: str) -> str:
    """
    Enquadra dados usando a técnica de Inserção de Bits (Bit Stuffing).
    Insere um '0' após cinco '1's consecutivos.
    [FLAG] + [DADOS_COM_STUFFING] + [FLAG]
    """
    print("[TX-Enquadramento] Bit Stuffing")
    dados_stuffed = ''
    contagem_uns = 0
    
    for bit in bits_dados:
        if bit == '1':
            dados_stuffed += '1'
            contagem_uns += 1
        else: # bit == '0'
            dados_stuffed += '0'
            contagem_uns = 0
            
        # Insere o bit de stuffing
        if contagem_uns == 5:
            dados_stuffed += '0'
            contagem_uns = 0
            
    return FLAG_BITS + dados_stuffed + FLAG_BITS


# -------------------------------------------------------------------
# Seção 3: DETECÇÃO DE ERROS (ERROR DETECTION)
# -------------------------------------------------------------------

def adicionar_paridade_par(bits_dados: str) -> str:
    """
    Calcula a paridade par para a string de bits e a anexa no final.
    O bit de paridade é 0 se o número de '1's for par, 1 caso contrário.
    [DADOS] + [BIT_PARIDADE]
    """

    print(f"[TX-Detecção] Paridade Par: Aplicando...")
    paridade = 0
    for bit in bits_dados:
        paridade ^= int(bit)

    return bits_dados + str(paridade)


def adicionar_checksum(bits_dados: str) -> str:
    """
    Calcula o Checksum (Soma de Verificação) em blocos de 8 bits
    usando aritmética de complemento de um (one's complement) e anexa ao final.
    [DADOS] + [CHECKSUM (8 bits)]
    """
    print(f"[TX-Detecção] Checksum 8-bit: Calculando...")

    # --- ALTERAÇÃO MÍNIMA: pad direita igual à versão funcional ---
    if len(bits_dados) % 8 != 0:
        falta = 8 - (len(bits_dados) % 8)
        bits_dados = bits_dados + ('0' * falta)
    # --------------------------------------------------------------

    # Agora sim converte para lista de bytes (sem alterar conteúdo)
    lista_bytes_dados = [int(bits_dados[i:i+8], 2)
                         for i in range(0, len(bits_dados), 8)]

    soma = 0

    # Soma os bytes
    for byte in lista_bytes_dados:
        soma += byte

    # Trata carry
    while (soma >> 8) > 0:
        soma = (soma & 0xFF) + (soma >> 8)

    # Complemento de 1
    checksum = (~soma) & 0xFF
    checksum_bits = format(checksum, '08b')

    # Reconstrói string de dados
    dados_formatados = ''.join(format(b, '08b') for b in lista_bytes_dados)

    return dados_formatados + checksum_bits




POLI = 0x104C11DB7

def crc32(bits_str: str) -> str:
    """
    Aplica padding específico (<64 bits) e calcula o CRC-32 (IEEE 802.3).
    O cálculo usa divisão bitwise/aritmética.
    Retorna: (mensagem_final_com_crc, tamanho_do_padding)
    """
    pad_len = max(0, 64 - len(bits_str))
    padding = "".join(str(i % 2) for i in range(pad_len))
    dados_padded = bits_str + padding
    
    # Prepara dados para divisão: converte para inteiro e adiciona 32 zeros
    data_int = int(dados_padded, 2) << 32
    
    # 2. Loop de divisão polinomial
    highest_bit = data_int.bit_length() - 1 if data_int != 0 else 0
    
    for i in range(highest_bit, 31, -1):
        if (data_int >> i) & 1:
            data_int ^= POLI << (i - 32)

    # O resto são os 32 bits menos significativos (o CRC)
    crc_val = data_int & 0xFFFFFFFF
    
    crc_str = format(crc_val, '032b')
    
    return dados_padded + crc_str

# -------------------------------------------------------------------
# Seção 4: CORREÇÃO DE ERROS (ERROR CORRECTION)
# -------------------------------------------------------------------

def transmissor_hamming(bits_dados: str) -> str:
    """
    Codifica os dados com bits de Hamming, inserindo bits de paridade
    nas posições que são potências de 2.
    """
    print(f"[TX-Correção] Hamming: Codificando...")

    msg = '$' + bits_dados 
    aux = ''
    bits_verif = {}
    cont = 0

    m = len(bits_dados)
    r = 0

    # Calcula r exatamente como o código funcional faz
    while (2**r < r + m + 1):
        r += 1

    # --- CORREÇÃO: voltar a usar índices 0-based como o código funcional ---
    for i in range(len(msg) + r):
        if _e_potencia_de_2(i):
            aux += 'b'
            bits_verif[i] = '0'
        else:
            aux += msg[cont]
            cont += 1

    # --- CORREÇÃO: manter aux sem reintroduzir '$' ---
    # aux = '$' + aux   # removido

    # 2. calcular bits que cada verificador cobre (igual à versão funcional)
    for i in range(len(aux)):
        if aux[i] == 'b':
            bits_a_somar = ''
            pulo = i
            while (pulo < len(aux)):
                bits_a_somar += aux[pulo:pulo+i]
                pulo += i + i
            bits_verif[i] = bits_a_somar[1:]

    # 3. XOR de paridade — igual ao original
    lista = list(aux)
    for key, value in bits_verif.items():
        res = int(value[0])
        for bit in value[1:]:
            res ^= int(bit)
        bits_verif[key] = str(res)
        lista[key] = str(res)

    aux = ''.join(lista)

    return aux[1:]
