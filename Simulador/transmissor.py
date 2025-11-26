from typing import List
import random
import pickle
import socket

from CamadaFisica.fisica_transmissor import (
    encode_NRZ, encode_bipolar, encode_manchester,
    encode_ASK, encode_FSK, encode_PSK, encode_QPSK, encode_16QAM,
)
from CamadaEnlace.enlace_transmissor import (
    transmissor_hamming, adicionar_paridade_par, crc32,adicionar_checksum,
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
            return dados_bits

        resultado = []
        for bit in dados_bits:
            if random.random() < self.noise_level:
                resultado.append('1' if bit == '0' else '0')
            else:
                resultado.append(bit)
        return ''.join(resultado)

    def processar(self, dados: str) -> List[float]:
        print("\n[DEBUG TX] --- Início do processamento no transmissor ---")
        print("[DEBUG TX] Mensagem original:", dados)

        etapas = {"original": dados}
        dados = self._processar_enquadramento(dados, etapas)
        dados = self._processar_correcao_erros(dados, etapas)
        dados = self._processar_deteccao_erros(dados, etapas)
        dados = self._aplicar_ruido_e_registrar(dados, etapas)
        resultado = self._processar_modulacao(dados, etapas)

        self.etapas = etapas
        print("[DEBUG TX] --- Fim do processamento no transmissor ---\n")
        return resultado

    def _processar_enquadramento(self, dados: str, etapas: dict) -> str:
        """Aplica enquadramento nos dados"""
        enquadradores = {
            "contagem": (enquadrar_contagem_caracteres, "contagem"),
            "bit-stuffing": (enquadrar_bit_stuffing, "bit-stuffing"),
            "byte-stuffing": (enquadrar_byte_stuffing, "byte-stuffing")
        }

        if self.enquadramento in enquadradores:
            enquad_func, debug_msg = enquadradores[self.enquadramento]
            print(debug_msg)
            dados_enquadrados = enquad_func(dados)
            etapas["enquadrado"] = dados_enquadrados
            
            print("[DEBUG TX] Após enquadramento:", dados_enquadrados)
            print("[DEBUG TX] Qtdd de bits:", len(dados_enquadrados))
            return dados_enquadrados
        
        return dados

    def _processar_correcao_erros(self, dados: str, etapas: dict) -> str:
        """Aplica correção de erros (Hamming)"""
        if self.correcao == "hamming":
            print("[DEBUG TX] Tamanho pré Hamming:", len(dados))
            dados_hamming = transmissor_hamming(dados)
            etapas["hamming"] = dados_hamming
            print("[DEBUG TX] Após aplicação de Hamming:", dados_hamming)
            return dados_hamming
        return dados

    def _processar_deteccao_erros(self, dados: str, etapas: dict) -> str:
        """Aplica detecção de erros (paridade ou CRC)"""
        if self.deteccao == "paridade":
            dados_paridade = adicionar_paridade_par(dados)
            etapas["paridade"] = dados_paridade
            print("[DEBUG TX] Após adição de bit de paridade:", dados_paridade)
            return dados_paridade
        
        elif self.deteccao == "crc":
            print("[DEBUG TX] Tamanho pré crc32:", len(dados))
            dados_crc = crc32(dados)
            print("[DEBUG] DADOS ENTRADA :", dados)
            print("[DEBUG] DADOS CRC     :", dados_crc)
            print("[DEBUG] LEN ANTES     :", len(dados))
            print("[DEBUG] LEN DEPOIS    :", len(dados_crc))
            print("[DEBUG TX] Após adição de crc32:", dados_crc)
            return dados_crc
        elif self.deteccao == "checksum":
            dados_checksum = adicionar_checksum(dados)
            return dados_checksum
            
        
        return dados

    def _aplicar_ruido_e_registrar(self, dados: str, etapas: dict) -> str:
        """Aplica ruído e registra o resultado"""
        dados_com_ruido = self.aplicar_ruido(dados)
        etapas["com_ruido"] = dados_com_ruido
        #print(f"[DEBUG TX] Após simulação de ruído (nível = {self.noise_level}):", dados_com_ruido)
        return dados_com_ruido

    def _processar_modulacao(self, dados: str, etapas: dict) -> List[float]:

        # Se a modulação de portadora for QPSK, NÃO modula digitalmente antes
        if self.mod_portadora == "QPSK":
            resultado = dados  # mantém bits puros
        if self.mod_portadora == "16QAM":
            resultado = dados  # mantém bits puros
        else:
            moduladores_digital = {
                "NRZ": (encode_NRZ, "NRZ"),
                "bipolar": (encode_bipolar, "bipolar"),
                "manchester": (encode_manchester, "manchester"),
            }

            if self.mod_digital in moduladores_digital:
                mod_func, mod_name = moduladores_digital[self.mod_digital]
                resultado = mod_func(dados)
                print(f"[DEBUG TX] Modulação digital {mod_name} realizada")
            else:
                resultado = dados

        # Agora sim aplica modulação de portadora
        resultado = self._aplicar_modulacao_portadora(resultado)
        return resultado


    def _aplicar_modulacao_portadora(self, dados: List[float]) -> List[float]:
        """Aplica modulação de portadora"""
        if self.mod_portadora == "ASK":
            resultado = encode_ASK(dados)
            print("[DEBUG TX] Modulação portadora ASK realizada")
        elif self.mod_portadora == "FSK":
            resultado = encode_FSK(dados)
            print("[DEBUG TX] Modulação portadora FSK realizada")
        elif self.mod_portadora == "PSK":
            resultado = encode_PSK(dados)
            print("[DEBUG TX] Modulação portadora PSK realizada")
        elif self.mod_portadora == "QPSK":
            resultado = encode_QPSK(dados)
            print("[DEBUG TX] Modulação portadora QPSK realizada")
        elif self.mod_portadora == "16QAM":
            resultado = encode_16QAM(dados)
        else:
            resultado = dados
        
        return resultado


def transmitir_via_socket(mensagem: str, enquadramento: str, correcao: str, deteccao: str,
                          mod_digital: str, mod_portadora: str, noise_level: float = 0.0) -> dict:
    """Transmite mensagem via socket usando o protocolo definido"""
    HOST = 'localhost'
    PORT = 5000

    # Converte mensagem para bits
    mensagem_em_bytes = mensagem.encode()
    mensagem_em_bits = ''.join(f'{byte:08b}' for byte in mensagem_em_bytes)

    # Processa a mensagem no transmissor
    tx = Transmissor(enquadramento, correcao, deteccao, mod_digital, mod_portadora, noise_level)
    sinal_a_transmitir = tx.processar(mensagem_em_bits)
    print(sinal_a_transmitir)

    # Prepara pacote para transmissão
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

    # Transmite via socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    client.sendall(sinal_a_transmitir_em_bytes)
    client.shutdown(socket.SHUT_WR)
    print(f"[Transmissor] Dados enviados via socket")

    # Recebe resposta
    dados_resposta = b''
    while True:
        parte = client.recv(1024)
        if not parte:
            break
        dados_resposta += parte

    mensagem_recebida = pickle.loads(dados_resposta)
    client.close()

    return mensagem_recebida


# Alias para manter compatibilidade
transmitir_via_Socket = transmitir_via_socket