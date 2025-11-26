import threading
import time

from Simulador.receptor import receber_via_Socket     
from Simulador.transmissor import transmitir_via_Socket  

#codigo de teste em terminal

def main():
    ENQ = "contagem" #todos funcionando! 
    COR = "hamming"  #apenas hamming ok! 
    DET = "crc" #todos funcionando
    MOD_DIG = "NRZ"   # todos funcionando
    MOD_POR = "PSK" # todos funcionando
    NOISE = 0.0

    
    def iniciar_receptor():
        receber_via_Socket(ENQ, COR, DET, MOD_DIG, MOD_POR)

    t = threading.Thread(target=iniciar_receptor, daemon=True)
    t.start()

    # Tempo para o servidor subir
    time.sleep(1)

    mensagem = "Hello Mundo! Testando comunicação via socket👆."

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
