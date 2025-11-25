from typing import List
import random
import pickle
import socket

# -----------------------------
# Camada Física (modulação)
# -----------------------------
from CamadaFisica.modulacao_demodulacao_digital import (
    NRZ_polar_modulation, bipolar_modulation, manchester_modulation,
)

from CamadaFisica.modulacao_demodulacao_portadora import (
    ASK_modulation, FSK_modulation, QAM16_modulation
)

# -----------------------------
# Camada de Enlace
# -----------------------------
from CamadaEnlace.enlace_transmissor import (
    transmissor_hamming, adicionar_paridade_par, crc32,
    enquadrar_contagem_caracteres, enquadrar_bit_stuffing, enquadrar_byte_stuffing
)


# ==========================================================
# ===== Funções auxiliares de transmissão confiável ========
# ==========================================================
def send_with_length(sock, data_bytes):
    """Envia primeiro o comprimento (4 bytes big-endian), depois os dados."""
    size = len(data_bytes)
    sock.sendall(size.to_bytes(4, "big"))
    sock.sendall(data_bytes)


def recv_all(sock, length):
    """Garante receber exatamente 'length' bytes."""
    data = b''
    while len(data) < length:
        parte = sock.recv(length - len(data))
        if not parte:
            return None
        data += parte
    return data


# ==========================================================
# ===================== CLASSE TRANSMISSOR =================
# ==========================================================
class Transmissor:
    def __init__(self, enquadramento="contagem", correcao="hamming",
                 deteccao="crc", mod_digital="NRZ", mod_portadora="ASK",
                 noise_level=0.0):

        self.enquadramento = enquadramento
        self.correcao = correcao
        self.deteccao = deteccao
        self.mod_digital = mod_digital
        self.mod_portadora = mod_portadora
        self.noise_level = noise_level

    # ---------------------------------------------------------
    # Aplica ruído bit a bit (flip 0/1) com probabilidade p
    # ---------------------------------------------------------
    def aplicar_ruido(self, dados_bits: str) -> str:
        if self.noise_level <= 0.0:
            return dados_bits
        resultado = []
        for b in dados_bits:
            if random.random() < self.noise_level:
                resultado.append('1' if b == '0' else '0')
            else:
                resultado.append(b)
        return ''.join(resultado)

    # ---------------------------------------------------------
    # PROCESSAMENTO COMPLETO
    # ---------------------------------------------------------
    def processar(self, dados: str) -> List[float]:
        etapas = {}
        etapas["original"] = dados

        # ---------------------------
        # ENQUADRAMENTO
        # ---------------------------
        if self.enquadramento == "contagem":
            dados = enquadrar_contagem_caracteres(dados)
        elif self.enquadramento == "bit-stuffing":
            dados = enquadrar_bit_stuffing(dados)
        elif self.enquadramento == "byte-stuffing":
            dados = enquadrar_byte_stuffing(dados)

        etapas["enquadrado"] = dados

        # ---------------------------
        # CORREÇÃO (Hamming)
        # ---------------------------
        if self.correcao == "hamming":
            dados = transmissor_hamming(dados)
            etapas["hamming"] = dados

        # ---------------------------
        # DETECÇÃO DE ERROS
        # ---------------------------
        if self.deteccao == "paridade":
            dados = adicionar_paridade_par(dados)
        elif self.deteccao == "crc":
            dados = crc32(dados)

        # ---------------------------
        # Ruído opcional
        # ---------------------------
        dados = self.aplicar_ruido(dados)
        etapas["com_ruido"] = dados

        # ---------------------------
        # MODULAÇÃO DIGITAL
        # ---------------------------
        if self.mod_digital == "NRZ":
            resultado = NRZ_polar_modulation(dados)
        elif self.mod_digital == "bipolar":
            resultado = bipolar_modulation(dados)
        elif self.mod_digital == "manchester":
            resultado = manchester_modulation(dados)
        elif self.mod_digital == "8QAM":
            resultado = QAM16_modulation(dados)  # sim, 16QAM = 8QAM na sua nomenclatura

        # ---------------------------
        # MODULAÇÃO POR PORTADORA
        # (exceto se já for 16QAM)
        # ---------------------------
        if self.mod_digital != "8QAM":
            if self.mod_portadora == "ASK":
                resultado = ASK_modulation(resultado)
            elif self.mod_portadora == "FSK":
                resultado = FSK_modulation(resultado)

        self.etapas = etapas
        return resultado


# ==========================================================
# FUNÇÃO PRINCIPAL DE TRANSMISSÃO VIA SOCKET
# ==========================================================
def transmitir_via_socket(
        mensagem: str,
        enquadramento="contagem",
        correcao="hamming",
        deteccao="crc",
        mod_digital="NRZ",
        mod_portadora="ASK",
        noise_level=0.0):

    HOST = "localhost"
    PORT = 5000

    # Converte a mensagem (string) para bits
    mensagem_bits = ''.join(f'{byte:08b}' for byte in mensagem.encode())

    # Instancia o transmissor
    tx = Transmissor(enquadramento, correcao, deteccao,
                     mod_digital, mod_portadora, noise_level)

    # Gera o sinal modulado final
    sinal = tx.processar(mensagem_bits)

    # Pacote a ser enviado
    pacote_envio = {
        "sinal": sinal,
        "enq": enquadramento,
        "cor": correcao,
        "det": deteccao,
        "mod_dig": mod_digital,
        "mod_por": mod_portadora,
        "noise": noise_level,
    }

    data = pickle.dumps(pacote_envio)

    # ------------------------
    # TRANSMISSÃO VIA SOCKET
    # ------------------------
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PORT))

    # envia Tamanho + Dados
    send_with_length(cliente, data)

    # ---------- Recebe resposta ----------
    # recebe tamanho
    raw_len = recv_all(cliente, 4)
    if raw_len is None:
        cliente.close()
        return {"erro": "Resposta vazia do receptor."}

    data_len = int.from_bytes(raw_len, "big")

    # recebe os bytes exatos
    resposta_raw = recv_all(cliente, data_len)
    cliente.close()

    return pickle.loads(resposta_raw)
