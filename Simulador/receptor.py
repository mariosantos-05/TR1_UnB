from typing import List
import socket
import pickle

from CamadaFisica.fisica_receptor import (
    decode_NRZ, decode_bipolar, decode_manchester,
    decode_ASK, decode_FSK, decode_PSK, decode_QPSK, decode_16QAM
)
from CamadaEnlace.enlace_receptor import (
    receptor_hamming, verificar_paridade_par, verificar_crc32,
    desenquadrar_contagem_caracteres, desenquadrar_bit_stuffing, desenquadrar_byte_stuffing,
    remover_crc_e_padding, verificar_checksum
)

DEBUG = False

def debug(*msg):
    if DEBUG:
        print("[DEBUG RX]", *msg)
class Receptor:
    def __init__(self, enquadramento="contagem", correcao="hamming",
                 deteccao="crc", mod_digital="NRZ", mod_portadora="ASK"):
        self.enquadramento = enquadramento
        self.correcao = correcao
        self.deteccao = deteccao
        self.mod_digital = mod_digital
        self.mod_portadora = mod_portadora

    def processar(self, dados: List[int]) -> str:
        debug("--- Início do processamento no receptor ---")

        etapas_rx = {"recebido": dados}
        dados = self._processar_demodulacao(dados, etapas_rx)
        dados = self._processar_deteccao_correcao(dados, etapas_rx)
        dados = self._processar_desenquadramento(dados, etapas_rx)

        self.etapas_rx = etapas_rx

        debug("--- Fim do processamento no receptor ---")
        return dados

    def _processar_demodulacao(self, dados: List[int], etapas_rx: dict) -> str:

        if self.mod_digital != "16QAM":
            dados = self._demodular_portadora(dados)
            debug(f"Após demodulação portadora {self.mod_portadora}: {dados}")

        dados = self._demodular_digital(dados)
        etapas_rx["demodulado"] = dados

        dados_str = ''.join(map(str, dados))
        etapas_rx["bits_puros"] = dados_str

        debug("Bits puros:", dados_str)

        return dados_str

    def _demodular_portadora(self, dados):
        if self.mod_portadora == "QPSK":
            return decode_QPSK(dados)
        if self.mod_portadora == "16QAM":
            return decode_16QAM(dados)
        if self.mod_portadora == "ASK":
            return decode_ASK(dados)
        if self.mod_portadora == "FSK":
            return decode_FSK(dados)
        if self.mod_portadora == "PSK":
            return decode_PSK(dados)
        return dados

    def _demodular_digital(self, dados: List[int]) -> List[int]:

        if self.mod_portadora in ["QPSK", "16QAM"]:
            return dados  # Sem demodulação digital nessas modulações

        demoduladores = {
            "NRZ": (decode_NRZ, "NRZ"),
            "bipolar": (decode_bipolar, "bipolar"),
            "manchester": (decode_manchester, "manchester"),
        }

        if self.mod_digital in demoduladores:
            func, nome = demoduladores[self.mod_digital]
            debug(f"Demodulando digital ({nome})...")
            dados = func(dados)
            debug(f"Após demodulação digital {nome}: {dados}")

        return dados

    def _processar_deteccao_correcao(self, dados: str, etapas_rx: dict) -> str:
        dados = self._aplicar_deteccao_erros(dados, etapas_rx)
        dados = self._aplicar_correcao_erros(dados, etapas_rx)

        debug("Após correção e remoção de bits extras:", dados)
        return dados

    def _aplicar_deteccao_erros(self, dados: str, etapas_rx: dict) -> str:

        
        if self.deteccao == "paridade":
            if not verificar_paridade_par(dados):
                debug("Erro de paridade detectado.")
            etapas_rx["removido_paridade"] = dados
            return (dados)[:-1]  # Remove o bit de paridade

        
        elif self.deteccao == "crc":
            if not verificar_crc32(dados):
                debug("Erro de CRC detectado.")
                dados_sem_crc = remover_crc_e_padding(dados)
                debug("Tamanho pós remover CRC:", len(dados_sem_crc))
                return dados_sem_crc
            else:
                debug("CRC verificado com sucesso.")
                dados_sem_crc = remover_crc_e_padding(dados)
                etapas_rx["removido_crc"] = dados_sem_crc
                debug("Tamanho pós remover CRC:", len(dados_sem_crc))
                return dados_sem_crc

        
        elif self.deteccao == "checksum":
            ok, dados_sem_checksum = verificar_checksum(dados)
            if not ok:
                debug("Erro: checksum inválido.")
                etapas_rx["erro_checksum"] = dados
                return None
            else:
                debug("Checksum verificado com sucesso.")
                etapas_rx["removido_checksum"] = dados_sem_checksum
                return dados_sem_checksum

        return dados

    def _aplicar_correcao_erros(self, dados: str, etapas_rx: dict) -> str:
        if self.correcao == "hamming":
            dados_corrigidos = receptor_hamming(dados)
            etapas_rx["corrigido_hamming"] = dados_corrigidos
            debug("Tamanho pós Hamming:", len(dados_corrigidos))
            return dados_corrigidos
        return dados

    def _processar_desenquadramento(self, dados: str, etapas_rx: dict) -> str:

        desenquadradores = {
            "contagem": (desenquadrar_contagem_caracteres, "contagem"),
            "bit-stuffing": (desenquadrar_bit_stuffing, "bit-stuffing"),
            "byte-stuffing": (desenquadrar_byte_stuffing, "byte-stuffing")
        }

        if self.enquadramento in desenquadradores:
            func, nome = desenquadradores[self.enquadramento]
            debug(f"Desenquadrando ({nome})...")
            dados_desenquadrados = func(dados)
            etapas_rx["desenquadrado"] = dados_desenquadrados
            debug(f"Após desenquadramento {nome}: {dados_desenquadrados}")
            return dados_desenquadrados

        return dados

