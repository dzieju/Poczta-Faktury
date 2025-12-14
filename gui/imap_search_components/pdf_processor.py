"""
PDF text extraction and search functionality for mail search

Source: Copied and adapted from dzieju-app2 repository
Original file: https://github.com/dzieju/dzieju-app2/blob/fcee6b91bf240d17ceb38f8564beab5aa9637437/gui/imap_search_components/pdf_processor.py
"""
import io
import os
import re
import tempfile
import sys

# Import logger from our local gui module
try:
    from gui.logger import log
except ImportError:
    # Fallback if running standalone
    def log(message, level="INFO"):
        print(f"[{level}] {message}", flush=True)

# Try to import OCR dependencies
try:
    import pytesseract
    from pdf2image import convert_from_bytes
    HAVE_OCR = True
    log("PDF OCR dependencies available")
except ImportError as e:
    HAVE_OCR = False
    log(f"PDF OCR dependencies not available: {e}")

try:
    import pdfplumber
    HAVE_PDFPLUMBER = True
    log("pdfplumber available for text extraction")
except ImportError as e:
    HAVE_PDFPLUMBER = False
    log(f"pdfplumber not available: {e}")


class PDFProcessor:
    """Handles PDF text extraction and search operations"""
    
    def __init__(self):
        self.search_cancelled = False
    
    def cancel_search(self):
        """Cancel ongoing PDF processing"""
        self.search_cancelled = True
    
    def search_in_pdf_attachment(self, attachment, search_text, attachment_name=""):
        """
        Search for text in a PDF attachment
        
        Args:
            attachment: Email attachment object with content (bytes or object with 'content' attribute)
            search_text: Text to search for (case-insensitive)
            attachment_name: Name of the attachment for logging
            
        Returns:
            dict: {
                'found': bool,
                'matches': list of found text snippets,
                'method': 'text_extraction' or 'ocr'
            }
        """
        if self.search_cancelled:
            return {'found': False, 'matches': [], 'method': 'cancelled'}
        
        # Handle different attachment formats
        pdf_content = None
        if isinstance(attachment, bytes):
            pdf_content = attachment
        elif hasattr(attachment, 'content'):
            pdf_content = attachment.content
        elif hasattr(attachment, 'get_payload'):
            # Email attachment from standard library
            pdf_content = attachment.get_payload(decode=True)
        
        if not pdf_content:
            return {'found': False, 'matches': [], 'method': 'no_content'}
        
        # Check if PDF processing is available
        if not HAVE_PDFPLUMBER and not HAVE_OCR:
            log("PDF search not available: missing dependencies (pdfplumber, pytesseract)")
            return {'found': False, 'matches': [], 'method': 'missing_dependencies'}
        
        search_text_lower = search_text.lower().strip()
        if not search_text_lower:
            return {'found': False, 'matches': [], 'method': 'empty_search'}
        
        log(f"Wyszukiwanie '{search_text}' w załączniku PDF: {attachment_name}")
        
        try:
            # First try text extraction (faster) if available
            if HAVE_PDFPLUMBER:
                result = self._search_with_text_extraction(pdf_content, search_text_lower, attachment_name)
                if result['found']:
                    return result
            
            # If text extraction fails or finds nothing, try OCR if available
            if HAVE_OCR and not self.search_cancelled:
                result = self._search_with_ocr(pdf_content, search_text_lower, attachment_name)
                return result
                
        except Exception as e:
            log(f"Error searching PDF {attachment_name}: {str(e)}")
            return {'found': False, 'matches': [], 'method': 'error', 'error': str(e)}
        
        return {'found': False, 'matches': [], 'method': 'not_found'}
    
    def _search_with_text_extraction(self, pdf_content, search_text_lower, attachment_name):
        """Try to extract text directly from PDF and search"""
        if not HAVE_PDFPLUMBER:
            return {'found': False, 'matches': [], 'method': 'pdfplumber_not_available'}
            
        try:
            log(f"Próba ekstrakcji tekstu z PDF: {attachment_name}")
            
            # Use pdfplumber to extract text
            with io.BytesIO(pdf_content) as pdf_stream:
                with pdfplumber.open(pdf_stream) as pdf:
                    all_text = ""
                    for page_num, page in enumerate(pdf.pages):
                        if self.search_cancelled:
                            break
                        
                        page_text = page.extract_text()
                        if page_text:
                            all_text += page_text + "\n"
                    
                    if all_text.strip():
                        # Search for the text (case-insensitive)
                        all_text_lower = all_text.lower()
                        if search_text_lower in all_text_lower:
                            matches = self._extract_matches(all_text, search_text_lower)
                            log(f"Tekst znaleziony w PDF {attachment_name} przez ekstrakcję tekstu (dokładne dopasowanie)")
                            return {'found': True, 'matches': matches, 'method': 'text_extraction'}
                        else:
                            # Try normalized search if exact match not found
                            log(f"Dokładne dopasowanie nie znalezione, próba znormalizowanego wyszukiwania...")
                            matches = self._extract_matches(all_text, search_text_lower)
                            if matches:
                                log(f"Tekst znaleziony w PDF {attachment_name} przez ekstrakcję tekstu (dopasowanie przybliżone)")
                                return {'found': True, 'matches': matches, 'method': 'text_extraction_normalized'}
                            else:
                                log(f"Tekst nie znaleziony w PDF {attachment_name} przez ekstrakcję tekstu")
                    else:
                        log(f"Brak tekstu do ekstrakcji z PDF {attachment_name}")
                        
        except Exception as e:
            log(f"Error during text extraction from {attachment_name}: {str(e)}")
        
        return {'found': False, 'matches': [], 'method': 'text_extraction_failed'}
    
    def _search_with_ocr(self, pdf_content, search_text_lower, attachment_name):
        """Use OCR to extract text from PDF and search"""
        if not HAVE_OCR:
            return {'found': False, 'matches': [], 'method': 'ocr_not_available'}
            
        try:
            log(f"Próba OCR z PDF: {attachment_name}")
            
            # Try to detect poppler path (Windows-specific, but won't break on Linux)
            poppler_path = None
            if sys.platform == 'win32':
                possible_paths = [
                    r"C:\poppler\Library\bin",
                    r"C:\Program Files\poppler\Library\bin",
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        poppler_path = path
                        break
            
            # Convert PDF to images
            if poppler_path:
                images = convert_from_bytes(pdf_content, dpi=200, poppler_path=poppler_path)
            else:
                images = convert_from_bytes(pdf_content, dpi=200)
            
            all_ocr_text = ""
            
            # Single-threaded OCR processing
            for page_num, image in enumerate(images):
                if self.search_cancelled:
                    break
                
                log(f"OCR strona {page_num + 1}/{len(images)} z PDF {attachment_name}")
                
                # Perform OCR - try Polish and English
                try:
                    page_text = pytesseract.image_to_string(image, lang='pol+eng')
                except Exception as e:
                    # Fallback to English only if Polish not available
                    log(f"Fallback to English OCR: {e}")
                    page_text = pytesseract.image_to_string(image, lang='eng')
                
                if page_text:
                    all_ocr_text += page_text + "\n"
            
            if all_ocr_text.strip():
                # Search for the text (case-insensitive)
                all_ocr_text_lower = all_ocr_text.lower()
                if search_text_lower in all_ocr_text_lower:
                    matches = self._extract_matches(all_ocr_text, search_text_lower)
                    log(f"Tekst znaleziony w PDF {attachment_name} przez OCR (dokładne dopasowanie)")
                    return {'found': True, 'matches': matches, 'method': 'ocr'}
                else:
                    # Try normalized search if exact match not found
                    log(f"Dokładne dopasowanie OCR nie znalezione, próba znormalizowanego wyszukiwania...")
                    matches = self._extract_matches(all_ocr_text, search_text_lower)
                    if matches:
                        log(f"Tekst znaleziony w PDF {attachment_name} przez OCR (dopasowanie przybliżone)")
                        return {'found': True, 'matches': matches, 'method': 'ocr_normalized'}
                    else:
                        log(f"Tekst nie znaleziony w PDF {attachment_name} przez OCR")
            else:
                log(f"Brak tekstu z OCR z PDF {attachment_name}")
                
        except Exception as e:
            log(f"Error during OCR from {attachment_name}: {str(e)}")
        
        return {'found': False, 'matches': [], 'method': 'ocr_failed'}
    
    def _extract_matches(self, full_text, search_text_lower):
        """
        Extract text snippets around matches
        
        This method performs both exact matching and normalized matching
        (removing spaces, dashes, etc.) to handle various formatting styles.
        
        Args:
            full_text: Full text to search in
            search_text_lower: Lowercase search text
            
        Returns:
            List of text snippets with context around matches (max 5)
        """
        matches = []
        full_text_lower = full_text.lower()
        
        # Find all occurrences - try both exact match and normalized match
        start = 0
        while True:
            pos = full_text_lower.find(search_text_lower, start)
            if pos == -1:
                break
            
            # Extract context around the match (50 chars before and after)
            context_start = max(0, pos - 50)
            context_end = min(len(full_text), pos + len(search_text_lower) + 50)
            
            context = full_text[context_start:context_end].strip()
            if context not in matches:  # Avoid duplicates
                matches.append(context)
            
            start = pos + 1
        
        # If no exact matches found, try normalized search (remove spaces, special chars)
        if not matches and len(search_text_lower) > 3:  # Only for longer search terms
            normalized_search = re.sub(r'[\s\-_./\\]+', '', search_text_lower)
            normalized_text = re.sub(r'[\s\-_./\\]+', '', full_text_lower)
            
            start = 0
            while True:
                pos = normalized_text.find(normalized_search, start)
                if pos == -1:
                    break
                
                # Try to find approximate position in original text
                # This is a rough approximation - count chars before position
                chars_before = pos
                approx_pos = 0
                char_count = 0
                for i, char in enumerate(full_text):
                    if not re.match(r'[\s\-_./\\]', char.lower()):
                        char_count += 1
                    if char_count >= chars_before:
                        approx_pos = i
                        break
                
                # Extract context around approximate match
                context_start = max(0, approx_pos - 50)
                context_end = min(len(full_text), approx_pos + len(search_text_lower) + 100)
                
                context = full_text[context_start:context_end].strip()
                if context not in matches:
                    matches.append(f"[Dopasowanie przybliżone] {context}")
                
                start = pos + 1
                
                if len(matches) >= 3:  # Limit normalized matches
                    break
        
        return matches[:5]  # Limit to 5 matches to avoid too much data
