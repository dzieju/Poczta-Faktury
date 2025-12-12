#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplikacja do wyszukiwania faktur w załącznikach email po numerze NIP
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import imaplib
import poplib
import email
from email.header import decode_header
import os
import re
import tempfile
from pathlib import Path
import PyPDF2
import pdfplumber


class EmailInvoiceFinderApp:
    """Główna aplikacja do wyszukiwania faktur"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Poczta Faktury - Wyszukiwanie faktur po NIP")
        self.root.geometry("800x600")
        
        # Konfiguracja email
        self.email_config = {
            'protocol': 'IMAP',
            'server': '',
            'port': '',
            'email': '',
            'password': '',
            'use_ssl': True
        }
        
        # Ustawienia wyszukiwania
        self.search_config = {
            'nip': '',
            'output_folder': ''
        }
        
        self.create_widgets()
    
    def create_widgets(self):
        """Tworzenie interfejsu użytkownika"""
        # Notebook (zakładki)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Zakładka 1: Konfiguracja email
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Konfiguracja poczty")
        self.create_email_config_tab()
        
        # Zakładka 2: Wyszukiwanie NIP
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="Wyszukiwanie NIP")
        self.create_search_tab()
    
    def create_email_config_tab(self):
        """Tworzenie zakładki konfiguracji email"""
        # Protokół
        protocol_frame = ttk.LabelFrame(self.config_frame, text="Protokół", padding=10)
        protocol_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        self.protocol_var = tk.StringVar(value='IMAP')
        ttk.Radiobutton(protocol_frame, text="IMAP", variable=self.protocol_var, 
                       value='IMAP').pack(side='left', padx=5)
        ttk.Radiobutton(protocol_frame, text="POP3", variable=self.protocol_var, 
                       value='POP3').pack(side='left', padx=5)
        ttk.Radiobutton(protocol_frame, text="Exchange (IMAP)", variable=self.protocol_var, 
                       value='EXCHANGE').pack(side='left', padx=5)
        
        # Serwer
        ttk.Label(self.config_frame, text="Serwer:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.server_entry = ttk.Entry(self.config_frame, width=40)
        self.server_entry.grid(row=1, column=1, sticky='ew', padx=10, pady=5)
        
        # Port
        ttk.Label(self.config_frame, text="Port:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.port_entry = ttk.Entry(self.config_frame, width=40)
        self.port_entry.grid(row=2, column=1, sticky='ew', padx=10, pady=5)
        self.port_entry.insert(0, "993")  # Domyślny port IMAP SSL
        
        # Email
        ttk.Label(self.config_frame, text="Email:").grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.email_entry = ttk.Entry(self.config_frame, width=40)
        self.email_entry.grid(row=3, column=1, sticky='ew', padx=10, pady=5)
        
        # Hasło
        ttk.Label(self.config_frame, text="Hasło:").grid(row=4, column=0, sticky='w', padx=10, pady=5)
        self.password_entry = ttk.Entry(self.config_frame, width=40, show='*')
        self.password_entry.grid(row=4, column=1, sticky='ew', padx=10, pady=5)
        
        # SSL
        self.ssl_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.config_frame, text="Użyj SSL/TLS", 
                       variable=self.ssl_var).grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        
        # Przycisk testowania połączenia
        ttk.Button(self.config_frame, text="Testuj połączenie", 
                  command=self.test_connection).grid(row=6, column=0, columnspan=2, pady=20)
        
        # Status
        self.status_label = ttk.Label(self.config_frame, text="", foreground="blue")
        self.status_label.grid(row=7, column=0, columnspan=2, padx=10, pady=5)
        
        self.config_frame.columnconfigure(1, weight=1)
    
    def create_search_tab(self):
        """Tworzenie zakładki wyszukiwania"""
        # NIP
        ttk.Label(self.search_frame, text="Numer NIP:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.nip_entry = ttk.Entry(self.search_frame, width=40)
        self.nip_entry.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
        
        # Folder wyjściowy
        ttk.Label(self.search_frame, text="Folder zapisu:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        
        folder_frame = ttk.Frame(self.search_frame)
        folder_frame.grid(row=1, column=1, sticky='ew', padx=10, pady=5)
        
        self.folder_entry = ttk.Entry(folder_frame, width=30)
        self.folder_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(folder_frame, text="Przeglądaj...", 
                  command=self.browse_folder).pack(side='left', padx=5)
        
        # Przycisk wyszukiwania
        ttk.Button(self.search_frame, text="Szukaj faktur", 
                  command=self.search_invoices).grid(row=2, column=0, columnspan=2, pady=20)
        
        # Pasek postępu
        self.progress = ttk.Progressbar(self.search_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=5)
        
        # Wyniki
        ttk.Label(self.search_frame, text="Wyniki:").grid(row=4, column=0, columnspan=2, sticky='w', padx=10, pady=5)
        
        self.results_text = scrolledtext.ScrolledText(self.search_frame, height=20, width=70)
        self.results_text.grid(row=5, column=0, columnspan=2, sticky='nsew', padx=10, pady=5)
        
        self.search_frame.columnconfigure(1, weight=1)
        self.search_frame.rowconfigure(5, weight=1)
    
    def test_connection(self):
        """Testowanie połączenia z serwerem email"""
        protocol = self.protocol_var.get()
        server = self.server_entry.get()
        port = self.port_entry.get()
        email_addr = self.email_entry.get()
        password = self.password_entry.get()
        use_ssl = self.ssl_var.get()
        
        if not all([server, port, email_addr, password]):
            messagebox.showerror("Błąd", "Proszę wypełnić wszystkie pola")
            return
        
        try:
            port = int(port)
        except ValueError:
            messagebox.showerror("Błąd", "Port musi być liczbą")
            return
        
        self.status_label.config(text="Łączenie...", foreground="blue")
        self.root.update()
        
        try:
            if protocol == 'POP3':
                if use_ssl:
                    mail = poplib.POP3_SSL(server, port)
                else:
                    mail = poplib.POP3(server, port)
                mail.user(email_addr)
                mail.pass_(password)
                mail.quit()
            else:  # IMAP lub EXCHANGE
                if use_ssl:
                    mail = imaplib.IMAP4_SSL(server, port)
                else:
                    mail = imaplib.IMAP4(server, port)
                mail.login(email_addr, password)
                mail.logout()
            
            self.status_label.config(text="Połączenie udane!", foreground="green")
            messagebox.showinfo("Sukces", "Połączenie z serwerem poczty powiodło się!")
            
            # Zapisz konfigurację
            self.email_config = {
                'protocol': protocol,
                'server': server,
                'port': port,
                'email': email_addr,
                'password': password,
                'use_ssl': use_ssl
            }
            
        except Exception as e:
            self.status_label.config(text="Błąd połączenia", foreground="red")
            messagebox.showerror("Błąd", f"Nie udało się połączyć z serwerem:\n{str(e)}")
    
    def browse_folder(self):
        """Wybór folderu do zapisu"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
    
    def extract_text_from_pdf(self, pdf_path):
        """Ekstrakcja tekstu z pliku PDF"""
        text = ""
        
        # Próba z pdfplumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Błąd pdfplumber: {e}")
        
        # Jeśli pdfplumber nie zadziałał, spróbuj PyPDF2
        if not text:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"Błąd PyPDF2: {e}")
        
        return text
    
    def search_nip_in_text(self, text, nip):
        """Wyszukiwanie numeru NIP w tekście"""
        # Usuń wszystkie znaki niealfanumeryczne z NIP
        clean_nip = re.sub(r'[^0-9]', '', nip)
        
        # Usuń białe znaki z tekstu dla lepszego dopasowania
        clean_text = re.sub(r'\s+', '', text)
        
        # Szukaj NIP jako ciągłej liczby
        if clean_nip in clean_text:
            return True
        
        # Alternatywnie szukaj z możliwymi separatorami
        nip_patterns = [
            clean_nip,
            '-'.join([clean_nip[:3], clean_nip[3:6], clean_nip[6:8], clean_nip[8:]]),
            '-'.join([clean_nip[:3], clean_nip[3:]]),
        ]
        
        for pattern in nip_patterns:
            if pattern in text:
                return True
        
        return False
    
    def search_invoices(self):
        """Główna funkcja wyszukiwania faktur"""
        nip = self.nip_entry.get().strip()
        output_folder = self.folder_entry.get().strip()
        
        if not nip:
            messagebox.showerror("Błąd", "Proszę podać numer NIP")
            return
        
        if not output_folder:
            messagebox.showerror("Błąd", "Proszę wybrać folder zapisu")
            return
        
        if not os.path.exists(output_folder):
            messagebox.showerror("Błąd", "Wybrany folder nie istnieje")
            return
        
        if not self.email_config.get('server'):
            messagebox.showerror("Błąd", "Proszę najpierw skonfigurować połączenie email")
            self.notebook.select(0)  # Przełącz na zakładkę konfiguracji
            return
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Rozpoczynam wyszukiwanie...\n")
        self.progress.start()
        self.root.update()
        
        try:
            found_count = 0
            processed_count = 0
            
            # Połącz z serwerem email
            protocol = self.email_config['protocol']
            
            if protocol == 'POP3':
                found_count = self.search_with_pop3(nip, output_folder)
            else:  # IMAP lub EXCHANGE
                found_count = self.search_with_imap(nip, output_folder)
            
            self.progress.stop()
            self.results_text.insert(tk.END, f"\n=== Zakończono wyszukiwanie ===\n")
            self.results_text.insert(tk.END, f"Znaleziono faktur z NIP {nip}: {found_count}\n")
            
            if found_count > 0:
                messagebox.showinfo("Sukces", f"Znaleziono {found_count} faktur(y) z podanym NIP.\nPliki zapisano w: {output_folder}")
            else:
                messagebox.showinfo("Informacja", "Nie znaleziono faktur z podanym NIP")
            
        except Exception as e:
            self.progress.stop()
            self.results_text.insert(tk.END, f"\nBŁĄD: {str(e)}\n")
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas wyszukiwania:\n{str(e)}")
    
    def search_with_imap(self, nip, output_folder):
        """Wyszukiwanie przez IMAP"""
        found_count = 0
        
        # Połącz z serwerem
        if self.email_config['use_ssl']:
            mail = imaplib.IMAP4_SSL(self.email_config['server'], self.email_config['port'])
        else:
            mail = imaplib.IMAP4(self.email_config['server'], self.email_config['port'])
        
        mail.login(self.email_config['email'], self.email_config['password'])
        
        self.results_text.insert(tk.END, "Połączono z serwerem IMAP\n")
        self.root.update()
        
        # Wybierz skrzynkę INBOX
        mail.select('INBOX')
        
        # Wyszukaj wszystkie wiadomości
        status, messages = mail.search(None, 'ALL')
        
        if status != 'OK':
            raise Exception("Nie można pobrać listy wiadomości")
        
        message_ids = messages[0].split()
        total_messages = len(message_ids)
        
        self.results_text.insert(tk.END, f"Znaleziono {total_messages} wiadomości do przeszukania\n")
        self.root.update()
        
        # Przeszukaj wiadomości
        for i, msg_id in enumerate(message_ids, 1):
            if i % 10 == 0:
                self.results_text.insert(tk.END, f"Przetworzono {i}/{total_messages} wiadomości...\n")
                self.root.update()
            
            try:
                status, msg_data = mail.fetch(msg_id, '(RFC822)')
                
                if status != 'OK':
                    continue
                
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Pobierz temat
                subject = self.decode_email_subject(email_message.get('Subject', ''))
                
                # Sprawdź załączniki
                for part in email_message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    
                    if part.get('Content-Disposition') is None:
                        continue
                    
                    filename = part.get_filename()
                    
                    if filename and filename.lower().endswith('.pdf'):
                        filename = self.decode_email_subject(filename)
                        
                        # Zapisz tymczasowo PDF
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(part.get_payload(decode=True))
                            tmp_path = tmp_file.name
                        
                        try:
                            # Ekstrakcja tekstu z PDF
                            pdf_text = self.extract_text_from_pdf(tmp_path)
                            
                            # Sprawdź czy zawiera NIP
                            if self.search_nip_in_text(pdf_text, nip):
                                found_count += 1
                                
                                # Zapisz plik
                                safe_filename = self.make_safe_filename(filename)
                                output_path = os.path.join(output_folder, f"{found_count}_{safe_filename}")
                                
                                with open(output_path, 'wb') as f:
                                    f.write(part.get_payload(decode=True))
                                
                                self.results_text.insert(tk.END, f"✓ Znaleziono: {filename} (z: {subject})\n")
                                self.root.update()
                        
                        finally:
                            # Usuń plik tymczasowy
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass
            
            except Exception as e:
                print(f"Błąd przetwarzania wiadomości {msg_id}: {e}")
                continue
        
        mail.close()
        mail.logout()
        
        return found_count
    
    def search_with_pop3(self, nip, output_folder):
        """Wyszukiwanie przez POP3"""
        found_count = 0
        
        # Połącz z serwerem
        if self.email_config['use_ssl']:
            mail = poplib.POP3_SSL(self.email_config['server'], self.email_config['port'])
        else:
            mail = poplib.POP3(self.email_config['server'], self.email_config['port'])
        
        mail.user(self.email_config['email'])
        mail.pass_(self.email_config['password'])
        
        self.results_text.insert(tk.END, "Połączono z serwerem POP3\n")
        self.root.update()
        
        # Pobierz listę wiadomości
        num_messages = len(mail.list()[1])
        
        self.results_text.insert(tk.END, f"Znaleziono {num_messages} wiadomości do przeszukania\n")
        self.root.update()
        
        # Przeszukaj wiadomości
        for i in range(1, num_messages + 1):
            if i % 10 == 0:
                self.results_text.insert(tk.END, f"Przetworzono {i}/{num_messages} wiadomości...\n")
                self.root.update()
            
            try:
                response, lines, octets = mail.retr(i)
                email_body = b'\n'.join(lines)
                email_message = email.message_from_bytes(email_body)
                
                # Pobierz temat
                subject = self.decode_email_subject(email_message.get('Subject', ''))
                
                # Sprawdź załączniki
                for part in email_message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    
                    if part.get('Content-Disposition') is None:
                        continue
                    
                    filename = part.get_filename()
                    
                    if filename and filename.lower().endswith('.pdf'):
                        filename = self.decode_email_subject(filename)
                        
                        # Zapisz tymczasowo PDF
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(part.get_payload(decode=True))
                            tmp_path = tmp_file.name
                        
                        try:
                            # Ekstrakcja tekstu z PDF
                            pdf_text = self.extract_text_from_pdf(tmp_path)
                            
                            # Sprawdź czy zawiera NIP
                            if self.search_nip_in_text(pdf_text, nip):
                                found_count += 1
                                
                                # Zapisz plik
                                safe_filename = self.make_safe_filename(filename)
                                output_path = os.path.join(output_folder, f"{found_count}_{safe_filename}")
                                
                                with open(output_path, 'wb') as f:
                                    f.write(part.get_payload(decode=True))
                                
                                self.results_text.insert(tk.END, f"✓ Znaleziono: {filename} (z: {subject})\n")
                                self.root.update()
                        
                        finally:
                            # Usuń plik tymczasowy
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass
            
            except Exception as e:
                print(f"Błąd przetwarzania wiadomości {i}: {e}")
                continue
        
        mail.quit()
        
        return found_count
    
    def decode_email_subject(self, subject):
        """Dekodowanie tematu email"""
        if not subject:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(subject):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8'))
                except:
                    decoded_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                decoded_parts.append(str(part))
        
        return ''.join(decoded_parts)
    
    def make_safe_filename(self, filename):
        """Tworzenie bezpiecznej nazwy pliku"""
        # Usuń niebezpieczne znaki
        safe_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'
        safe_filename = ''.join(c for c in filename if c in safe_chars)
        
        # Ogranicz długość
        if len(safe_filename) > 200:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:196] + ext
        
        return safe_filename if safe_filename else 'faktura.pdf'


def main():
    """Uruchomienie aplikacji"""
    root = tk.Tk()
    app = EmailInvoiceFinderApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