def bits_para_bytes(bit_str: str) -> bytes:
    return bytes(int(bit_str[i:i+8], 2) for i in range(0, len(bit_str), 8))

def receber_via_socket(enquadramento: str, correcao: str, deteccao: str,
                       mod_digital: str, mod_portadora: str) -> None:

    HOST = 'localhost'
    PORT = 5000

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)

    print(f"[Receptor] Aguardando conexão na porta {PORT}...")

    while True:
        conn, addr = server.accept()
        print(f"[Receptor] Conectado a {addr}")

        dados_completos = b''
        while True:
            parte = conn.recv(1024)
            if not parte:
                break
            dados_completos += parte

        pacotao = pickle.loads(dados_completos)
        sinal_recebido = pacotao["msg"]

        print(f"Tamanho sinal recebido: {len(sinal_recebido)}")

        rx = Receptor(
            pacotao["enq"], pacotao["cor"], pacotao["det"],
            pacotao["mod_dig"], pacotao["mod_por"]
        )

        mensagem_recebida = rx.processar(sinal_recebido)

        print(f"Tamanho mensagem recebida: {len(mensagem_recebida)}")

        mensagem_bytes = bits_para_bytes(mensagem_recebida)

        try:
            mensagem_decodificada = mensagem_bytes.decode('utf-8')
        except UnicodeDecodeError:
            print("[WARNING] UTF-8 inválido — substituindo erros.")
            mensagem_decodificada = mensagem_bytes.decode('utf-8', errors='replace')

        print(f"[Receptor] Recebido: {mensagem_decodificada}")

        resposta = pickle.dumps({
            "mensagem": mensagem_decodificada,
            "etapas_tx": pacotao.get("etapas_tx", {}),
            "etapas_rx": rx.etapas_rx
        })

        conn.sendall(resposta)
        conn.close()

    server.close()


# Alias para manter compatibilidade
receber_via_Socket = receber_via_socket
