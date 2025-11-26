# -*- coding: utf-8 -*-
"""
Arquivo: enlace_receptor.py

Este arquivo contém todas as funções da Camada de Enlace (Lado do Receptor)
para o simulador de redes.

Funções incluídas:
1.  Desenquadramento (De-framing):
    - desenquadrar_contagem_caracteres
    - desenquadrar_bit_stuffing
    - desenquadrar_byte_stuffing
2.  Detecção de Erros (Error Detection):
    - verificar_paridade_par (Com correção de padding)
    - verificar_checksum
    - verificar_crc32
3.  Correção de Erros (Error Correction):
    - receptor_hamming
"""

# -------------------------------------------------------------------
# Seção 1: FUNÇÕES AUXILIARES
# -------------------------------------------------------------------

def _bits_para_lista_de_bytes(bits_dados: str) -> list[int]:
    """
    Converte string de bits em lista de bytes (inteiros).
    Assume que o input já está alinhado ou o padding será tratado pelo chamador.
    """
    lista_bytes = []
    # Processa em blocos de 8 bits
    for i in range(0, len(bits_dados), 8):
        byte_str = bits_dados[i:i+8]
        # Se sobrar um pedaço menor que 8 bits no final, processa também
        if byte_str: 
            lista_bytes.append(int(byte_str, 2))
    return lista_bytes

def _lista_de_bytes_para_bits(lista_bytes: list[int]) -> str:
    """Converte lista de bytes (inteiros) em string de bits."""
    return ''.join(format(byte, '08b') for byte in lista_bytes)

def _e_potencia_de_2(n: int) -> bool:
    """Verifica se um número é potência de 2."""
    return (n > 0) and (n & (n - 1) == 0)


# -------------------------------------------------------------------
# Seção 2: DESENQUADRAMENTO (DE-FRAMING)
# -------------------------------------------------------------------

def desenquadrar_contagem_caracteres(quadro_bits: str) -> str:
    """
    Desenquadra dados usando Contagem de Caracteres.
    Lê o primeiro byte (cabeçalho) para saber o tamanho e extrai os dados.
    Retorna: Apenas os dados (sem o cabeçalho).
    """
    print("[RX-Desenquadramento] Contagem de Caracteres")
    
    if len(quadro_bits) < 8:
        raise ValueError("Quadro muito curto para conter cabeçalho.")

    # 1. Ler o cabeçalho (primeiros 8 bits)
    tamanho_em_bytes = int(quadro_bits[0:8], 2)
    
    tamanho_esperado_bits = tamanho_em_bytes * 8
    
    inicio_dados = 8
    fim_dados = 8 + tamanho_esperado_bits
    
    if len(quadro_bits) < fim_dados:
        print(f"[AVISO] Quadro recebido menor que o esperado ({len(quadro_bits)} < {fim_dados}).")
    
    dados = quadro_bits[inicio_dados:fim_dados]
    return dados


# --- Constantes para Byte Stuffing ---
FLAG_BYTE_INT = 0x7E  # 126
ESC_BYTE_INT  = 0x7D  # 125

def desenquadrar_byte_stuffing(quadro_bits: str) -> str:
    """
    Desenquadra dados usando Byte Stuffing.
    Remove flags de início/fim e trata os caracteres de escape (ESC).
    """
    print("[RX-Desenquadramento] Byte Stuffing")
    
    lista_bytes = _bits_para_lista_de_bytes(quadro_bits)
    
    # Validação básica de Flags
    if len(lista_bytes) < 2:
        return "" 
        
    if lista_bytes[0] == FLAG_BYTE_INT and lista_bytes[-1] == FLAG_BYTE_INT:
        # Remove as flags das pontas
        meio = lista_bytes[1:-1]
    else:
        print("[AVISO] Flags de início/fim não encontradas ou incorretas.")
        meio = lista_bytes

    dados_desenquadrados = []
    i = 0
    while i < len(meio):
        byte_atual = meio[i]
        
        if byte_atual == ESC_BYTE_INT:
            # Encontrou ESC: O próximo byte é um dado literal
            i += 1
            if i < len(meio):
                dados_desenquadrados.append(meio[i])
            else:
                print("[ERRO] Caractere de escape no final do quadro.")
        elif byte_atual == FLAG_BYTE_INT:
            print("[AVISO] Flag encontrada no meio dos dados sem escape.")
            dados_desenquadrados.append(byte_atual)
        else:
            # Byte normal
            dados_desenquadrados.append(byte_atual)
        i += 1

    return _lista_de_bytes_para_bits(dados_desenquadrados)


