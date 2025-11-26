from typing import List
import random
import pickle
import socket

from CamadaFisica.modulacao_demodulacao_digital import (
    encode_NRZ, encode_bipolar, encode_manchester,
    encode_ASK, encode_FSK, encode_8QAM
)
from CamadaEnlace.enlace_transmissor import (
    transmissor_hamming, adicionar_paridade_par, crc32,
    enquadrar_contagem_caracteres, enquadrar_bit_stuffing, enquadrar_byte_stuffing
)


class Transmissor:
    def __init__(self, enquadramento="contagem", correcao="hamming", deteccao="crc32",
                 mod_digital="NRZ", mod_portadora="ASK", noise_level=0.0):
        self.enquadramento = enquadramento
        self.correcao = correcao
        self.deteccao = deteccao
        self.mod_digital = mod_digital
        self.mod_portadora = mod_portadora
        self.noise_level = noise_level

    def aplicar_ruido(self, dados_bits: str) -> str:
        """
        Simula ruído bit a bit, invertendo bits com probabilidade igual à taxa de ruído.
        """
        if self.noise_level <= 0.0:
            return dados_bits  # nada de ruído

        resultado = []
        for b in dados_bits:
            if random.random() < self.noise_level:
                resultado.append('1' if b == '0' else '0')
            else:
                resultado.append(b)
        return ''.join(resultado)

    def processar(self, dados: str) -> List[float]:
        print("\n[DEBUG TX] --- Início do processamento no transmissor ---")
        print("[DEBUG TX] Mensagem original:", dados)

        etapas = {}  # dicionário para registrar cada etapa da transmissão
        etapas["original"] = dados

        # Enquadramento
        if self.enquadramento == "contagem":
            dados = enquadrar_contagem_caracteres(dados)
            etapas["enquadrado"] = dados
            print("contagem")
        elif self.enquadramento == "bit-stuffing":
            dados = enquadrar_bit_stuffing(dados)
            print('bit-stuffing')
        elif self.enquadramento == "byte-stuffing":
            dados = enquadrar_byte_stuffing(dados)
            print("byte-stuffing")

        print("[DEBUG TX] Após enquadramento:", dados)
        print("[DEBUG TX] Qtdd de bits:", len(dados))

        # Correção de Erros
        if self.correcao == "hamming":
            print("[DEBUG TX] Tamanho pré Hamming:", len(dados))
            dados = transmissor_hamming(dados)
            etapas["hamming"] = dados
            print("[DEBUG TX] Após aplicação de Hamming:", dados)

        # Detecção de Erros
        if self.deteccao == "paridade":
            dados = adicionar_paridade_par(dados)
            etapas["paridade"] = dados
            print("[DEBUG TX] Após adição de bit de paridade:", dados)
        elif self.deteccao == "crc32":
            print("[DEBUG TX] Tamanho pré crc32:", len(dados))
            dados = crc32(dados)
            print("[DEBUG TX] Após adição de crc32:", dados)

        # Simula ruído nos bits
        dados = self.aplicar_ruido(dados)
        etapas["com_ruido"] = dados
        print(f"[DEBUG TX] Após simulação de ruído (nível = {self.noise_level}):", dados)

        # Modulação
        if self.mod_digital == "NRZ":
            resultado = encode_NRZ(dados)
        elif self.mod_digital == "bipolar":
            resultado = encode_bipolar(dados)
        elif self.mod_digital == "manchester":
            resultado = encode_manchester(dados)
        elif self.mod_digital == "8QAM":
            resultado = encode_8QAM(dados)

        print(f"[DEBUG TX] Modulação digital {self.mod_digital} realizada")

        if self.mod_digital != "8QAM":
            if self.mod_portadora == "ASK":
                resultado = encode_ASK(resultado)
            elif self.mod_portadora == "FSK":
                resultado = encode_FSK(resultado)
            print(f"[DEBUG TX] Modulação portadora {self.mod_portadora} realizada")

        self.etapas = etapas  # armazena as etapas para uso posterior

        print("[DEBUG TX] --- Fim do processamento no transmissor ---\n")
        return resultado


def transmitir_via_Socket(mensagem: str, enquadramento: str, correcao: str, deteccao: str,
                          mod_digital: str, mod_portadora: str, noise_level: float = 0.0):
    HOST = 'localhost'
    PORT = 5000

    mensagem_em_bytes = mensagem.encode()
    mensagem_em_bits = ''.join(f'{byte:08b}' for byte in mensagem_em_bytes)

    # inicializando o transmissor com noise_level
    tx = Transmissor(enquadramento, correcao, deteccao, mod_digital, mod_portadora, noise_level)

    # processando a mensagem
    sinal_a_transmitir = tx.processar(mensagem_em_bits)
    print(sinal_a_transmitir)

    pacotao = {
        "msg": sinal_a_transmitir,
        "enq": enquadramento,
        "cor": correcao,
        "det": deteccao,
        "mod_dig": mod_digital,
        "mod_por": mod_portadora,
        "noise_level": noise_level
    }

    sinal_a_transmitir_em_bytes = pickle.dumps(pacotao)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    client.sendall(sinal_a_transmitir_em_bytes)
    client.shutdown(socket.SHUT_WR)
    print(f"[Transmissor] Enviado: {sinal_a_transmitir_em_bytes}")

    dados_resposta = b''
    while True:
        parte = client.recv(1024)
        if not parte:
            break
        dados_resposta += parte

    mensagem_recebida = pickle.loads(dados_resposta)

    client.close()

    return mensagem_recebida
