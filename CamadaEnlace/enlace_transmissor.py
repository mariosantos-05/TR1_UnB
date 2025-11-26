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

    #if len(bits_dados) % 8 != 0:
    #    padding = 8 - (len(bits_dados) % 8)
    #    bits_dados = '0' * padding + bits_dados

    print(f"[TX-Detecção] Paridade Par: Aplicando...")
    paridade = 0
    for bit in bits_dados:
        paridade ^= int(bit)

    return bits_dados + ('1' if paridade else '0')


def adicionar_checksum(bits_dados: str) -> str:
    """
    Calcula um checksum 8-bit usando soma de complemento de 1,
    sem adicionar qualquer padding.
    """
    print("[TX-Detecção] Checksum 8-bit: Calculando...")

    # Se necessário, aplicar padding deve ser feito FORA desta função, consistentemente no TX e RX.
    # Aqui NÃO adicionamos padding, apenas trabalhamos com os bits existentes.

    # 1. Se não for múltiplo de 8, completar à direita com zeros (não à esquerda).
    #    Isso mantém o alinhamento e não altera o conteúdo sem controle.
    if len(bits_dados) % 8 != 0:
        falta = 8 - (len(bits_dados) % 8)
        bits_dados = bits_dados + ('0' * falta)

    soma = 0

    # 2. Soma os bytes
    for i in range(0, len(bits_dados), 8):
        byte = bits_dados[i:i+8]
        soma += int(byte, 2)

    # 3. Compacta os carries
    while (soma >> 8) > 0:
        soma = (soma & 0xFF) + (soma >> 8)

    # 4. Complemento de 1
    checksum = (~soma) & 0xFF
    checksum_bits = format(checksum, '08b')

    return bits_dados + checksum_bits



POLI = 0x104C11DB7

def crc32(bits_str: str) -> str:
    """
    Calcula CRC-32 sem depender de pad_len (padding fixo de 64 bits).
    """
    padding = "0" * 64                     # <= padding fixo
    dados_padded = bits_str + padding

    data_int = int(dados_padded, 2) << 32

    highest_bit = data_int.bit_length() - 1
    for i in range(highest_bit, 31, -1):
        if (data_int >> i) & 1:
            data_int ^= POLI << (i - 32)

    crc_val = data_int & 0xFFFFFFFF
    crc_str = format(crc_val, "032b")

    return dados_padded + crc_str


# -------------------------------------------------------------------
# Seção 4: CORREÇÃO DE ERROS (ERROR CORRECTION)
# -------------------------------------------------------------------

def transmissor_hamming(mensagem: str) -> str:
    msg = '$' + mensagem 
    aux = ''
    bits_verif = {}
    cont = 0

    m = len(mensagem)
    r = 0
    while (2**r < r + m + 1): r += 1 # enquanto 2^r for menor que r + m + 1, continuar incrementando r

    # Criando uma msg lista com a posição dos bits de verificação e também um dicionário para adicionar seus valores finais
    for i in range (len(msg) + r):
        if _e_potencia_de_2(i):
            aux += 'b'
            bits_verif[i] = '0'
        else:
            aux += msg[cont]
            cont += 1


    #Pegando os bits para calcular os bits verificadores
    for i in range (len(aux)):
        if aux[i] == 'b':
            bits_a_somar = ''
            pulo = i
            while (pulo < len(aux)):
                bits_a_somar += aux[pulo:pulo+i]
                pulo += i + i
            bits_verif[i] = bits_a_somar[1:] #removendo o próprio bit de verificação

    #Calculando a paridade dos bits verificadores
    lista = list(aux)
    for key, value in bits_verif.items():
        res = int(value[0])
        for bit in value[1:]:
            res ^= int(bit)
        bits_verif[key] = str(res)
        lista[key] = str(res)
    aux = ''.join(lista)

    #para ver os valores dos bits de verificação, incluir bits_verif no retorno
    return aux[1:]
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
    # Calcula o número de bits de paridade 'r' necessários
    while (2**r < r + m + 1): 
        r += 1 

    # 1. Cria a lista com posições dos bits de verificação ('b')
    for i in range (1, m + r + 1):
        if _e_potencia_de_2(i):
            aux += 'b'
            bits_verif[i] = '0'
        else:
            aux += msg[cont+1]
            cont += 1

    aux = '$' + aux

    # 2. Pega os bits para calcular os bits verificadores
    for i in range (1, len(aux)):
        if aux[i] == 'b':
            bits_a_somar = ''
            pulo = i
            while (pulo < len(aux)):
                bits_a_somar += aux[pulo:pulo+i]
                pulo += i + i
            bits_verif[i] = bits_a_somar[1:] 

    # 3. Calculando a paridade (XOR)
    lista = list(aux)
    for key, value in bits_verif.items():
        res = int(value[0])
        for bit in value[1:]:
            res ^= int(bit)
        bits_verif[key] = str(res)
        lista[key] = str(res)
    
    aux = ''.join(lista)

    return aux[1:]