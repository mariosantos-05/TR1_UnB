import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk

from threading import Thread
import numpy as np
import matplotlib
matplotlib.use('GTK4Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk4agg import FigureCanvasGTK4Agg as FigureCanvas


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

        # === Apply Dark CSS ===
        css = b"""
        window {
            background: linear-gradient(180deg, #141820, #0e1117);
            color: #e0e6ed;
        }
        box.main {
            padding: 16px;
        }
        frame {
            background: #1d232f;
            border-radius: 10px;
            border: 1px solid #2b3240;
            margin-bottom: 12px;
            padding: 10px;
        }
        button {
            background: #2d8bff;
            color: white;
            border-radius: 8px;
            padding: 8px 14px;
            font-weight: bold;
        }
        button:hover {
            background: #1c6ed6;
        }
        entry {
            background: #222836;
            color: white;
            border-radius: 6px;
            padding: 6px;
            border: 1px solid #333c4f;
        }
        label {
            color: #e0e6ed;
        }
        label.title {
            font-size: 18px;
            font-weight: bold;
            color: #46a0ff;
            margin-bottom: 6px;
        }
        spinbutton {
            background: #222836;
            color: white;
        }
        textview {
            background: #1b202b;
            color: #b5c0d0;
            border-radius: 8px;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # === MAIN CONTAINER ===
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, css_name="main")
        self.set_child(main_box)

        # === CONTROLS FRAME ===
        frame_controls = Gtk.Frame()
        main_box.append(frame_controls)

        box_controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        frame_controls.set_child(box_controls)

        label_title = Gtk.Label(label="Configurações de Simulação")
        label_title.add_css_class("title")
        box_controls.append(label_title)

        # --- Entry ---
        self.entry = Gtk.Entry(placeholder_text="Digite sua mensagem aqui")
        box_controls.append(self.entry)

        # --- Grid for parameters ---
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
            ["NRZ", "bipolar", "manchester", "8QAM"],
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

        # --- Noise control (correção aqui!) ---
        lbl_noise = Gtk.Label(label="Taxa de Ruído (0.0 a 1.0):", halign=Gtk.Align.END)
        adj = Gtk.Adjustment(
            value=0.0,
            lower=0.0,
            upper=1.0,
            step_increment=0.01,
            page_increment=0.1,
            page_size=0.0
        )
        self.noise_spin = Gtk.SpinButton(adjustment=adj, digits=2)
        grid.attach(lbl_noise, 2, 0, 1, 1)
        grid.attach(self.noise_spin, 3, 0, 1, 1)

        # --- Buttons ---
        box_buttons = Gtk.Box(spacing=10, halign=Gtk.Align.END, margin_top=10)
        box_controls.append(box_buttons)

        self.button_simular = Gtk.Button(label="Simular Transmissão")
        self.button_simular.connect("clicked", self.on_button_clicked)
        box_buttons.append(self.button_simular)

        self.button_toggle = Gtk.Button(label="Mostrar Mensagem")
        self.button_toggle.connect("clicked", self.on_toggle_view)
        box_buttons.append(self.button_toggle)

        # === VIEW FRAME ===
        frame_view = Gtk.Frame()
        main_box.append(frame_view)

        box_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        frame_view.set_child(box_view)

        label_results = Gtk.Label(label="Resultados da Simulação")
        label_results.add_css_class("title")
        box_view.append(label_results)

        # --- Graph ---
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        box_view.append(self.canvas)

        # --- Text view ---
        self.textview = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.textbuffer = self.textview.get_buffer()
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.textview)
        scrolled.set_min_content_height(250)
        box_view.append(scrolled)
        scrolled.hide()
        self.text_scrolled = scrolled
        self.graph_widget = self.canvas

    # --- Behavior ---
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
        mod_digital = self.dropdowns[3].get_selected_item().get_string()
        mod_portadora = self.dropdowns[4].get_selected_item().get_string()

        # --- Gerar sinais simulados ---
        t = np.linspace(0, 1, 300)
        if mod_digital == "NRZ":
            banda = np.sign(np.sin(2 * np.pi * 5 * t))
        elif mod_digital == "bipolar":
            banda = np.sin(2 * np.pi * 5 * t)
        elif mod_digital == "manchester":
            banda = np.sign(np.sin(2 * np.pi * 10 * t))
        else:
            banda = np.random.randn(len(t)) * 0.2

        if mod_portadora == "ASK":
            portadora = banda * np.cos(2 * np.pi * 20 * t)
        elif mod_portadora == "FSK":
            portadora = np.sin(2 * np.pi * (10 + 5 * banda) * t)
        else:
            portadora = None

        # --- Plot ---
        self.figure.clf()
        ax1 = self.figure.add_subplot(211)
        ax1.plot(t, banda, color='#2d8bff')
        ax1.set_title(f"Modulação Digital - {mod_digital}", color="white")
        ax1.grid(True, linestyle='--', alpha=0.4)
        ax1.tick_params(colors="lightgray")

        if portadora is not None:
            ax2 = self.figure.add_subplot(212)
            ax2.plot(t, portadora, color='#ff6666')
            ax2.set_title(f"Modulação por Portadora - {mod_portadora}", color="white")
            ax2.grid(True, linestyle='--', alpha=0.4)
            ax2.tick_params(colors="lightgray")

        self.figure.tight_layout()
        self.canvas.draw()

        # --- Texto de simulação ---
        def tarefa():
            texto = f"""
Mensagem simulada: "{msg}"

Parâmetros escolhidos:
- Modulação Digital: {mod_digital}
- Modulação Portadora: {mod_portadora}
- Ruído: {self.noise_spin.get_value():.2f}

(Resultados detalhados da transmissão aparecerão aqui futuramente)
"""
            GLib.idle_add(self.exibir_resposta, texto.strip())

        Thread(target=tarefa, daemon=True).start()


if __name__ == "__main__":
    app = NetworkApp()
    app.run()
