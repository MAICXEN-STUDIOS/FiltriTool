# dmg_settings.py
import os

# Nome del volume che apparirà sul Mac
volume_name = "FiltriTool"

# Formato compresso del DMG
format = 'UDBZ'

# I file da includere (la tua app appena compilata)
files = ['dist/FiltriTool.app']

# Crea la scorciatoia per la cartella Applicazioni del Mac
symlinks = {'Applications': '/Applications'}

# Nasconde i file di sistema come .DS_Store
badge_icon = None
hide_extensions = ['FiltriTool.app']

# Dimensione della finestra che si apre facendo doppio click sul DMG
window_rect = ((200, 200), (600, 400))

# Posizione delle icone nella finestra (X, Y)
icon_locations = {
    'FiltriTool.app': (140, 120),
    'Applications': (460, 120)
}