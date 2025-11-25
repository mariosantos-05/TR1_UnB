import pickle
import socket
from typing import List


from CamadaFisica.modulacao_demodulacao_digital import (
    NRZ_polar_demodulation, bipolar_demodulation,
    manchester_demodulation_correlator
)
from CamadaFisica.modulacao_demodulacao_portadora import (
    ASK_demodulation, FSK_demodulation, QAM16_demodulation
)
from CamadaEnlace.enlace_receptor import (
    receptor_hamming, verificar_paridade_par, verificar_crc32,
    desenquadrar_contagem_caracteres, desenquadrar_bit_stuffing,
    desenquadrar_byte_stuffing, remover_crc_e_padding
)



class Receptor:
    def __init__(self, enquadramento, correcao, deteccao, mod_digital, mod_portadora):
        self.enquadramento = enquadramento
        self.correcao = correcao
        self.deteccao = deteccao
        self.mod_digital = mod_digital
        self.mod_portadora = mod_portadora

    def processar(self, sinal: List[float]) -> str:

        etapas_rx = {}
        etapas_rx["recebido"] = sinal

        if self.mod_digital != "8QAM":
            if self.mod_portadora == "ASK":
                sinal = ASK_demodulation(sinal)
            elif self.mod_portadora == "FSK":
                sinal = FSK_demodulation(sinal)

        if self.mod_digital == "NRZ":
            bits = NRZ_polar_demodulation(sinal)
        elif self.mod_digital == "bipolar":
            bits = bipolar_demodulation(sinal)
        elif self.mod_digital == "manchester":
            bits = manchester_demodulation_correlator(sinal)
        elif self.mod_digital == "8QAM":
            bits = QAM16_demodulation(sinal)

        etapas_rx["demodulado"] = bits

        bits = "".join(str(b) for b in bits)
        etapas_rx["bits"] = bits

        if self.deteccao == "paridade":
            verificar_paridade_par(bits)
        elif self.deteccao == "crc":
            verificar_crc32(bits)
            bits = remover_crc_e_padding(bits)

        if self.correcao == "hamming":
            bits = receptor_hamming(bits)

        if self.enquadramento == "contagem":
            bits = desenquadrar_contagem_caracteres(bits)
        elif self.enquadramento == "bit-stuffing":
            bits = desenquadrar_bit_stuffing(bits)
        elif self.enquadramento == "byte-stuffing":
            bits = desenquadrar_byte_stuffing(bits)

        self.etapas_rx = etapas_rx
        return bits

def bits_para_bytes(bit_str):
    #assert len(bit_str) % 8 == 0
    byte_list = [
        int(bit_str[i:i+8], 2)
        for i in range(0, len(bit_str), 8)
    ]
    return bytes(byte_list)

def receber_via_socket():
    HOST = "localhost"
    PORT = 5000

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)

    print(f"[Receptor] Esperando conexões na porta {PORT}...")

    while True:
        conn, addr = server.accept()
        print(f"[Receptor] Conectado a {addr}")

        dados = b""
        while True:
            parte = conn.recv(1024)
            if not parte:
                break
            dados += parte

        pacotao = pickle.loads(dados)

        rx = Receptor(
            pacotao["enq"], pacotao["cor"], pacotao["det"],
            pacotao["mod_dig"], pacotao["mod_por"]
        )

        mensagem_bits = rx.processar(pacotao["msg"])
        mensagem_bytes = bits_para_bytes(mensagem_bits)

        try:
            mensagem_final = mensagem_bytes.decode("utf-8")
        except UnicodeDecodeError:
            mensagem_final = mensagem_bytes.decode("utf-8", errors="replace")

        resposta = pickle.dumps({
            "mensagem": mensagem_final,
            "etapas_rx": rx.etapas_rx,
            "etapas_tx": pacotao["etapas_tx"]
        })

        conn.sendall(resposta)
        conn.close()
