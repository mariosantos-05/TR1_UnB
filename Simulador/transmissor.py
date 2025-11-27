from typing import List
import random
import pickle
import socket
import numpy as np

from CamadaFisica.fisica_transmissor import (
    NRZ_polar_modulation, bipolar_modulation, manchester_modulation,
    ASK_modulation, FSK_modulation, PSK_modulation, QPSK_modulation, QAM16_modulation,
)
from CamadaEnlace.enlace_transmissor import (
    transmissor_hamming, adicionar_paridade_par, crc32, adicionar_checksum,
    enquadrar_contagem_caracteres, enquadrar_bit_stuffing, enquadrar_byte_stuffing
)

DEBUG = True

def debug(*msg):
    if DEBUG:
        print("[DEBUG TX]", *msg)

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
        if self.noise_level <= 0.0:
            return dados_bits

        resultado = []
        for bit in dados_bits:
            if random.random() < self.noise_level:
                resultado.append('1' if bit == '0' else '0')
            else:
                resultado.append(bit)
        return ''.join(resultado)

    def processar(self, dados: str) -> List[float]:
        debug("--- Início do processamento no transmissor ---")
        debug("Mensagem original:", dados)

        etapas = {"original": dados}
        dados = self._processar_enquadramento(dados, etapas)
        dados = self._processar_correcao_erros(dados, etapas)
        dados = self._processar_deteccao_erros(dados, etapas)
        dados = self._aplicar_ruido_e_registrar(dados, etapas)
        resultado = self._processar_modulacao(dados, etapas)

        self.etapas = etapas
        debug("--- Fim do processamento no transmissor ---")
        return resultado

    def _processar_enquadramento(self, dados: str, etapas: dict) -> str:
        enquadradores = {
            "contagem": enquadrar_contagem_caracteres,
            "bit-stuffing": enquadrar_bit_stuffing,
            "byte-stuffing": enquadrar_byte_stuffing
        }

        if self.enquadramento in enquadradores:
            debug("Aplicando enquadramento:", self.enquadramento)
            dados_enquadrados = enquadradores[self.enquadramento](dados)
            etapas["enquadrado"] = dados_enquadrados

            debug("Após enquadramento:", dados_enquadrados)
            debug("Qtdd de bits:", len(dados_enquadrados))
            return dados_enquadrados
        
        return dados

    def _processar_correcao_erros(self, dados: str, etapas: dict) -> str:
        if self.correcao == "hamming":
            debug("Tamanho pré Hamming:", len(dados))
            dados_hamming = transmissor_hamming(dados)
            etapas["hamming"] = dados_hamming
            debug("Após aplicação de Hamming:", dados_hamming)
            return dados_hamming
        
        return dados


    def _processar_deteccao_erros(self, dados: str, etapas: dict) -> str:
        if self.deteccao == "paridade":
            dados_paridade = adicionar_paridade_par(dados)
            etapas["paridade"] = dados_paridade
            debug("Após adição de paridade:", dados_paridade)
            return dados_paridade

        elif self.deteccao == "crc":
            debug("Tamanho pré CRC:", len(dados))
            dados_crc = crc32(dados)
            debug("Dados entrada:", dados)
            debug("Dados CRC:", dados_crc)
            debug("Len antes:", len(dados))
            debug("Len depois:", len(dados_crc))
            etapas["crc"] = dados_crc
            return dados_crc

        elif self.deteccao == "checksum":
            dados_checksum = adicionar_checksum(dados)
            etapas["checksum"] = dados_checksum
            debug("Após adição de checksum:", dados_checksum)
            return dados_checksum

        return dados


    def _aplicar_ruido_e_registrar(self, dados: str, etapas: dict) -> str:
        dados_com_ruido = self.aplicar_ruido(dados)
        etapas["com_ruido"] = dados_com_ruido
        debug(f"Após ruído (nível {self.noise_level}):", dados_com_ruido)
        return dados_com_ruido


    def _processar_modulacao(self, dados: str, etapas: dict) -> List[float]:

        if self.mod_portadora in ["QPSK", "16QAM"]:
            resultado = dados
        else:
            moduladores_digital = {
                "NRZ": NRZ_polar_modulation,
                "bipolar": bipolar_modulation,
                "manchester": manchester_modulation,
            }

            if self.mod_digital in moduladores_digital:
                resultado = moduladores_digital[self.mod_digital](dados)
                debug(f"Modulação digital {self.mod_digital} realizada")
            else:
                resultado = dados

        resultado = self._aplicar_modulacao_portadora(resultado)
        return resultado

    def _aplicar_modulacao_portadora(self, dados: List[float]) -> List[float]:
        if self.mod_portadora == "ASK":
            debug("Modulação portadora ASK realizada")
            resultado = ASK_modulation(dados) 
            return resultado + np.random.normal(loc=0, scale=1, size=len(resultado))
        elif self.mod_portadora == "FSK":
            debug("Modulação portadora FSK realizada")
            resultado = FSK_modulation(dados)
            return resultado + np.random.normal(loc=0, scale=1, size=len(resultado))
        elif self.mod_portadora == "PSK":
            debug("Modulação portadora PSK realizada")
            resultado = PSK_modulation(dados)
            return resultado + np.random.normal(loc=0, scale=1, size=len(resultado))
        elif self.mod_portadora == "QPSK":
            debug("Modulação portadora QPSK realizada")
            resultado = QPSK_modulation(dados)
            return resultado + np.random.normal(loc=0, scale=1, size=len(resultado))
        elif self.mod_portadora == "16QAM":
            debug("Modulação portadora 16QAM realizada")
            resultado = QAM16_modulation(dados)
            return resultado + np.random.normal(loc=0, scale=1, size=len(resultado))

        return dados

def transmitir_via_socket(mensagem: str, enquadramento: str, correcao: str, deteccao: str,
                          mod_digital: str, mod_portadora: str, noise_level: float = 0.0) -> dict:

    PORT = 5000
    HOST = 'localhost'

    mensagem_em_bits = ''.join(f'{byte:08b}' for byte in mensagem.encode())

    tx = Transmissor(enquadramento, correcao, deteccao, mod_digital, mod_portadora, noise_level)
    sinal_a_transmitir = tx.processar(mensagem_em_bits)

    pacotao = {
        "msg": sinal_a_transmitir,
        "enq": enquadramento,
        "cor": correcao,
        "det": deteccao,
        "mod_dig": mod_digital,
        "mod_por": mod_portadora,
        "noise_level": noise_level,
        "etapas_tx": tx.etapas
    }

    sinal_a_transmitir_em_bytes = pickle.dumps(pacotao)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    client.sendall(sinal_a_transmitir_em_bytes)
    client.shutdown(socket.SHUT_WR)
    print("[Transmissor] Dados enviados via socket")

    dados_resposta = b''
    while True:
        parte = client.recv(1024)
        if not parte:
            break
        dados_resposta += parte

    client.close()
    return pickle.loads(dados_resposta)

transmitir_via_Socket = transmitir_via_socket