# --- Constante para Bit Stuffing ---
FLAG_BITS = '01111110'

def desenquadrar_bit_stuffing(quadro_bits: str) -> str:
    """
    Desenquadra dados usando Bit Stuffing.
    Remove o '0' inserido após cinco '1's consecutivos.
    """
    print("[RX-Desenquadramento] Bit Stuffing")
    
    # Remove flags se estiverem presentes nas extremidades
    dados_processar = quadro_bits
    if dados_processar.startswith(FLAG_BITS):
        dados_processar = dados_processar[len(FLAG_BITS):]
    if dados_processar.endswith(FLAG_BITS):
        dados_processar = dados_processar[:-len(FLAG_BITS)]
        
    dados_saida = ""
    contagem_uns = 0
    i = 0
    
    while i < len(dados_processar):
        bit = dados_processar[i]
        
        if bit == '1':
            contagem_uns += 1
            dados_saida += '1'
            i += 1
        else: # bit == '0'
            if contagem_uns == 5:
                # Este '0' foi inserido pelo stuffing. Deve ser removido.
                contagem_uns = 0
                i += 1 
            else:
                # É um '0' normal
                contagem_uns = 0
                dados_saida += '0'
                i += 1
                
    return dados_saida


# -------------------------------------------------------------------
# Seção 3: DETECÇÃO DE ERROS (ERROR DETECTION)
# -------------------------------------------------------------------

def verificar_paridade_par(bits_recebidos: str) -> tuple[bool, str]:
    """
    Verifica a paridade par.
    Retorna: (True se válido/False se inválido, dados_sem_o_bit_paridade)
    
    Nota: Esta função remove o padding de alinhamento indesejado no início, 
    que foi inserido pelo TX para garantir que a Contagem de Caracteres funcione.
    """
    print("[RX-Detecção] Verificando Paridade Par...")
    
    if not bits_recebidos:
        return False, ""

    # 1. Verificação da Paridade (em todos os bits recebidos)
    paridade = 0
    for bit in bits_recebidos:
        paridade ^= int(bit)
        
    valido = paridade == 0
    
    # 2. Remoção do Bit de Paridade (último bit)
    dados_com_padding = bits_recebidos[:-1]
    
    # 3. Remoção do Padding de Alinhamento 
    dados_finais = dados_com_padding[7:]
    
    if not valido:
        print("[ERRO] Falha na verificação de paridade.")
    
    return valido, dados_finais


def verificar_checksum(bits_com_checksum: str) -> tuple[bool, str]:
    """
    Verifica o Checksum em blocos de 8 bits.
    A soma de todos os blocos (dados + checksum) deve resultar em 0xFF.
    Retorna: (True se válido/False se inválido, dados_sem_o_checksum)
    """
    print("[RX-Detecção] Verificando Checksum 8-bit...")

    if len(bits_com_checksum) % 8 != 0 or len(bits_com_checksum) < 16:
        print("[ERRO] Quadro incompleto ou desalinhado para verificação de Checksum.")
        return False, bits_com_checksum

    soma = 0
    # 1. Soma TODOS os blocos, INCLUINDO o checksum (último bloco)
    for i in range(0, len(bits_com_checksum), 8):
        bloco = bits_com_checksum[i:i+8]
        soma += int(bloco, 2)
        
    # 2. Trata o "carry" (enrola o estouro)
    while (soma >> 8) > 0:
        soma = (soma & 0xFF) + (soma >> 8)
        
    dados_originais = bits_com_checksum[:-8] # Remove os 8 bits de checksum
    
    # 3. Verificação: Se a soma final (complemento de 1) for 0xFF (todos os bits '1'), está correto.
    if soma == 0xFF:
        return True, dados_originais
    else:
        print(f"[ERRO] Falha na verificação de Checksum. Soma final: {format(soma, '08b')}")
        return False, dados_originais


