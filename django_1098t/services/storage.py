# django_1098t/services/storage.py

from django.core.files.base import ContentFile
from cis.backends.storage_backend import PrivateMediaStorage
from django_1098t.constants import STORAGE_PATH_PREFIX
import datetime


class Form1098TStorage:
    """Handles S3 storage operations for 1098-T forms."""
    
    def __init__(self):
        self.storage = PrivateMediaStorage()
    
    def save_form(self, pdf_bytes: bytes, student_id: int, tax_year: int) -> tuple:
        """
        Save a PDF form to S3 storage.
        
        Args:
            pdf_bytes: PDF file content as bytes
            student_id: Student ID
            tax_year: Tax year
            
        Returns:
            Tuple of (file_path, file_size)
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = (
            f"{STORAGE_PATH_PREFIX}{tax_year}/"
            f"student_{student_id}_1098t_{tax_year}_{timestamp}.pdf"
        )
        
        self.storage.save(file_path, ContentFile(pdf_bytes))
        file_size = len(pdf_bytes)
        
        return file_path, file_size
    
    def delete_form(self, file_path: str):
        """Delete a form from S3 storage."""
        if self.storage.exists(file_path):
            self.storage.delete(file_path)
    
    def get_file_content(self, file_path: str) -> bytes:
        """Retrieve file content from S3."""
        with self.storage.open(file_path, 'rb') as f:
            return f.read()
    
    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in S3."""
        return self.storage.exists(file_path)