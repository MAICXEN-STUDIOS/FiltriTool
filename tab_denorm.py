from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, 
                               QLineEdit, QComboBox, QPushButton, QTextEdit)
from PySide6.QtCore import Qt
from filter_math import denormalize_component, format_eng, get_commercial_value

class TabDenorm(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.combo_comp = QComboBox()
        self.combo_comp.addItems(["Induttore (Lₙ)", "Condensatore (Cₙ)"])
        form_layout.addRow("Componente di partenza:", self.combo_comp)

        self.input_val_n = QLineEdit("1.0")
        form_layout.addRow("Valore normalizzato:", self.input_val_n)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["LP (Passa-Basso)", "HP (Passa-Alto)", "BP (Passa-Banda)", "SB (Elimina-Banda)"])
        self.combo_type.currentIndexChanged.connect(self.toggle_band_input)
        form_layout.addRow("Trasforma in:", self.combo_type)

        self.input_w0 = QLineEdit("1000")
        self.input_R1 = QLineEdit("50")
        self.input_B = QLineEdit("100")
        self.input_B.setEnabled(False) 
        
        form_layout.addRow("Pulsazione di rif. (ω₀) [rad/s]:", self.input_w0)
        form_layout.addRow("Resistenza di rif. (R₁) [Ω]:", self.input_R1)
        form_layout.addRow("Banda (B) [rad/s]:", self.input_B)

        layout.addLayout(form_layout)

        self.btn_calc = QPushButton("Calcola Denormalizzazione")
        self.btn_calc.clicked.connect(self.calculate)
        layout.addWidget(self.btn_calc)

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        # Assicura uno sfondo pulito senza forzare un font monospaziato globale per non rompere il LaTeX
        self.text_output.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.text_output)

        self.setLayout(layout)

    def toggle_band_input(self):
        filter_type = self.combo_type.currentText()[:2]
        self.input_B.setEnabled(filter_type in ["BP", "SB"])

    def calculate(self):
        try:
            comp_type = 'L' if self.combo_comp.currentIndex() == 0 else 'C'
            val_n = float(self.input_val_n.text())
            w0 = float(self.input_w0.text())
            R1 = float(self.input_R1.text())
            B = float(self.input_B.text()) if self.input_B.isEnabled() else None
            f_type = self.combo_type.currentText()[:2]

            res = denormalize_component(comp_type, val_n, f_type, w0, R1, B)
            self.display_result(res, comp_type, f_type)

        except ValueError:
            self.text_output.setHtml("<span style='color: red;'>Errore: Inserisci valori numerici validi.</span>")

    def render_value_block(self, symbol, value, unit, formula_html):
        """Metodo di supporto per generare l'HTML formattato per un singolo componente calcolato."""
        val_sci = f"{value:.5e}"
        val_eng = format_eng(value, unit)
        
        comm_val = get_commercial_value(value)
        comm_eng = format_eng(comm_val, unit)
        
        block = f"{formula_html}"
        block += f"<div style='margin-left: 20px;'>"
        block += f"<p>&#8226; <b>Esatto:</b> {symbol} = {val_sci} {unit} = <b style='font-size:1.1em;'>{val_eng}</b></p>"
        block += f"<p>&#8226; <b>Commerciale (E24):</b> <b style='color:#0071e3; font-size:1.1em;'>{comm_eng}</b></p>"
        block += f"</div>"
        return block

    def display_result(self, res, comp_type, f_type):
        simbolo = "Lₙ" if comp_type == 'L' else "Cₙ"
        
        html = f"<h3>Trasformazione da {simbolo} a {f_type}</h3>"
        html += f"<p><b>Struttura Finale:</b> {res['type']}</p>"
        html += f"<p style='color: gray;'><i>{res['desc']}</i></p><hr>"

        if 'value' in res:
            simb_out = "L" if "Induttore" in res['type'] else "C"
            unita = "H" if simb_out == "L" else "F"
            html += self.render_value_block(simb_out, res['value'], unita, res['formula'])
        else:
            html += self.render_value_block("L", res['L_val'], "H", res['formula_L'])
            html += "<hr style='border-top: 1px dashed #ccc; margin: 10px 0;'>"
            html += self.render_value_block("C", res['C_val'], "F", res['formula_C'])

        self.text_output.setHtml(html)