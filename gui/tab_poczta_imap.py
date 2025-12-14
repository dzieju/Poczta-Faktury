"""
Tab for IMAP/POP3 mail with configuration

Source: Copied and adapted from dzieju-app2 repository
Original file: https://github.com/dzieju/dzieju-app2/blob/main/gui/tab_poczta_imap.py
"""
import tkinter as tk
from tkinter import ttk

# Import the mail configuration widget
try:
    from gui.mail_config_widget import MailConfigWidget
    HAVE_MAIL_WIDGET = True
except ImportError as e:
    HAVE_MAIL_WIDGET = False
    IMPORT_ERROR = str(e)


class TabPocztaIMAP(ttk.Frame):
    """
    IMAP/POP3 mail tab with configuration
    
    Note: Search functionality is handled in the main application
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        if not HAVE_MAIL_WIDGET:
            # Show error message if widget couldn't be imported
            error_frame = ttk.Frame(self)
            error_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            error_label = ttk.Label(
                error_frame, 
                text=f"Nie można załadować widgetu konfiguracji poczty:\n{IMPORT_ERROR}\n\nSprawdź czy zainstalowano wymagane zależności.",
                justify="center",
                foreground="red"
            )
            error_label.pack(expand=True)
            return
        
        # Create the configuration widget directly
        self.config_widget = MailConfigWidget(self)
        self.config_widget.pack(fill="both", expand=True)
        
        # Callback for when configuration is saved
        self.config_widget.on_config_saved = self._on_config_changed
    
    def _on_config_changed(self):
        """Called when configuration is saved"""
        # Future: can refresh other tabs or notify parent
        pass