POLI_CRC32 = 0x104C11DB7

def verificar_crc32(bits_recebidos: str) -> bool:
    """
    Verifica se o CRC-32 é válido.
    Recebe a mensagem completa (Dados + Padding + CRC).
    Retorna True se o resto da divisão for 0.
    """
    print("[RX-Detecção] Verificando CRC-32...")
    try:
        dados_int = int(bits_recebidos, 2)
    except ValueError:
        return False
        
    msb_index = dados_int.bit_length() - 1
    
    for i in range(msb_index, 31, -1):
        if (dados_int >> i) & 1:
            # Alinha o MSB do polinômio (bit 32) com o bit atual (i)
            dados_int ^= POLI_CRC32 << (i - 32)
            
    return dados_int == 0

def remover_crc_e_padding(bits_recebidos: str, pad_len: int = 0) -> str:
    """
    Função utilitária para remover o CRC (32 bits) e o Padding (opcional).
    Deve ser chamada apenas se o CRC for validado.
    """
    # Remove os últimos 32 bits (CRC)
    sem_crc = bits_recebidos[:-32]
    
    # Remove o padding, se houver
    if pad_len > 0:
        # O padding está no final dos dados, antes do CRC
        return sem_crc[:-pad_len]
    
    return sem_crc


# -------------------------------------------------------------------
# Seção 4: CORREÇÃO DE ERROS (ERROR CORRECTION)
# -------------------------------------------------------------------

def receptor_hamming(bits_recebidos: str) -> tuple[str, int]:
    """
    Verifica e corrige 1 bit de erro usando Hamming.
    Retorna: (dados_corrigidos_sem_bits_controle, posicao_erro)
    
    posicao_erro = 0 se não houver erro.
    Se houver erro, corrige internamente antes de retornar.
    """
    print("[RX-Correção] Hamming: Verificando...")
    
    # Adiciona um placeholder no índice 0 para facilitar a matemática (1-based)
    codigo_recebido = [''] + list(bits_recebidos)
    n = len(bits_recebidos)
    
    # Calcula a Síndrome (posição do erro)
    posicao_erro = 0
    
    # Descobre quantos bits de paridade 'r' existem no quadro
    num_r = n.bit_length() 
    
    # Verifica paridade para cada bit de controle (potências de 2: 1, 2, 4, 8...)
    for i in range(num_r):
        pos_paridade = 2**i
        if pos_paridade > n:
            break
            
        xor_soma = 0
        # Verifica os bits cobertos por esta paridade
        for j in range(1, n + 1):
            # Se o bit 'j' é coberto pela paridade 'i' (bitwise AND)
            if (j >> i) & 1:
                if codigo_recebido[j] != '':
                    xor_soma ^= int(codigo_recebido[j])
        
        # Se a soma for ímpar (1), adiciona o peso desta paridade à síndrome
        if xor_soma != 0:
            posicao_erro += pos_paridade
            
    # Correção
    if posicao_erro != 0:
        if posicao_erro <= n:
            print(f"[RX-Correção] ERRO DETECTADO na posição {posicao_erro}. Corrigindo...")
            # Inverte o bit
            bit_atual = codigo_recebido[posicao_erro]
            codigo_recebido[posicao_erro] = '0' if bit_atual == '1' else '1'
        else:
            print(f"[RX-Correção] Erro detectado na posição {posicao_erro} (fora do quadro). Impossível corrigir.")
    else:
        print("[RX-Correção] Nenhum erro detectado.")

    # Extração dos dados (Remove bits de paridade)
    dados_originais = ''
    for i in range(1, n + 1):
        # Se 'i' NÃO é potência de 2, é bit de dados
        if not _e_potencia_de_2(i):
            dados_originais += codigo_recebido[i]
            
    return dados_originais, posicao_erro
