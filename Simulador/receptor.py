from typing import List

from CamadaFisica.modulacao_demodulacao_digital import (
    decode_NRZ, decode_bipolar, decode_manchester,
    decode_ASK, decode_FSK, decode_8QAM
)
from CamadaEnlace.enlace_receptor import (
    receptor_hamming, verificar_paridade_par, verificar_crc32,
    desenquadrar_contagem_caracteres, desenquadrar_bit_stuffing, desenquadrar_byte_stuffing,
    remover_bit_paridade, remover_crc_e_padding, 
)

import socket
import pickle

class Receptor:
    def __init__(self, enquadramento="contagem", correcao="hamming", deteccao="crc", mod_digital="NRZ", mod_portadora="ASK"):
        self.enquadramento = enquadramento
        self.correcao = correcao
        self.deteccao = deteccao
        self.mod_digital = mod_digital
        self.mod_portadora = mod_portadora

    def processar(self, dados: List[int]) -> str:
        print("\n[DEBUG] --- Início do processamento no receptor ---")

        etapas_rx = {"recebido": dados}
        
        if self.mod_digital != "8QAM":
            # entra lista de floats...
            if self.mod_portadora == "ASK":
                dados = decode_ASK(dados)
                print("recebdno ASK")
            elif self.mod_portadora == "FSK":
                dados = decode_FSK(dados)
                print("recebendo FSK")
            # sai lista de floats...
            print(f"[DEBUG] Após demodulação portadora {self.mod_portadora}: {dados}")
        # 1. Demodulação
        # entra lista de floats...
        if self.mod_digital == "NRZ":
            dados = decode_NRZ(dados)
            print("recebendo NRZ")
        elif self.mod_digital == "bipolar":
            dados = decode_bipolar(dados)
            print("recebendo bipolar")
        elif self.mod_digital == "manchester":
            dados = decode_manchester(dados)
            print("recebendo manchester")
        elif self.mod_digital == "8QAM":
            dados = decode_8QAM(dados)
            print("recebendo 8QAM")
        etapas_rx["demodulado"] = dados
        # sai string de bits...

        print(f"[DEBUG] Após demodulação digital ou 8QAM -> {self.mod_digital}: {dados}")

        # Transforma lista de bits em string
        dados = ''.join(map(str, dados))
        etapas_rx["bits_puros"] = dados
        print("[DEBUG] Em string de bits:", dados)
# ---> Até aqui Deus nos ajudou, depois ta dando erro no hamming

        # 2. Detecção e correção de erros
        if self.deteccao == "paridade":
            if not verificar_paridade_par(dados):
                print("[DEBUG] Erro de paridade detectado.")
            etapas_rx["removido_paridade"] = dados
            dados = remover_bit_paridade(dados)

        elif self.deteccao == "crc":
            if not verificar_crc32(dados):
                print("[DEBUG] Erro de CRC detectado. Aplicando Hamming.")
                dados = remover_crc_e_padding(dados)
                print("[DEBUG] Tamanho depois de remover CRC:", len(dados))

            else:
                print("[DEBUG] CRC verificado com sucesso.")
                dados = remover_crc_e_padding(dados)
                etapas_rx["removido_crc"] = dados
                print("[DEBUG] Tamanho depois de remover CRC:", len(dados))

        if self.correcao == "hamming":
            dados = receptor_hamming(dados)
            etapas_rx["corrigido_hamming"] = dados
            print("[DEBUG] Tamanho depois de remover Hamming:", len(dados))
            #remover_bits_hamming(dados)



        print("[DEBUG] Após correção e remoção de bits extras:", dados)

        # 3. Desenquadramento
        if self.enquadramento == "contagem":
            dados = desenquadrar_contagem_caracteres(dados)
            print("contagem")
        elif self.enquadramento == "bit-stuffing":
            dados = desenquadrar_bit_stuffing(dados)
            print("bit-stuffing")
        elif self.enquadramento == "byte-stuffing":
            dados = desenquadrar_byte_stuffing(dados)
            print("byte-stuffing")

        etapas_rx["desenquadrado"] = dados

        print(f"[DEBUG] Após desenquadramento {self.enquadramento}: {dados}")
        print("[DEBUG] --- Fim do processamento no receptor ---\n")

        self.etapas_rx = etapas_rx  # armazena as etapas para uso posterior

        return dados

def bits_para_bytes(bit_str):
    #assert len(bit_str) % 8 == 0
    byte_list = [
        int(bit_str[i:i+8], 2)
        for i in range(0, len(bit_str), 8)
    ]
    return bytes(byte_list)

def receber_via_Socket(enquadramento: str, correcao: str, deteccao: str, mod_digital: str, mod_portadora: str):
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

        rx = Receptor(pacotao["enq"], pacotao["cor"], pacotao["det"], pacotao["mod_dig"], pacotao["mod_por"])
        mensagem_recebida = rx.processar(sinal_recebido)
        print(f'Tamanho mensagem recebida: {len(mensagem_recebida)}')
        print(mensagem_recebida)

        mensagem_recebida = bits_para_bytes(mensagem_recebida)
        print(mensagem_recebida)

        try:
            mensagem_recebida = mensagem_recebida.decode('utf-8')
        except UnicodeDecodeError:
            print("[WARNING] Erro ao decodificar UTF-8, substituindo bytes inválidos.")
            mensagem_recebida = mensagem_recebida.decode('utf-8', errors='replace')

        print(f"[Receptor] Recebido: {mensagem_recebida}")

        resposta_bytes = pickle.dumps({
            "mensagem": mensagem_recebida,
            "etapas_tx": pacotao.get("etapas_tx", {}),
            "etapas_rx": rx.etapas_rx
        })
        conn.sendall(resposta_bytes)
        conn.close()
        
    server.close()

