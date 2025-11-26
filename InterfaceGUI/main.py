import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

def apply_dark_css():
    css = b"""
    /* === GENERAL WINDOW === */
    window {
        background: #141820;
        color: #e0e6ed;
    }

    box, grid {
        background: transparent;
    }

    entry, 
    spinbutton,
    comboboxtext {
        background: #222836;
        color: white;
        border-radius: 6px;
        padding: 6px;
        border: 1px solid #333c4f;
    }

    label {
        color: #e0e6ed;
        font-size: 13px;
    }

    /* Titles */
    label.title {
        color: #46a0ff;
        font-size: 17px;
        font-weight: bold;
        margin-bottom: 6px;
    }

    /* Frames */
    frame {
        background: #1d232f;
        border-radius: 10px;
        border: 1px solid #2b3240;
        padding: 10px;
        margin-bottom: 12px;
    }

    /* Buttons */
    button {
        background: #2d8bff;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        padding: 8px 14px;
        border: none;
    }

    button:hover {
        background: #1c6ed6;
    }

    /* TextView */
    textview text {
        background: #1b202b;
        color: #b5c0d0;
    }

    textview {
        background: #1b202b;
        border-radius: 8px;
        padding: 8px;
        border: 1px solid #2b3240;
    }

    scrolledwindow {
        background: #1b202b;
        border-radius: 8px;
        border: 1px solid #2b3240;
    }
    """

    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

from CamadaFisica.fisica_transmissor import (
    NRZ_polar_modulation,
    bipolar_modulation,
    manchester_modulation,
    ASK_modulation,
    FSK_modulation,
    PSK_modulation,
    QPSK_modulation,
    QAM16_modulation
)

from Simulador.transmissor import transmitir_via_Socket
from Simulador.receptor import receber_via_Socket   

from threading import Thread

