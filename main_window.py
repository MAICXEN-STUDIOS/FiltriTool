from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from tab_denorm import TabDenorm
from tab_synthesis import TabSynthesis
from updater import UpdateCheckerThread, UpdateDialog, CURRENT_VERSION

class FilterDesignTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Sintesi Filtri - Electronics Helper (v{CURRENT_VERSION})")
        self.resize(750, 550)

        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.tabs = QTabWidget()
        self.tab1 = TabDenorm()
        self.tab2 = TabSynthesis()

        self.tabs.addTab(self.tab1, "Denormalizzazione Componenti")
        self.tabs.addTab(self.tab2, "Sintesi Completa")
        
        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.check_for_updates()

    def check_for_updates(self):
        """Lancia il controllo versioni in un thread separato."""
        self.update_thread = UpdateCheckerThread()
        self.update_thread.update_available.connect(self.show_update_dialog)
        self.update_thread.start()

    def show_update_dialog(self, latest_version, release_notes, download_url):
        """Viene chiamata automaticamente se c'è un aggiornamento."""
        dialog = UpdateDialog(latest_version, release_notes, download_url, self)
        dialog.exec()