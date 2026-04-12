import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette
from main_window import FilterDesignTool

def get_dynamic_stylesheet(app):
    lightness = app.palette().color(QPalette.ColorRole.Window).lightness()
    is_dark = lightness < 128

    if is_dark:
        bg_main, bg_panel, bg_input = "#1c1c1e", "#2c2c2e", "#3a3a3c"
        text_main, text_dim, border = "#f5f5f7", "#a1a1a6", "#48484a"
        accent, accent_hover = "#0a84ff", "#0071e3"
    else:
        bg_main, bg_panel, bg_input = "#f5f5f7", "#ffffff", "#ffffff"
        text_main, text_dim, border = "#1d1d1f", "#515154", "#d2d2d7"
        accent, accent_hover = "#0071e3", "#0077ed"

    return f"""
    QMainWindow {{ background-color: {bg_main}; }}
    QWidget {{ font-family: -apple-system, "SF Pro Display", "Segoe UI", Roboto, sans-serif; font-size: 14px; color: {text_main}; }}
    QTabWidget::pane {{ border: 1px solid {border}; border-radius: 8px; background: {bg_panel}; }}
    QTabBar::tab {{ background: {bg_main}; border: 1px solid {border}; padding: 8px 16px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; color: {text_dim}; }}
    QTabBar::tab:selected {{ background: {bg_panel}; border-bottom-color: {bg_panel}; font-weight: bold; color: {text_main}; }}
    QLineEdit, QComboBox {{ border: 1px solid {border}; border-radius: 6px; padding: 6px 10px; background: {bg_input}; color: {text_main}; }}
    QLineEdit:focus, QComboBox:focus {{ border: 1px solid {accent}; }}
    QComboBox::drop-down {{ width: 24px; border: none; }}
    QComboBox QAbstractItemView {{ border: 1px solid {border}; border-radius: 6px; background: {bg_input}; selection-background-color: {accent}; color: {text_main}; outline: none; }}
    QPushButton {{ background-color: {accent}; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 500; }}
    QPushButton:hover {{ background-color: {accent_hover}; }}
    QTextEdit {{ border: 1px solid {border}; border-radius: 8px; background: {bg_panel}; padding: 12px; color: {text_main}; }}
    """

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    app.setStyleSheet(get_dynamic_stylesheet(app))
    
    window = FilterDesignTool()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()