import matplotlib
matplotlib.use('GTK3Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas

import numpy as np


def upsample_signal(signal, samples_per_bit=20):
    return np.repeat(signal, samples_per_bit)

class NetworkGUI(Gtk.Window):
    def __init__(self):
        super().__init__(title="Network Simulator")
        self.set_title("Network Simulator")
        self.set_default_size(1000, 720)

        apply_dark_css()

        self.box_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(self.box_main)

        # --- TITLE ---
        title = Gtk.Label(label="Configurações de Simulação")
        title.get_style_context().add_class("title")
        title.set_halign(Gtk.Align.START)
        self.box_main.pack_start(title, False, False, 6)

        # --- MAIN GRID ---
        grid = Gtk.Grid(row_spacing=10, column_spacing=12, column_homogeneous=False)
        self.box_main.pack_start(grid, False, False, 0)

        # ENTRY 
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Digite sua mensagem aqui")
        self.entry.set_hexpand(True)
        self.entry.set_halign(Gtk.Align.FILL)
        grid.attach(self.entry, 0, 0, 4, 1)

        labels = [
            "Enquadramento:", "Correção de Erros:", "Detecção de Erros:", 
            "Modulação Digital (Banda Base):", "Modulação por Portadora:"
        ]
        options = [
            ["contagem", "bit-stuffing", "byte-stuffing"],      
            ["hamming", "nenhuma"],                             
            ["paridade", "crc", "checksum", "nenhuma"],         
            ["NRZ", "bipolar", "manchester"], 
            ["ASK", "FSK", "PSK", "QPSK", "16QAM", "nenhuma"]           
        ]


        self.combos = []

        for i, (label_text, opts) in enumerate(zip(labels, options)):
            label = Gtk.Label(label=label_text, halign=Gtk.Align.START)
            combo = Gtk.ComboBoxText()
            for opt in opts:
                combo.append_text(opt)
            combo.set_active(0)
            combo.set_hexpand(True)
            combo.set_halign(Gtk.Align.FILL)

            grid.attach(label, 0, i + 1, 1, 1)
            grid.attach(combo, 1, i + 1, 3, 1)  
            self.combos.append(combo)

        # NOISE
        label_noise = Gtk.Label(label="Taxa de Ruído (0.0 a 1.0):", halign=Gtk.Align.START)
        self.noise_adjustment = Gtk.Adjustment(0.0, 0.0, 1.0, 0.01, 0.1, 0.0)
        self.noise_spin = Gtk.SpinButton()
        self.noise_spin.set_adjustment(self.noise_adjustment)
        self.noise_spin.set_digits(2)
        self.noise_spin.set_hexpand(False)

        grid.attach(label_noise, 0, 6, 1, 1)
        grid.attach(self.noise_spin, 1, 6, 1, 1)

        # BUTTONS - responsive box
        button_box = Gtk.Box(spacing=10)
        button_box.set_homogeneous(True)
        button_box.set_hexpand(True)

        self.button = Gtk.Button(label="Simular Transmissão")
        self.button.connect("clicked", self.on_button_clicked)
        self.button.set_hexpand(True)
        self.button.set_halign(Gtk.Align.FILL)

        self.toggle_button = Gtk.Button(label="Mostrar Mensagem")
        self.toggle_button.connect("clicked", self.on_toggle_view)
        self.toggle_button.set_hexpand(True)
        self.toggle_button.set_halign(Gtk.Align.FILL)

        button_box.pack_start(self.button, True, True, 0)
        button_box.pack_start(self.toggle_button, True, True, 0)

        self.box_main.pack_start(button_box, False, False, 6)

        # TEXTVIEW
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textbuffer = self.textview.get_buffer()

        self.text_scrolled = Gtk.ScrolledWindow()
        self.text_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.text_scrolled.add(self.textview)
        self.text_scrolled.set_min_content_height(300)

        # === GRAPH WITH ZOOM / PAN TOOLBAR ===
        from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3
        
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.set_hexpand(True)
        self.canvas.set_vexpand(True)
        
        # Toolbar for zoom, pan, save, reset
        self.toolbar = NavigationToolbar2GTK3(self.canvas, self)
        
        # Add toolbar first, then graph canvas
        self.box_main.pack_start(self.toolbar, False, False, 0)
        self.box_main.pack_start(self.canvas, True, True, 0)
        
        # Scroll-wheel zoom function
        def scroll_zoom(event):
            # Zoom EACH subplot horizontally (X only)
            for ax in self.figure.axes:
                x_min, x_max = ax.get_xlim()
        
                # zoom in or out
                scale = 0.9 if event.step > 0 else 1.1
                new_width = (x_max - x_min) * scale
        
                # cursor X position
                cx = event.xdata
                if cx is None:
                    continue
                
                # compute new x-limits centered at cursor
                ax.set_xlim([cx - new_width / 2, cx + new_width / 2])
        
            # redraw
            self.canvas.draw_idle()

        
        # Attach scroll zoom to the canvas
        self.canvas.mpl_connect("scroll_event", scroll_zoom)
        
        # Add textview below graph (hidden initially)
        self.box_main.pack_start(self.text_scrolled, True, True, 0)
        self.text_scrolled.hide()

    def on_toggle_view(self, button):
        if self.canvas.get_visible():
            self.canvas.hide()
            self.text_scrolled.show()
            self.toggle_button.set_label("Mostrar Gráficos")
        else:
            self.text_scrolled.hide()
            self.canvas.show()
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

        samples_per_bit = 20

        # --- DIGITAL MODULATION ---
        if mod_digital == "NRZ":
            banda = upsample_signal(NRZ_polar_modulation(mensagem_bits), samples_per_bit)
        elif mod_digital == "bipolar":
            banda = upsample_signal(bipolar_modulation(mensagem_bits), samples_per_bit)
        elif mod_digital == "manchester":
            banda = upsample_signal(manchester_modulation(mensagem_bits), samples_per_bit)
        else:
            banda = np.array([])

        # --- CARRIER MODULATION ---
        if mod_portadora == "ASK":
            portadora = ASK_modulation(banda.tolist() if isinstance(banda, np.ndarray) else banda)

        elif mod_portadora == "FSK":
            portadora = FSK_modulation(banda.tolist() if isinstance(banda, np.ndarray) else banda)

        elif mod_portadora == "PSK":
            portadora = PSK_modulation(banda.tolist() if isinstance(banda, np.ndarray) else banda)

        elif mod_portadora == "QPSK":
            portadora = QPSK_modulation(banda.tolist() if isinstance(banda, np.ndarray) else banda)

        elif mod_portadora == "16QAM":
            portadora = QAM16_modulation(
                banda.tolist() if isinstance(banda, np.ndarray) else banda
            )

        else:
            portadora = None



        # --- DRAW ---
        self.figure.clf()
        ax1 = self.figure.add_subplot(211)
        ax1.set_title(f"Modulação Digital - {mod_digital}", color="white")
        ax1.plot(banda, color="#2d8bff")
        ax1.grid(True)

        if portadora is not None:
            ax2 = self.figure.add_subplot(212)
            ax2.set_title(f"Modulação por Portadora - {mod_portadora}", color="white")
            ax2.plot(portadora, color="#ff6666")
            ax2.grid(True)

        self.canvas.draw()

        # --- SEND THREAD ---
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

                msg = resposta["mensagem"]
                etapas_tx = resposta.get("etapas_tx", {})
                etapas_rx = resposta.get("etapas_rx", {})

                texto = f"Mensagem recebida: {msg}\n\n--- Etapas no Transmissor ---\n"
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
