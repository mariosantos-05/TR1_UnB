from CamadaFisica.fisica_transmissor import (
    encode_NRZ,
    encode_bipolar,
    encode_manchester,
    encode_ASK,
    encode_FSK,
    encode_16QAM
)

from Simulador.transmissor import transmitir_via_Socket
from Simulador.receptor import receber_via_Socket   

from threading import Thread
from gi.repository import GLib

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import matplotlib
matplotlib.use('GTK3Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas

import numpy as np


def upsample_signal(signal, samples_per_bit=20):
    """Repete cada valor do sinal samples_per_bit vezes para suavizar a forma de onda"""
    return np.repeat(signal, samples_per_bit)


class NetworkGUI(Gtk.Window):
    def __init__(self):
        super().__init__(title="Network Simulator")
        self.set_default_size(900, 700)
        self.set_border_width(10)

        self.box_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add(self.box_main)

        # --- Controles organizados em grid para economizar espaço ---
        grid = Gtk.Grid(row_spacing=6, column_spacing=12)
        self.box_main.pack_start(grid, False, False, 0)

        # Entrada de texto
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Digite sua mensagem aqui")
        grid.attach(self.entry, 0, 0, 4, 1)  # ocupa 4 colunas na linha 0

        # Labels e combos
        labels = ["Enquadramento:", "Correção de Erros:", "Detecção de Erros:", 
                  "Modulação Digital (Banda Base):", "Modulação por Portadora:"]
        options = [
            ["contagem", "bit-stuffing", "byte-stuffing"],
            ["hamming", "nenhuma"],
            ["paridade", "crc", "nenhuma"],
            ["NRZ", "bipolar", "manchester", "16encode_16QAM"],
            ["ASK", "FSK", "nenhuma"]
        ]

        self.combos = []

        for i, (label_text, opts) in enumerate(zip(labels, options)):
            label = Gtk.Label(label=label_text, halign=Gtk.Align.START)
            combo = Gtk.ComboBoxText()
            for opt in opts:
                combo.append_text(opt)
            combo.set_active(0)

            # Organiza em duas colunas: label à esquerda, combo à direita
            grid.attach(label, 0, i + 1, 1, 1)
            grid.attach(combo, 1, i + 1, 1, 1)

            self.combos.append(combo)

        # Spin para ruído
        self.noise_adjustment = Gtk.Adjustment(0.0, 0.0, 1.0, 0.01, 0.1, 0.0)
        self.noise_spin = Gtk.SpinButton()
        self.noise_spin.set_adjustment(self.noise_adjustment)
        self.noise_spin.set_digits(2)
        self.noise_spin.set_value(0.0)

        label_noise = Gtk.Label(label="Taxa de Ruído (0.0 a 1.0):", halign=Gtk.Align.START)
        grid.attach(label_noise, 2, 1, 1, 1)
        grid.attach(self.noise_spin, 3, 1, 1, 1)

        # Botão para simular
        self.button = Gtk.Button(label="Simular Transmissão")
        self.button.connect("clicked", self.on_button_clicked)
        grid.attach(self.button, 2, 2, 2, 1)  # ocupa 2 colunas

        # Botão para alternar entre mensagem e gráfico
        self.toggle_button = Gtk.Button(label="Mostrar Mensagem")
        self.toggle_button.connect("clicked", self.on_toggle_view)
        grid.attach(self.toggle_button, 2, 3, 2, 1)

        # --- Área de mensagem (TextView em ScrolledWindow) ---
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textbuffer = self.textview.get_buffer()

        self.text_scrolled = Gtk.ScrolledWindow()
        self.text_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.text_scrolled.set_min_content_height(300)
        self.text_scrolled.set_max_content_height(400)
        self.text_scrolled.add(self.textview)

        # --- Área dos gráficos ---
        self.figure = Figure(figsize=(8, 4), dpi=100)  # figura mais compacta
        self.canvas = FigureCanvas(self.figure)

        self.graph_scrolled = Gtk.ScrolledWindow()
        self.graph_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.graph_scrolled.set_min_content_height(300)
        self.graph_scrolled.set_max_content_height(450)
        self.graph_scrolled.add(self.canvas)

        # Começa mostrando gráfico
        self.box_main.pack_start(self.graph_scrolled, True, True, 0)
        self.box_main.pack_start(self.text_scrolled, True, True, 0)
        self.text_scrolled.hide()

    def on_toggle_view(self, button):
        if self.graph_scrolled.get_visible():
            self.graph_scrolled.hide()
            self.text_scrolled.show()
            self.toggle_button.set_label("Mostrar Gráficos")
        else:
            self.text_scrolled.hide()
            self.graph_scrolled.show()
            self.toggle_button.set_label("Mostrar Mensagem")

    def exibir_resposta(self, texto):
        self.textbuffer.set_text(f"Mensagem recebida do servidor:\n{texto}")

    def exibir_erro(self, erro):
        self.textbuffer.set_text(f"Erro ao enviar/receber: {erro}")

    def on_button_clicked(self, widget):
        mensagem_original = self.entry.get_text()
        mensagem_bits = ''.join(f'{byte:08b}' for byte in mensagem_original.encode())

        enquadramento = self.combos[0].get_active_text()
        correcao = self.combos[1].get_active_text()
        deteccao = self.combos[2].get_active_text()
        mod_digital = self.combos[3].get_active_text()
        mod_portadora = self.combos[4].get_active_text()
        noise_level = self.noise_spin.get_value()

        samples_per_bit = 20  # quantidade de samples por bit para suavizar o gráfico

        # Gerar sinais para plotagem e fazer upsample para banda base digital
        if mod_digital == "NRZ":
            banda_base_raw = encode_NRZ(mensagem_bits)
            banda_base = upsample_signal(banda_base_raw, samples_per_bit)
        elif mod_digital == "bipolar":
            banda_base_raw = encode_bipolar(mensagem_bits)
            banda_base = upsample_signal(banda_base_raw, samples_per_bit)
        elif mod_digital == "manchester":
            banda_base_raw = encode_manchester(mensagem_bits)
            banda_base = upsample_signal(banda_base_raw, samples_per_bit)
        elif mod_digital == "16encode_16QAM":
            banda_base_raw, _ = encode_16QAM(mensagem_bits)
            # 16encode_16QAM geralmente é sinal complexo, então vamos upsample só o real para plotar (ou converta para módulo se quiser)
            banda_base = upsample_signal(np.real(banda_base_raw), samples_per_bit)
        else:
            banda_base = []

        # Codificação por portadora
        if mod_portadora == "ASK":
            if isinstance(banda_base, np.ndarray):
                portadora = encode_ASK(banda_base.tolist())
            else:
                portadora = encode_ASK(banda_base)
        elif mod_portadora == "FSK":
            if isinstance(banda_base, np.ndarray):
                portadora = encode_FSK(banda_base.tolist())
            else:
                portadora = encode_FSK(banda_base)
        else:
            portadora = None

        self.figure.clf()
        ax1 = self.figure.add_subplot(211)
        ax1.set_title(f"Modulação Digital - {mod_digital}")
        ax1.plot(banda_base, color='blue')
        ax1.set_ylabel("Amplitude")
        ax1.grid(True)

        if portadora is not None:
            ax2 = self.figure.add_subplot(212)
            ax2.set_title(f"Modulação por Portadora - {mod_portadora}")
            ax2.plot(portadora, color='red')
            ax2.set_ylabel("Amplitude")
            ax2.grid(True)

        self.canvas.draw()

        # Enviar via socket em thread
        def tarefa():
            try:
                resposta = transmitir_via_Socket(
                    mensagem_original,
                    enquadramento,
                    correcao,
                    deteccao,
                    mod_digital,
                    mod_portadora,
                    noise_level
                )

                mensagem = resposta["mensagem"]
                etapas_tx = resposta.get("etapas_tx", {})
                etapas_rx = resposta.get("etapas_rx", {})

                texto = f"Mensagem recebida: {mensagem}\n\n"
                texto += "--- Etapas no Transmissor ---\n"
                for nome, bits in etapas_tx.items():
                    texto += f"{nome}: {bits[:120]}...\n"

                texto += "\n--- Etapas no Receptor ---\n"
                for nome, bits in etapas_rx.items():
                    texto += f"{nome}: {bits[:120]}...\n"

                GLib.idle_add(self.exibir_resposta, texto)
            except Exception as e:
                GLib.idle_add(self.exibir_erro, str(e))

        Thread(target=tarefa, daemon=True).start()


if __name__ == "__main__":
    Thread(
        target=receber_via_Socket,
        args=("contagem", "hamming", "paridade", "NRZ", "ASK"),
        daemon=True
    ).start()

    win = NetworkGUI()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
