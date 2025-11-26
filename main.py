import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk

from threading import Thread
import numpy as np
import random
import pickle
import socket
import time

import matplotlib
matplotlib.use('GTK4Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk4agg import FigureCanvasGTK4Agg as FigureCanvas

from Simulador.receptor import Receptor
from Simulador.transmissor import Transmissor

from CamadaFisica.fisica_transmissor import (
    encode_NRZ, encode_bipolar, encode_manchester,
    encode_ASK, encode_FSK, encode_16QAM
)
from CamadaFisica.fisica_receptor import (
    decode_NRZ, decode_bipolar, decode_manchester,
    decode_ASK, decode_FSK, decode_16QAM
)
from CamadaEnlace.enlace_transmissor import (
    transmissor_hamming, adicionar_paridade_par, crc32,
    enquadrar_contagem_caracteres, enquadrar_bit_stuffing, enquadrar_byte_stuffing
)
from CamadaEnlace.enlace_receptor import (
    receptor_hamming, verificar_paridade_par, verificar_crc32,
    desenquadrar_contagem_caracteres, desenquadrar_bit_stuffing, desenquadrar_byte_stuffing,
    remover_bit_paridade, remover_crc_e_padding
)

# --- FUNÇÕES AUXILIARES ---
def bits_para_bytes(bit_str):
    return bytes(int(bit_str[i:i+8], 2) for i in range(0, len(bit_str), 8))

# --- TRANSMISSOR ---
class Transmissor:
    def __init__(self, enquadramento="contagem", correcao="hamming", deteccao="crc32",
                 mod_digital="NRZ", mod_portadora="ASK", noise_level=0.0):
        self.enquadramento = enquadramento
        self.correcao = correcao
        self.deteccao = deteccao
        self.mod_digital = mod_digital
        self.mod_portadora = mod_portadora
        self.noise_level = noise_level
        self.etapas = {}

    def aplicar_ruido(self, dados_bits: str) -> str:
        if self.noise_level <= 0.0:
            return dados_bits
        return ''.join(b if random.random() >= self.noise_level else ('1' if b=='0' else '0') for b in dados_bits)

    def processar(self, dados: str) -> list:
        etapas = {"original": dados}

        # --- Enquadramento ---
        if self.enquadramento=="contagem":
            dados = enquadrar_contagem_caracteres(dados)
        elif self.enquadramento=="bit-stuffing":
            dados = enquadrar_bit_stuffing(dados)
        elif self.enquadramento=="byte-stuffing":
            dados = enquadrar_byte_stuffing(dados)
        etapas["enquadrado"] = dados

        # --- Correção de Erros ---
        if self.correcao=="hamming":
            dados = transmissor_hamming(dados)
            etapas["hamming"] = dados

        # --- Detecção de Erros ---
        if self.deteccao=="paridade":
            dados = adicionar_paridade_par(dados)
            etapas["paridade"] = dados
        elif self.deteccao=="crc32":
            dados = crc32(dados)
            etapas["crc32"] = dados

        # --- Ruído ---
        dados = self.aplicar_ruido(dados)
        etapas["com_ruido"] = dados

        # --- Modulação ---
        if self.mod_digital=="NRZ":
            resultado = encode_NRZ(dados)
        elif self.mod_digital=="bipolar":
            resultado = encode_bipolar(dados)
        elif self.mod_digital=="manchester":
            resultado = encode_manchester(dados)
        elif self.mod_digital=="16QAM":
            resultado = encode_16QAM(dados)

        if self.mod_digital!="16QAM":
            if self.mod_portadora=="ASK":
                resultado = encode_ASK(resultado)
            elif self.mod_portadora=="FSK":
                resultado = encode_FSK(resultado)

        self.etapas = etapas
        return resultado

# --- RECEPTOR ---
class Receptor:
    def __init__(self, enquadramento="contagem", correcao="hamming", deteccao="crc", mod_digital="NRZ", mod_portadora="ASK"):
        self.enquadramento = enquadramento
        self.correcao = correcao
        self.deteccao = deteccao
        self.mod_digital = mod_digital
        self.mod_portadora = mod_portadora
        self.etapas_rx = {}

    def processar(self, dados: list) -> str:
        etapas_rx = {"recebido": dados.copy()}

        # --- Demodulação Portadora ---
        if self.mod_digital != "16QAM":
            if self.mod_portadora=="ASK":
                dados = decode_ASK(dados)
            elif self.mod_portadora=="FSK":
                dados = decode_FSK(dados, )

        # --- Demodulação Digital ---
        if self.mod_digital=="NRZ":
            dados = decode_NRZ(dados)
        elif self.mod_digital=="bipolar":
            dados = decode_bipolar(dados)
        elif self.mod_digital=="manchester":
            dados = decode_manchester(dados)
        elif self.mod_digital=="16QAM":
            dados = decode_16QAM(dados)
        etapas_rx["demodulado"] = dados

        dados = ''.join(map(str,dados))
        etapas_rx["bits_puros"] = dados

        # --- Detecção e correção ---
        if self.deteccao=="paridade":
            if not verificar_paridade_par(dados):
                pass
            etapas_rx["removido_paridade"] = dados
            dados = remover_bit_paridade(dados)
        elif self.deteccao=="crc":
            if not verificar_crc32(dados):
                dados = remover_crc_e_padding(dados)
            else:
                dados = remover_crc_e_padding(dados)
                etapas_rx["removido_crc"] = dados

        if self.correcao=="hamming":
            dados = receptor_hamming(dados)
            etapas_rx["corrigido_hamming"] = dados

        # --- Desenquadramento ---
        if self.enquadramento=="contagem":
            dados = desenquadrar_contagem_caracteres(dados)
        elif self.enquadramento=="bit-stuffing":
            dados = desenquadrar_bit_stuffing(dados)
        elif self.enquadramento=="byte-stuffing":
            dados = desenquadrar_byte_stuffing(dados)
        etapas_rx["desenquadrado"] = dados

        self.etapas_rx = etapas_rx
        return dados

# --- SOCKET SIMULADO (dentro da mesma aplicação) ---
def transmitir_e_receber_local(mensagem, enquadramento, correcao, deteccao, mod_digital, mod_portadora, noise_level):
    # Transmissor
    tx = Transmissor(enquadramento, correcao, deteccao, mod_digital, mod_portadora, noise_level)
    mensagem_bits = ''.join(f'{b:08b}' for b in mensagem.encode())
    sinal_tx = tx.processar(mensagem_bits)

    # Receptor
    rx = Receptor(enquadramento, correcao, deteccao, mod_digital, mod_portadora)
    mensagem_rx = rx.processar(sinal_tx)
    mensagem_rx_bytes = bits_para_bytes(mensagem_rx)
    try:
        mensagem_rx_str = mensagem_rx_bytes.decode('utf-8')
    except:
        mensagem_rx_str = mensagem_rx_bytes.decode('utf-8', errors='replace')

    return {
        "mensagem": mensagem_rx_str,
        "etapas_tx": tx.etapas,
        "etapas_rx": rx.etapas_rx,
        "sinal_tx": sinal_tx
    }

# --- GTK4 GUI ---
class NetworkApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.example.NetworkSim")
    def do_activate(self):
        win = NetworkGUI(self)
        win.present()

class NetworkGUI(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Network Simulator")
        self.set_default_size(1000, 720)

        css = b"""
        window { background: #141820; color: #e0e6ed; }
        box.main { padding: 16px; }
        frame { background: #1d232f; border-radius: 10px; border: 1px solid #2b3240; margin-bottom: 12px; padding: 10px; }
        button { background: #2d8bff; color: white; border-radius: 8px; padding: 8px 14px; font-weight: bold; }
        button:hover { background: #1c6ed6; }
        entry { background: #222836; color: white; border-radius: 6px; padding: 6px; border: 1px solid #333c4f; }
        label { color: #e0e6ed; }
        label.title { font-size: 18px; font-weight: bold; color: #46a0ff; margin-bottom: 6px; }
        spinbutton { background: #222836; color: white; }
        textview { background: #1b202b; color: #b5c0d0; border-radius: 8px; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, css_name="main")
        self.set_child(main_box)

        # CONTROLS
        frame_controls = Gtk.Frame()
        main_box.append(frame_controls)
        box_controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        frame_controls.set_child(box_controls)
        label_title = Gtk.Label(label="Configurações de Simulação")
        label_title.add_css_class("title")
        box_controls.append(label_title)
        self.entry = Gtk.Entry(placeholder_text="Digite sua mensagem aqui")
        box_controls.append(self.entry)

        # GRID
        grid = Gtk.Grid(column_spacing=12, row_spacing=8, margin_top=8)
        box_controls.append(grid)
        labels = [
            "Enquadramento:", "Correção de Erros:", "Detecção de Erros:",
            "Modulação Digital:", "Modulação por Portadora:"
        ]
        options = [
            ["contagem", "bit-stuffing", "byte-stuffing"],
            ["hamming", "nenhuma"],
            ["paridade", "crc", "nenhuma"],
            ["NRZ", "bipolar", "manchester", "16QAM"],
            ["ASK", "FSK", "nenhuma"]
        ]
        self.dropdowns = []
        for i, (text, opts) in enumerate(zip(labels, options)):
            lbl = Gtk.Label(label=text, halign=Gtk.Align.END)
            dd = Gtk.DropDown.new_from_strings(opts)
            dd.set_selected(0)
            grid.attach(lbl, 0, i, 1, 1)
            grid.attach(dd, 1, i, 1, 1)
            self.dropdowns.append(dd)

        # Noise
        lbl_noise = Gtk.Label(label="Taxa de Ruído (0.0 a 1.0):", halign=Gtk.Align.END)
        adj = Gtk.Adjustment(value=0.0, lower=0.0, upper=1.0, step_increment=0.01)
        self.noise_spin = Gtk.SpinButton(adjustment=adj, digits=2)
        grid.attach(lbl_noise, 2, 0, 1, 1)
        grid.attach(self.noise_spin, 3, 0, 1, 1)

        # BUTTONS
        box_buttons = Gtk.Box(spacing=10, halign=Gtk.Align.END, margin_top=10)
        box_controls.append(box_buttons)
        self.button_simular = Gtk.Button(label="Simular Transmissão")
        self.button_simular.connect("clicked", self.on_button_clicked)
        box_buttons.append(self.button_simular)
        self.button_toggle = Gtk.Button(label="Mostrar Mensagem")
        self.button_toggle.connect("clicked", self.on_toggle_view)
        box_buttons.append(self.button_toggle)

        # VIEW
        frame_view = Gtk.Frame()
        main_box.append(frame_view)
        box_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        frame_view.set_child(box_view)
        label_results = Gtk.Label(label="Resultados da Simulação")
        label_results.add_css_class("title")
        box_view.append(label_results)
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        box_view.append(self.canvas)
        self.textview = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.textbuffer = self.textview.get_buffer()
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.textview)
        scrolled.set_min_content_height(250)
        box_view.append(scrolled)
        scrolled.hide()
        self.text_scrolled = scrolled
        self.graph_widget = self.canvas

    def on_toggle_view(self, button):
        if self.graph_widget.get_visible():
            self.graph_widget.hide()
            self.text_scrolled.show()
            self.button_toggle.set_label("Mostrar Gráficos")
        else:
            self.text_scrolled.hide()
            self.graph_widget.show()
            self.button_toggle.set_label("Mostrar Mensagem")

    def exibir_resposta(self, texto):
        self.textbuffer.set_text(texto)

    def on_button_clicked(self, button):
        msg = self.entry.get_text()
        enquadramento = self.dropdowns[0].get_selected_item().get_string()
        correcao = self.dropdowns[1].get_selected_item().get_string()
        deteccao = self.dropdowns[2].get_selected_item().get_string()
        mod_digital = self.dropdowns[3].get_selected_item().get_string()
        mod_portadora = self.dropdowns[4].get_selected_item().get_string()
        noise_level = self.noise_spin.get_value()

        def tarefa():
            resposta = transmitir_e_receber_local(
                msg, enquadramento, correcao, deteccao, mod_digital, mod_portadora, noise_level
            )

            texto = f"""
Mensagem original: "{msg}"
Mensagem recebida: "{resposta['mensagem']}"

--- Etapas TX ---
{resposta.get('etapas_tx', {})}

--- Etapas RX ---
{resposta.get('etapas_rx', {})}
"""
            GLib.idle_add(self.exibir_resposta, texto.strip())

            # --- Gráfico com Múltiplas Visualizações ---
            sinal_tx = resposta['sinal_tx']
            t = np.linspace(0, len(sinal_tx) / 1000, len(sinal_tx))
            
            self.figure.clf()
            self.figure.patch.set_facecolor('#1d232f')
            
            # Criar subplots
            ax1 = self.figure.add_subplot(211)  # Sinal completo
            ax2 = self.figure.add_subplot(212)  # Zoom nas primeiras amostras
            
            # Configurar fundo dos subplots
            for ax in [ax1, ax2]:
                ax.set_facecolor('#1d232f')
                ax.tick_params(colors='lightgray')
                for spine in ax.spines.values():
                    spine.set_color('lightgray')
                ax.grid(True, linestyle='--', alpha=0.3, color='lightgray')
            
            # Plot 1: Sinal completo
            ax1.plot(t, sinal_tx, color='#2d8bff', linewidth=1, alpha=0.8)
            ax1.set_title(f"Sinal Transmitido Completo - {mod_digital} + {mod_portadora}", 
                         color='white', fontsize=12, pad=10)
            ax1.set_ylabel('Amplitude', color='lightgray')
            
            # Plot 2: Zoom nas primeiras amostras
            zoom_samples = min(200, len(sinal_tx))  # Mostrar até 200 amostras
            if zoom_samples > 0:
                ax2.plot(t[:zoom_samples], sinal_tx[:zoom_samples], color='#ff6b6b', linewidth=1.5)
                ax2.set_title("Zoom: Primeiras Amostras", color='white', fontsize=12, pad=10)
                ax2.set_xlabel('Tempo (s)', color='lightgray')
                ax2.set_ylabel('Amplitude', color='lightgray')
            
            self.figure.tight_layout()
            GLib.idle_add(self.canvas.draw)

        Thread(target=tarefa, daemon=True).start()

if __name__ == "__main__":
    app = NetworkApp()
    app.run()
