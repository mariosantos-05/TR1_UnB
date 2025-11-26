import threading
import time

from Simulador.receptor import receber_via_Socket     
from Simulador.transmissor import transmitir_via_Socket  


def main():
    ENQ = "contagem"
    COR = "hamming"
    DET = "crc"
    MOD_DIG = "NRZ"
    MOD_POR = "ASK"
    NOISE = 0.0

    
    def iniciar_receptor():
        receber_via_Socket(ENQ, COR, DET, MOD_DIG, MOD_POR)

    t = threading.Thread(target=iniciar_receptor, daemon=True)
    t.start()

    # Tempo para o servidor subir
    time.sleep(1)

    # Mensagem a enviar
    mensagem = "Hello Mundo! Testando comunicação 😎"

    print("\n=== TRANSMISSOR ENVIANDO ===\n")
    resposta = transmitir_via_Socket(
        mensagem,
        ENQ, COR, DET, MOD_DIG, MOD_POR,
        noise_level=NOISE,
    )

    print("\n=== RESPOSTA RECEBIDA DO SERVIDOR ===")
    print(resposta["mensagem"])


if __name__ == "__main__":
    main()
