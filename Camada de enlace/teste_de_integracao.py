# -*- coding: utf-8 -*-
"""
Testes de Integração para as Camadas de Enlace (Transmissor <-> Receptor).
Verifica a recuperação da mensagem original em diferentes cenários de protocolo.
"""
import unittest
import enlace_transmissor as tx
import enlace_receptor as rx

# -------------------------------------------------------------------
# FUNÇÕES AUXILIARES DE TESTE
# -------------------------------------------------------------------

def get_dados_basicos(texto: str = "Trabalho") -> str:
    """Converte texto para string de bits (8 bits por caractere)."""
    return ''.join(f'{byte:08b}' for byte in texto.encode('utf-8'))

class TestIntegracaoCamadaEnlace(unittest.TestCase):

    def setUp(self):
        """Configura os dados de entrada comuns."""
        self.DADOS_ORIGINAIS = get_dados_basicos("Info") # 4 caracteres = 32 bits
        self.DADOS_HAMMING = "1101001" # 7 bits

    # -------------------------------------------------------------------
    # Cenário 1: Contagem + Paridade Par (Sem Erro)
    # -------------------------------------------------------------------

    def test_integracao_contagem_paridade_sem_erro(self):
        print("\n=======================================================")
        print("CENÁRIO 1: Contagem + Paridade (Sem Erro)")
        print("=======================================================")
        
        dados_entrada = self.DADOS_ORIGINAIS
        
        # --- LADO TX ---
        print("\n--- PASSO TX 1: Detecção de Erro (Paridade) ---")
        bits_com_controle = tx.adicionar_paridade_par(dados_entrada)
        print(f"TX Saída Paridade: {bits_com_controle}")
        
        print("\n--- PASSO TX 2: Enquadramento (Contagem) ---")
        quadro_transmitido = tx.enquadrar_contagem_caracteres(bits_com_controle)
        print(f"TX Saída Enquadr.: {quadro_transmitido}")
        
        # Simulação: Quadro Recebido sem alteração
        quadro_recebido = quadro_transmitido

        # --- LADO RX ---
        print("\n--- PASSO RX 1: Desenquadramento (Contagem) ---")
        dados_pos_desenq = rx.desenquadrar_contagem_caracteres(quadro_recebido)
        print(f"RX Saída Desenq.: {dados_pos_desenq}")
        
        print("\n--- PASSO RX 2: Verificação de Erro (Paridade) ---")
        valido, dados_finais = rx.verificar_paridade_par(dados_pos_desenq)
        print(f"RX Saída Paridade: Válido={valido}, Dados={dados_finais}")

        # --- ASSERT FINAIS ---
        self.assertTrue(valido, "A verificação de paridade falhou.")
        self.assertEqual(dados_finais, dados_entrada, "Os dados recuperados não correspondem ao original.")

    # -------------------------------------------------------------------
    # Cenário 2: Bit Stuffing + Hamming (Com Correção de Erro)
    # -------------------------------------------------------------------

    def test_integracao_bitstuffing_hamming_com_erro(self):
        print("\n=======================================================")
        print("CENÁRIO 2: Bit Stuffing + Hamming (Com Correção de Erro)")
        print("=======================================================")

        dados_entrada = self.DADOS_HAMMING # "1101001"
        
        # --- LADO TX ---
        print("\n--- PASSO TX 1: Correção de Erro (Hamming) ---")
        bits_com_controle = tx.transmissor_hamming(dados_entrada)
        print(f"TX Saída Hamming: {bits_com_controle}") 
        
        print("\n--- PASSO TX 2: Enquadramento (Bit Stuffing) ---")
        quadro_transmitido = tx.enquadrar_bit_stuffing(bits_com_controle)
        print(f"TX Saída Enquadr.: {quadro_transmitido}")
        
        # Simulação: Introdução de ERRO na Posição 6 (índice 5 no Hamming)
        conteudo_hamming = quadro_transmitido[len(tx.FLAG_BITS):-len(tx.FLAG_BITS)]
        
        if len(conteudo_hamming) > 5:
            conteudo_corrompido = conteudo_hamming[:5] + ('0' if conteudo_hamming[5] == '1' else '1') + conteudo_hamming[6:]
        else:
             conteudo_corrompido = conteudo_hamming 
        
        quadro_recebido = tx.FLAG_BITS + conteudo_corrompido + tx.FLAG_BITS
        print(f"\nMEIO DE COMUNICAÇÃO: Erro injetado na pos 6 do payload.")

        # --- LADO RX ---
        print("\n--- PASSO RX 1: Desenquadramento (Bit Stuffing) ---")
        dados_pos_desenq = rx.desenquadrar_bit_stuffing(quadro_recebido)
        print(f"RX Saída Desenq.: {dados_pos_desenq}")
        
        print("\n--- PASSO RX 2: Correção de Erro (Hamming) ---")
        dados_finais, pos_erro = rx.receptor_hamming(dados_pos_desenq)
        print(f"RX Saída Hamming: Pos. Erro={pos_erro}, Dados={dados_finais}")
        
        # --- ASSERT FINAIS ---
        self.assertEqual(pos_erro, 6, "O Hamming falhou em detectar o erro na posição 6.")
        self.assertEqual(dados_finais, dados_entrada, "Os dados recuperados não correspondem ao original após correção.")

    # -------------------------------------------------------------------
    # Cenário 3: Byte Stuffing + CRC32 (Lógica Yantavares)
    # -------------------------------------------------------------------
    
    def test_integracao_bytestuffing_crc_com_padding(self):
        print("\n=======================================================")
        print("CENÁRIO 3: Byte Stuffing + CRC32 (Com Padding)")
        print("=======================================================")

        dados_entrada = get_dados_basicos("A") # 8 bits
        
        # --- LADO TX ---
        print("\n--- PASSO TX 1: Detecção de Erro (CRC32 com Padding) ---")
        bits_com_crc_e_pad, pad_len = tx.crc32(dados_entrada)
        print(f"TX Saída CRC+Pad: Len={len(bits_com_crc_e_pad)}, PadLen={pad_len}")
        
        header_padding = format(pad_len, '08b')
        payload_para_enquadrar = header_padding + bits_com_crc_e_pad
        print(f"Payload com Header: {payload_para_enquadrar[:20]}...")

        print("\n--- PASSO TX 2: Enquadramento (Byte Stuffing) ---")
        quadro_transmitido = tx.enquadrar_byte_stuffing(payload_para_enquadrar)
        print(f"TX Saída Enquadr.: {quadro_transmitido[:20]}...")

        # Simulação: Quadro Recebido sem alteração
        quadro_recebido = quadro_transmitido

        # --- LADO RX ---
        print("\n--- PASSO RX 1: Desenquadramento (Byte Stuffing) ---")
        dados_pos_desenq = rx.desenquadrar_byte_stuffing(quadro_recebido)
        print(f"RX Saída Desenq.: {dados_pos_desenq[:20]}...")

        pad_len_recebido = int(dados_pos_desenq[:8], 2)
        payload_crc_recebido = dados_pos_desenq[8:]
        print(f"RX Payload: Tamanho Padding Lido={pad_len_recebido}")
        
        print("\n--- PASSO RX 2: Verificação e Limpeza (CRC32) ---")
        valido = rx.verificar_crc32(payload_crc_recebido)

        dados_sem_controle = rx.remover_crc_e_padding(payload_crc_recebido, pad_len_recebido)
        print(f"RX Saída Limpeza: Válido={valido}, Dados={dados_sem_controle}")

        # --- ASSERT FINAIS ---
        self.assertTrue(valido, "A verificação do CRC falhou. Integridade do quadro perdida.")
        self.assertEqual(dados_sem_controle, dados_entrada, "Os dados recuperados não correspondem ao original.")

    # -------------------------------------------------------------------
    # Cenário 4: Contagem + Checksum (Sem Erro) - Originalmente 4
    # -------------------------------------------------------------------

    def test_integracao_contagem_checksum_sem_erro(self):
        print("\n=======================================================")
        print("CENÁRIO 4: Contagem + Checksum (Sem Erro)")
        print("=======================================================")
        
        dados_entrada = self.DADOS_ORIGINAIS
        
        # --- LADO TX ---
        print("\n--- PASSO TX 1: Detecção de Erro (Checksum) ---")
        bits_com_controle = tx.adicionar_checksum(dados_entrada)
        print(f"TX Saída Checksum: {bits_com_controle}")
        
        print("\n--- PASSO TX 2: Enquadramento (Contagem) ---")
        quadro_transmitido = tx.enquadrar_contagem_caracteres(bits_com_controle)
        print(f"TX Saída Enquadr.: {quadro_transmitido}")
        
        # Simulação: Quadro Recebido sem alteração
        quadro_recebido = quadro_transmitido

        # --- LADO RX ---
        print("\n--- PASSO RX 1: Desenquadramento (Contagem) ---")
        dados_pos_desenq = rx.desenquadrar_contagem_caracteres(quadro_recebido)
        print(f"RX Saída Desenq.: {dados_pos_desenq}")
        
        print("\n--- PASSO RX 2: Verificação e Limpeza (Checksum) ---")
        valido, dados_com_padding = rx.verificar_checksum(dados_pos_desenq)
        print(f"RX Saída Checksum: Válido={valido}, Dados c/ Pad={dados_com_padding}")
        
        # Remoção do Padding de Alinhamento (Dados originais têm 32 bits)
        dados_finais = dados_com_padding[-32:]
        
        # --- ASSERT FINAIS ---
        self.assertTrue(valido, "A verificação de Checksum falhou.")
        self.assertEqual(dados_finais, dados_entrada, "Os dados recuperados não correspondem ao original.")
        
    # -------------------------------------------------------------------
    # Cenário 5: Bit Stuffing + Checksum (Com Erro) - NOVO TESTE
    # -------------------------------------------------------------------

    def test_integracao_bitstuffing_checksum_com_erro(self):
        print("\n=======================================================")
        print("CENÁRIO 5: Bit Stuffing + Checksum (Com Erro)")
        print("=======================================================")
        
        dados_entrada = self.DADOS_ORIGINAIS # 32 bits
        
        # --- LADO TX ---
        print("\n--- PASSO TX 1: Detecção de Erro (Checksum) ---")
        bits_com_controle = tx.adicionar_checksum(dados_entrada) # 40 bits (32 dados + 8 checksum)
        print(f"TX Saída Checksum: {bits_com_controle[:40]}...")
        
        print("\n--- PASSO TX 2: Enquadramento (Bit Stuffing) ---")
        quadro_transmitido = tx.enquadrar_bit_stuffing(bits_com_controle)
        print(f"TX Saída Enquadr.: {quadro_transmitido[:40]}...")
        
        # Simulação: Introdução de ERRO no PAYLOAD (inverte o 5º bit de dados - índice 40)
        flags_len = len(tx.FLAG_BITS)
        payload_inicial = quadro_transmitido[flags_len:-flags_len]
        
        # Injetar erro no 5º bit do payload (índice 4 no payload)
        if len(payload_inicial) > 4:
            payload_corrompido = payload_inicial[:4] + ('0' if payload_inicial[4] == '1' else '1') + payload_inicial[5:]
        else:
             payload_corrompido = payload_inicial 
        
        # Re-monta o quadro com o erro
        quadro_recebido = tx.FLAG_BITS + payload_corrompido + tx.FLAG_BITS
        print(f"\nMEIO DE COMUNICAÇÃO: Erro injetado no 5º bit do payload.")

        # --- LADO RX ---
        print("\n--- PASSO RX 1: Desenquadramento (Bit Stuffing) ---")
        dados_pos_desenq = rx.desenquadrar_bit_stuffing(quadro_recebido)
        print(f"RX Saída Desenq.: {dados_pos_desenq[:40]}...")
        
        print("\n--- PASSO RX 2: Verificação e Limpeza (Checksum) ---")
        # Deve falhar na verificação devido ao erro injetado
        valido, dados_com_padding = rx.verificar_checksum(dados_pos_desenq)
        print(f"RX Saída Checksum: Válido={valido}, Dados c/ Pad={dados_com_padding[-32:]}")
        
        # O dado original tem 32 bits.
        dados_finais = dados_com_padding[-32:]
        
        # --- ASSERT FINAIS ---
        self.assertFalse(valido, "O Checksum falhou em detectar o erro.")
        self.assertNotEqual(dados_finais, dados_entrada, "Os dados recuperados não deveriam ser iguais ao original (após erro).")


if __name__ == '__main__':
    unittest.main()