from typing import List
import socket
import pickle

from CamadaFisica.fisica_receptor import (
    decode_NRZ, decode_bipolar, decode_manchester,
    decode_ASK, decode_FSK,decode_PSK, decode_QPSK,decode_16QAM
)
from CamadaEnlace.enlace_receptor import (
    receptor_hamming, verificar_paridade_par, verificar_crc32,
    desenquadrar_contagem_caracteres, desenquadrar_bit_stuffing, desenquadrar_byte_stuffing,
    remover_bit_paridade, remover_crc_e_padding,verificar_checksum
)


class Receptor:
    def __init__(self, enquadramento="contagem", correcao="hamming", 
                 deteccao="crc", mod_digital="NRZ", mod_portadora="ASK"):
        self.enquadramento = enquadramento
        self.correcao = correcao
        self.deteccao = deteccao
        self.mod_digital = mod_digital
        self.mod_portadora = mod_portadora

    def processar(self, dados: List[int]) -> str:
        print("\n[DEBUG] --- Início do processamento no receptor ---")
        
        etapas_rx = {"recebido": dados}
        dados = self._processar_demodulacao(dados, etapas_rx)
        dados = self._processar_deteccao_correcao(dados, etapas_rx)
        dados = self._processar_desenquadramento(dados, etapas_rx)
        
        self.etapas_rx = etapas_rx
        print("[DEBUG] --- Fim do processamento no receptor ---\n")
        return dados

    def _processar_demodulacao(self, dados: List[int], etapas_rx: dict) -> str:
        """Processa demodulação de portadora e digital"""
        if self.mod_digital != "16QAM":
            dados = self._demodular_portadora(dados)
            print(f"[DEBUG] Após demodulação portadora {self.mod_portadora}: {dados}")

        dados = self._demodular_digital(dados)
        etapas_rx["demodulado"] = dados
        
        # Transforma lista de bits em string
        dados_str = ''.join(map(str, dados))
        etapas_rx["bits_puros"] = dados_str
        print("[DEBUG] Em string de bits:", dados_str)
        
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
        if self.mod_portadora == "QPSK":
            return dados  
        if self.mod_portadora == "16QAM":
            return dados  
        demoduladores = {
            "NRZ": (decode_NRZ, "recebendo NRZ"),
            "bipolar": (decode_bipolar, "recebendo bipolar"),
            "manchester": (decode_manchester, "recebendo manchester"),
        }
        
        if self.mod_digital in demoduladores:
            demod_func, debug_msg = demoduladores[self.mod_digital]
            print(debug_msg)
            dados = demod_func(dados)
            print(f"[DEBUG] Após demodulação digital {self.mod_digital}: {dados}")
        
        return dados

    def _processar_deteccao_correcao(self, dados: str, etapas_rx: dict) -> str:
        """Processa detecção e correção de erros"""
        dados = self._aplicar_deteccao_erros(dados, etapas_rx)
        dados = self._aplicar_correcao_erros(dados, etapas_rx)
        print("[DEBUG] Após correção e remoção de bits extras:", dados)
        return dados

    def _aplicar_deteccao_erros(self, dados: str, etapas_rx: dict) -> str:
        """Aplica detecção de erros (paridade ou CRC)"""
        if self.deteccao == "paridade":
            if not verificar_paridade_par(dados):
                print("[DEBUG] Erro de paridade detectado.")
            etapas_rx["removido_paridade"] = dados
            return remover_bit_paridade(dados)

        elif self.deteccao == "crc":
            if not verificar_crc32(dados):
                print("[DEBUG] Erro de CRC detectado. Aplicando Hamming.")
                dados_sem_crc = remover_crc_e_padding(dados)
                print("[DEBUG] Tamanho depois de remover CRC:", len(dados_sem_crc))
                return dados_sem_crc
            else:
                print("[DEBUG] CRC verificado com sucesso.")
                dados_sem_crc = remover_crc_e_padding(dados)
                etapas_rx["removido_crc"] = dados_sem_crc
                print("[DEBUG] Tamanho depois de remover CRC:", len(dados_sem_crc))
                return dados_sem_crc
            
        elif self.deteccao == "checksum":
            ok, dados_sem_checksum = verificar_checksum(dados)
            if not ok:
                print("[ERRO] Checksum inválido. Descartando quadro.")
                # Não continue pipeline com dados corrompidos
                etapas_rx["erro_checksum"] = dados
                return None  # <-- o jeito certo de indicar falha
            else:
                print("[DEBUG] Checksum verificado com sucesso.")
                etapas_rx["removido_checksum"] = dados_sem_checksum
                return dados_sem_checksum
                
        
        return dados

    def _aplicar_correcao_erros(self, dados: str, etapas_rx: dict) -> str:
        """Aplica correção de erros (Hamming)"""
        if self.correcao == "hamming":
            dados_corrigidos = receptor_hamming(dados)
            etapas_rx["corrigido_hamming"] = dados_corrigidos
            print("[DEBUG] Tamanho depois de remover Hamming:", len(dados_corrigidos))
            return dados_corrigidos
        return dados

    def _processar_desenquadramento(self, dados: str, etapas_rx: dict) -> str:
        """Processa desenquadramento"""
        desenquadradores = {
            "contagem": (desenquadrar_contagem_caracteres, "contagem"),
            "bit-stuffing": (desenquadrar_bit_stuffing, "bit-stuffing"),
            "byte-stuffing": (desenquadrar_byte_stuffing, "byte-stuffing")
        }
        
        if self.enquadramento in desenquadradores:
            desenquad_func, debug_msg = desenquadradores[self.enquadramento]
            print(debug_msg)
            dados_desenquadrados = desenquad_func(dados)
            etapas_rx["desenquadrado"] = dados_desenquadrados
            print(f"[DEBUG] Após desenquadramento {self.enquadramento}: {dados_desenquadrados}")
            return dados_desenquadrados
        
        return dados


def bits_para_bytes(bit_str: str) -> bytes:
    """Converte string de bits para bytes"""
    byte_list = [
        int(bit_str[i:i+8], 2)
        for i in range(0, len(bit_str), 8)
    ]
    return bytes(byte_list)


def receber_via_socket(enquadramento: str, correcao: str, deteccao: str, 
                      mod_digital: str, mod_portadora: str) -> None:
    """Recebe dados via socket e processa com o receptor"""
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
        
        print(f'Tamanho sinal recebido: {len(sinal_recebido)}')
        print(sinal_recebido)

        rx = Receptor(pacotao["enq"], pacotao["cor"], pacotao["det"], 
                     pacotao["mod_dig"], pacotao["mod_por"])
        mensagem_recebida = rx.processar(sinal_recebido)
        
        print(f'Tamanho mensagem recebida: {len(mensagem_recebida)}')
        print(mensagem_recebida)

        mensagem_bytes = bits_para_bytes(mensagem_recebida)
        print(mensagem_bytes)

        try:
            mensagem_decodificada = mensagem_bytes.decode('utf-8')
        except UnicodeDecodeError:
            print("[WARNING] Erro ao decodificar UTF-8, substituindo bytes inválidos.")
            mensagem_decodificada = mensagem_bytes.decode('utf-8', errors='replace')

        print(f"[Receptor] Recebido: {mensagem_decodificada}")

        resposta_bytes = pickle.dumps({
            "mensagem": mensagem_decodificada,
            "etapas_tx": pacotao.get("etapas_tx", {}),
            "etapas_rx": rx.etapas_rx
        })
        
        conn.sendall(resposta_bytes)
        conn.close()
    
    server.close()


# Alias para manter compatibilidade
receber_via_Socket = receber_via_socket