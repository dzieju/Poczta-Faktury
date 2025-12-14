"""
Tab for Exchange mail with sub-tabs for configuration

Source: Copied and adapted from dzieju-app2 repository
Original file: https://github.com/dzieju/dzieju-app2/blob/main/gui/tab_poczta_exchange.py
"""
import tkinter as tk
from tkinter import ttk

# Import the Exchange mail configuration widget
try:
    from gui.exchange_mail_config_widget import ExchangeMailConfigWidget
    HAVE_EXCHANGE_WIDGET = True
except ImportError as e:
    HAVE_EXCHANGE_WIDGET = False
    IMPORT_ERROR = str(e)


class TabPocztaExchange(ttk.Frame):
    """
    Exchange mail tab with sub-tabs:
    - Konfiguracja poczty (Mail Configuration)
    
    Note: Search functionality is handled in the main application
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        if not HAVE_EXCHANGE_WIDGET:
            # Show error message if widget couldn't be imported
            error_frame = ttk.Frame(self)
            error_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            error_label = ttk.Label(
                error_frame, 
                text=f"Nie można załadować widgetu konfiguracji Exchange:\n{IMPORT_ERROR}\n\nSprawdź czy zainstalowano wymagane zależności.",
                justify="center",
                foreground="red"
            )
            error_label.pack(expand=True)
            return
        
        # Create the configuration widget directly (no sub-tabs for now)
        self.config_widget = ExchangeMailConfigWidget(self)
        self.config_widget.pack(fill="both", expand=True)
        
        # Callback for when configuration is saved
        self.config_widget.on_config_saved = self._on_config_changed
    
    def _on_config_changed(self):
        """Called when configuration is saved"""
        # Future: can refresh other tabs or notify parent
        pass
