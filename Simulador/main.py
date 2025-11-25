import sys
from Simulador.transmissor import transmitir_via_socket

from Simulador.receptor import receber_via_socket

def modo_transmissor(texto):
    print("[TX] Iniciando transmissão...")
    resposta = transmitir_via_socket(texto)
    print("[TX] Resposta do receptor:", resposta)


def modo_receptor():
    print("[RX] Aguardando transmissão...")
    receber_via_socket()


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python3 -m Simulador.main transmissor \"mensagem\"")
        print("  python3 -m Simulador.main receptor")
        sys.exit(1)

    modo = sys.argv[1].lower()

    if modo == "transmissor":
        if len(sys.argv) < 3:
            print("Erro: falta a mensagem para transmissão.")
            sys.exit(1)
        texto = sys.argv[2]
        modo_transmissor(texto)

    elif modo == "receptor":
        modo_receptor()

    else:
        print("Modo inválido. Use: transmissor | receptor")
        sys.exit(1)


if __name__ == "__main__":
    main()
