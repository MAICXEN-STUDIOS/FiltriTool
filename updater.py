import sys
import os
import platform
import tempfile
import subprocess
import zipfile
import requests
from packaging import version
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QTextEdit, QProgressBar, QApplication)

# Sostituisci con il link raw del tuo version.json su GitHub
UPDATE_URL = "https://raw.githubusercontent.com/MAICXEN-STUDIOS/FiltriTool/refs/heads/main/version.json"
CURRENT_VERSION = "1.1.0"

class UpdateCheckerThread(QThread):
    """Interroga il server per trovare nuove versioni."""
    update_available = Signal(str, str, str)  # version, notes, download_url

    def run(self):
        try:
            response = requests.get(UPDATE_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            latest_version = data.get("latest_version", "0.0.0")
            release_notes = data.get("release_notes", "")
            
            # Seleziona il link in base al sistema operativo
            if platform.system() == "Windows":
                download_url = data.get("download_url_win", "")
            else:
                download_url = data.get("download_url_mac", "")

            if version.parse(latest_version) > version.parse(CURRENT_VERSION) and download_url:
                self.update_available.emit(latest_version, release_notes, download_url)
                
        except Exception:
            pass


class DownloadThread(QThread):
    """Scarica il file in background riportando la percentuale."""
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=10)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            # Crea un file temporaneo sicuro
            ext = ".exe" if platform.system() == "Windows" else ".zip"
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            
            with open(tmp_file.name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)
                            
            self.finished.emit(tmp_file.name)
        except Exception as e:
            self.error.emit(str(e))


class UpdateDialog(QDialog):
    """Interfaccia dell'Updater Enterprise."""
    def __init__(self, latest_version, release_notes, download_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiornamento Software")
        self.resize(450, 300)
        self.setModal(True)
        self.download_url = download_url

        self.init_ui(latest_version, release_notes)

    def init_ui(self, latest_version, release_notes):
        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)

        self.lbl_title = QLabel(f"<h2>Versione {latest_version} disponibile!</h2>")
        self.lbl_subtitle = QLabel("È raccomandato aggiornare per ottenere le ultime funzionalità.")
        self.layout.addWidget(self.lbl_title)
        self.layout.addWidget(self.lbl_subtitle)

        self.txt_notes = QTextEdit()
        self.txt_notes.setReadOnly(True)
        self.txt_notes.setText(release_notes)
        self.layout.addWidget(self.txt_notes)

        # Barra di progresso (Nascosta di default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch()
        
        self.btn_skip = QPushButton("Ignora per ora")
        self.btn_skip.setStyleSheet("background-color: #e8e8ed; color: #1d1d1f;")
        self.btn_skip.clicked.connect(self.reject)
        
        self.btn_update = QPushButton("Scarica e Installa")
        self.btn_update.clicked.connect(self.start_download)
        
        self.btn_layout.addWidget(self.btn_skip)
        self.btn_layout.addWidget(self.btn_update)
        
        self.layout.addLayout(self.btn_layout)
        self.setLayout(self.layout)

    def start_download(self):
        # Cambia l'interfaccia utente in modalità Download
        self.txt_notes.hide()
        self.btn_skip.hide()
        self.btn_update.setEnabled(False)
        self.btn_update.setText("Scaricamento in corso...")
        self.progress_bar.show()
        
        self.downloader = DownloadThread(self.download_url)
        self.downloader.progress.connect(self.progress_bar.setValue)
        self.downloader.finished.connect(self.install_and_restart)
        self.downloader.error.connect(self.show_error)
        self.downloader.start()

    def show_error(self, error_msg):
        self.lbl_subtitle.setText(f"<span style='color:red;'>Errore di download: {error_msg}</span>")
        self.btn_update.setText("Riprova")
        self.btn_update.setEnabled(True)
        self.btn_skip.show()

    def install_and_restart(self, file_path):
        self.lbl_subtitle.setText("Preparazione dell'installazione...")
        self.progress_bar.setRange(0, 0) # Effetto caricamento infinito
        
        # Blocca l'esecuzione se stiamo sviluppando da main.py (non compilato)
        if not getattr(sys, 'frozen', False):
            self.lbl_subtitle.setText("Aggiornamento simulato con successo (Modalità Sviluppatore).")
            self.btn_skip.setText("Chiudi")
            self.btn_skip.show()
            return

        if platform.system() == "Windows":
            # WINDOWS: Lancia il setup.exe scaricato
            # Aggiungendo "/SILENT" installa senza chiedere conferme (se supportato da Inno Setup)
            os.startfile(file_path)
            QApplication.quit()
            
        elif platform.system() == "Darwin": # MAC
            # Trova il percorso dell'app attualmente in esecuzione
            current_exe = sys.executable
            current_app = current_exe[:current_exe.find('.app') + 4]
            
            temp_dir = tempfile.mkdtemp()
            script_path = os.path.join(temp_dir, "update_mac.sh")
            
            # Crea lo script bash fantasma
            with open(script_path, "w") as f:
                f.write(f"""#!/bin/bash
                # 1. Aspetta 2 secondi per far chiudere l'app vecchia
                sleep 2

                # 2. FIX PYTHON: Usa l'utility 'unzip' nativa del Mac per estrarre l'archivio.
                # Questo è FONDAMENTALE perché preserva i symlink (che zipfile di Python rompeva).
                unzip -q "{file_path}" -d "{temp_dir}"

                # 3. Trova l'app appena estratta (il cui nome finisce per .app)
                EXTRACTED_APP=$(find "{temp_dir}" -name "*.app" -maxdepth 1 | head -n 1)

                if [ -n "$EXTRACTED_APP" ]; then
                    # 4. Cancella la vecchia app
                    rm -rf "{current_app}"
                    
                    # 5. Sposta la nuova app al suo posto
                    mv "$EXTRACTED_APP" "{current_app}"
                    
                    # 6. FIX APPLE: Rimuove la quarantena di macOS (ignora gli errori se non c'è)
                    xattr -cr "{current_app}" 2>/dev/null
                    
                    # 7. Riapri l'app aggiornata
                    open "{current_app}"
                fi
                """)
            
            # Rende lo script eseguibile e lo lancia in modo indipendente
            os.chmod(script_path, 0o755)
            subprocess.Popen(['sh', script_path], start_new_session=True)
            QApplication.quit()