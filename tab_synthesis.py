from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QComboBox, QPushButton, QTextEdit, 
                               QTabWidget, QSplitter, QRadioButton, QButtonGroup, QLabel, QCheckBox)
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import schemdraw
import schemdraw.elements as elm
import numpy as np

from filter_math_synthesis import (get_filter_info, design_filter_transfer_function, 
                                   calc_bode_data, synthesize_lc_ladder, calc_filter_parameters)
from filter_math import format_eng

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('#fbfbfd')
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

class TabSynthesis(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.plot_data = None

    def init_ui(self):
        main_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.combo_tech = QComboBox()
        self.combo_tech.addItems(["Passivo LC", "Passivo RC", "Attivo Sallen-Key"])
        form_layout.addRow("Tecnologia:", self.combo_tech)
        
        self.combo_approx = QComboBox()
        self.combo_approx.addItems(["Butterworth", "Chebyshev I", "Chebyshev II", "Ellittico (Cauer)", "Bessel"])
        form_layout.addRow("Approssimazione:", self.combo_approx)

        self.input_fp = QLineEdit("1000")
        self.input_fs = QLineEdit("2000")
        self.input_Ap = QLineEdit("1.0")
        self.input_As = QLineEdit("40.0")
        self.input_R1 = QLineEdit("50")

        form_layout.addRow("Fine Banda Passante (f_p) [Hz]:", self.input_fp)
        form_layout.addRow("Inizio Banda Oscura (f_s) [Hz]:", self.input_fs)
        form_layout.addRow("Attenuaz. max (A_p) [dB]:", self.input_Ap)
        form_layout.addRow("Attenuaz. min (A_s) [dB]:", self.input_As)
        form_layout.addRow("Terminazione (R_1) [Ω]:", self.input_R1)

        left_layout.addLayout(form_layout)

        # Toggle Scala Lineare globale per i grafici
        self.check_linear_x = QCheckBox("Usa asse X lineare nei grafici")
        self.check_linear_x.toggled.connect(self.refresh_all_plots)
        left_layout.addWidget(self.check_linear_x)

        self.btn_synth = QPushButton("Esegui Sintesi")
        self.btn_synth.clicked.connect(self.run_synthesis)
        left_layout.addWidget(self.btn_synth)
        left_layout.addStretch()
        left_panel.setLayout(left_layout)

        self.right_tabs = QTabWidget()
        self.tab_info = QTextEdit()
        self.tab_info.setReadOnly(True)
        self.right_tabs.addTab(self.tab_info, "Info Teoriche")

        self.tab_circ = QWidget()
        circ_layout = QVBoxLayout()
        self.canvas_circ = PlotCanvas(self, width=6, height=3)
        circ_layout.addWidget(self.canvas_circ)
        self.tab_circ.setLayout(circ_layout)
        self.right_tabs.addTab(self.tab_circ, "Circuito")

        self.tab_bode_mag = QWidget()
        bode_mag_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        
        self.radio_lin = QRadioButton("Modulo |H(s)|")
        self.radio_db10 = QRadioButton("Modulo 10log|H(s)|")
        self.radio_db20 = QRadioButton("Guadagno 20log|H(s)|")
        self.radio_db20.setChecked(True)
        
        self.bg_scale = QButtonGroup()
        self.bg_scale.addButton(self.radio_lin)
        self.bg_scale.addButton(self.radio_db10)
        self.bg_scale.addButton(self.radio_db20)
        self.bg_scale.buttonClicked.connect(self.update_mag_plot)
        
        control_layout.addWidget(self.radio_lin)
        control_layout.addWidget(self.radio_db10)
        control_layout.addWidget(self.radio_db20)
        control_layout.addStretch()
        
        bode_mag_layout.addLayout(control_layout)
        self.canvas_mag = PlotCanvas(self)
        bode_mag_layout.addWidget(self.canvas_mag)
        self.tab_bode_mag.setLayout(bode_mag_layout)
        self.right_tabs.addTab(self.tab_bode_mag, "Bode Ampiezza")

        self.tab_bode_phase = QWidget()
        phase_layout = QVBoxLayout()
        self.canvas_phase = PlotCanvas(self)
        phase_layout.addWidget(self.canvas_phase)
        self.tab_bode_phase.setLayout(phase_layout)
        self.right_tabs.addTab(self.tab_bode_phase, "Bode Fase")

        self.tab_delay = QWidget()
        delay_layout = QVBoxLayout()
        self.canvas_delay = PlotCanvas(self)
        delay_layout.addWidget(self.canvas_delay)
        self.tab_delay.setLayout(delay_layout)
        self.right_tabs.addTab(self.tab_delay, "Ritardo di Gruppo")

        splitter.addWidget(left_panel)
        splitter.addWidget(self.right_tabs)
        splitter.setSizes([320, 600])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def refresh_all_plots(self):
        if self.plot_data:
            self.update_mag_plot()
            self.update_phase_plot()
            self.update_delay_plot()

    def run_synthesis(self):
        try:
            approx = self.combo_approx.currentText()
            fp = float(self.input_fp.text())
            fs = float(self.input_fs.text())
            Ap = float(self.input_Ap.text())
            As = float(self.input_As.text())
            R1 = float(self.input_R1.text())

            # Calcolo Parametri Filtro
            k, eps, d_fact = calc_filter_parameters(fp, fs, Ap, As)
            html_info = get_filter_info(approx)
            
            N, Wn, b, a = design_filter_transfer_function(approx, fp, fs, Ap, As)
            if N is None: return
                
            html_info += "<h3>Parametri Calcolati</h3><ul>"
            html_info += f"<li><b>Ordine calcolato (N):</b> {N}</li>"
            html_info += f"<li><b>Fattore di Selettività (k = f_p/f_s):</b> {k:.4f}</li>"
            html_info += f"<li><b>Fattore di Ripple (ε):</b> {eps:.4f}</li>"
            html_info += f"<li><b>Fattore di Discriminazione (d):</b> {d_fact:.4e}</li></ul>"
            
            components = synthesize_lc_ladder(approx, N, fp, Ap, R1)
            self.draw_circuit(components, R1)
            self.tab_info.setHtml(html_info)

            f_hz, mag_lin, phase, delay = calc_bode_data(b, a, fp, fs)
            self.plot_data = (f_hz, mag_lin, phase, delay, fp, fs)
            self.refresh_all_plots()

        except Exception as e:
            self.tab_info.setHtml(f"<p style='color:red;'>Errore: {str(e)}</p>")

    def draw_circuit(self, components, R1):
        """Disegna il circuito evitando sovrapposizioni e allineando la massa in basso."""
        self.canvas_circ.axes.clear()
        if not components:
            self.canvas_circ.axes.text(0.5, 0.5, "Schema Cauer/Darlington non ancora implementato.", ha='center', va='center')
            self.canvas_circ.axes.axis('off')
            self.canvas_circ.draw()
            return

        d = schemdraw.Drawing(canvas=self.canvas_circ.axes)
        d.config(fontsize=12, unit=2.5) 
        
        # Generatore e R1
        d += elm.SourceSin().up().label('E', 'left')
        d += elm.Resistor().right().label(f'R_S\n{R1}Ω')
        
        for i, comp in enumerate(components):
            c_type, val = comp
            val_str = format_eng(val, "H" if c_type == 'L' else "F")
            
            if c_type == 'L':
                d += elm.Inductor().right().label(f'{c_type}{i+1}\n{val_str}')
            else:
                # Diramazione verso massa
                d.push()
                d += elm.Capacitor().down().label(f'{c_type}{i+1}\n{val_str}', loc='bottom')
                d += elm.Ground() 
                d.pop()

        # FIX: Aggiunge una linea orizzontale prima del carico per separarlo
        # visivamente dall'ultimo componente ed evitare sovrapposizioni.
        d += elm.Line().right().length(1.0)
        
        # Carico d'uscita
        d += elm.Resistor().down().label(f'R_L\n{R1}Ω')
        d += elm.Ground()
        
        d.draw(show=False)
        self.canvas_circ.axes.set_aspect('equal')
        self.canvas_circ.axes.axis('off')
        self.canvas_circ.draw()

    def _plot_base(self, canvas, x_data, y_data, fp, fs, title, ylabel, color):
        ax = canvas.axes
        ax.clear()
        
        if self.check_linear_x.isChecked():
            ax.plot(x_data, y_data, color=color, linewidth=2)
        else:
            ax.semilogx(x_data, y_data, color=color, linewidth=2)
            
        ax.axvline(fp, color='green', linestyle='--', alpha=0.5, label='fp')
        ax.axvline(fs, color='red', linestyle='--', alpha=0.5, label='fs')
        ax.set_title(title)
        ax.set_xlabel("Frequenza (Hz)")
        ax.set_ylabel(ylabel)
        ax.grid(True, which="both", ls="--", alpha=0.5)
        if title == "Risposta in Ampiezza": ax.legend()
        canvas.draw()

    def update_mag_plot(self):
        if not self.plot_data: return
        f_hz, mag_lin, phase, delay, fp, fs = self.plot_data
        
        mag_safe = np.maximum(mag_lin, 1e-12)
        if self.radio_db20.isChecked():
            y_data = 20 * np.log10(mag_safe)
            ylabel = "20log|H(s)| (dB)"
        elif self.radio_db10.isChecked():
            y_data = 10 * np.log10(mag_safe)
            ylabel = "10log|H(s)| (dB)"
        else:
            y_data = mag_lin
            ylabel = "|H(s)|"

        self._plot_base(self.canvas_mag, f_hz, y_data, fp, fs, "Risposta in Ampiezza", ylabel, "#0071e3")

    def update_phase_plot(self):
        if not self.plot_data: return
        self._plot_base(self.canvas_phase, self.plot_data[0], self.plot_data[2], self.plot_data[4], self.plot_data[5], "Risposta in Fase", "Fase (Gradi)", "#ff9500")

    def update_delay_plot(self):
        if not self.plot_data: return
        delay_clipped = np.clip(self.plot_data[3], -0.01, np.percentile(self.plot_data[3], 95) * 1.5)
        self._plot_base(self.canvas_delay, self.plot_data[0], delay_clipped, self.plot_data[4], self.plot_data[5], "Ritardo di Gruppo", "Ritardo (s)", "#34c759")