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

# L'UNICO PUNTO IN CUI DOVRAI AGGIORNARE LA VERSIONE D'ORA IN POI:
CURRENT_VERSION = "1.3.0"

# L'API di GitHub che legge in automatico la tua pagina "Releases"
API_URL = "https://api.github.com/repos/MAICXEN-STUDIOS/FiltriTool/releases/latest"

class UpdateCheckerThread(QThread):
    """Interroga direttamente GitHub API per trovare nuove versioni."""
    update_available = Signal(str, str, str)  # version, notes, download_url

    def run(self):
        try:
            response = requests.get(API_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # GitHub restituisce il tag (es. "v1.3.0"). Lrstrip("v") toglie la 'v' per fare il calcolo matematico.
            latest_tag = data.get("tag_name", "v0.0.0").lstrip("v")
            
            # Prende le note scritte direttamente da te sulla pagina GitHub!
            release_notes = data.get("body", "Aggiornamento disponibile.")
            
            # I link statici definitivi
            if platform.system() == "Windows":
                download_url = "https://github.com/MAICXEN-STUDIOS/FiltriTool/releases/latest/download/FiltriTool_Win.zip"
            else:
                download_url = "https://github.com/MAICXEN-STUDIOS/FiltriTool/releases/latest/download/FiltriTool_Mac.zip"

            if version.parse(latest_tag) > version.parse(CURRENT_VERSION):
                self.update_available.emit(latest_tag, release_notes, download_url)
                
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
            # Trova l'eseguibile attuale e la sua cartella
            current_exe = sys.executable
            current_dir = os.path.dirname(current_exe)
            
            temp_dir = tempfile.mkdtemp()
            # Su Windows usiamo la libreria zipfile nativa (non ha i problemi dei symlink del Mac)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            # Cerca la cartella appena estratta (che contiene il nuovo eseguibile)
            extracted_folder = temp_dir
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                # MODIFICA QUESTA RIGA: Cambia "Electronics" in "FiltriTool"
                if os.path.isdir(item_path) and "FiltriTool" in item:
                    extracted_folder = item_path
                    break

            # Crea lo script BAT fantasma per Windows
            script_path = os.path.join(temp_dir, "update_win.bat")
            with open(script_path, "w") as f:
                f.write(f"""@echo off
                    timeout /t 2 /nobreak > NUL
                    xcopy "{extracted_folder}\*" "{current_dir}\" /s /e /y
                    start "" "{current_exe}"
                    del "%~f0"
                    """)
            # Esegue il file BAT e chiude l'app
            subprocess.Popen([script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            QApplication.quit()

        elif platform.system() == "Darwin": # MAC
            # [Il codice per il Mac che avevamo già scritto con unzip -q rimane esattamente qui]
            current_exe = sys.executable
            current_app = current_exe[:current_exe.find('.app') + 4]
            
            temp_dir = tempfile.mkdtemp()
            script_path = os.path.join(temp_dir, "update_mac.sh")
            
            with open(script_path, "w") as f:
                f.write(f"""#!/bin/bash
                    sleep 2
                    unzip -q "{file_path}" -d "{temp_dir}"
                    EXTRACTED_APP=$(find "{temp_dir}" -name "*.app" -maxdepth 1 | head -n 1)
                    if [ -n "$EXTRACTED_APP" ]; then
                        rm -rf "{current_app}"
                        mv "$EXTRACTED_APP" "{current_app}"
                        xattr -cr "{current_app}" 2>/dev/null
                        open "{current_app}"
                    fi
                    """)
            os.chmod(script_path, 0o755)
            subprocess.Popen(['sh', script_path], start_new_session=True)
            QApplication.quit()