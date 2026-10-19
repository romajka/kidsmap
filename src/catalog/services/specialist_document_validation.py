"""Bounded structural validation of documents before private storage writes."""
import os
from pathlib import Path
import subprocess
import sys

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_document_upload(uploaded_file):
    """Preserve original bytes and rewind the stream for subsequent storage."""
    invalid = _("Документ повреждён или его содержимое не соответствует формату. Выберите исправный PDF, PNG или JPEG.")
    unavailable = _("Не удалось безопасно проверить документ. Выберите файл меньшего размера или разрешения.")
    try:
        uploaded_file.seek(0)
        data = uploaded_file.read(10 * 1024 * 1024 + 1)
        if not data or len(data) > 10 * 1024 * 1024:
            raise ValidationError(invalid, code='invalid_document')
        suffix = Path(uploaded_file.name).suffix.lower()
        try:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name('specialist_document_probe.py')), suffix],
                input=data, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=5, check=False,
                env={'PATH': os.defpath, 'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1'},
            )
        except (OSError, subprocess.TimeoutExpired):
            raise ValidationError(unavailable, code='invalid_document') from None
        if result.returncode != 0 or result.stdout != b'valid\n':
            message = (_("PDF защищён паролем. Загрузите документ без пароля.")
                       if result.stdout == b'encrypted\n' else
                       unavailable if result.stdout == b'unavailable\n' or result.returncode != 0 else invalid)
            raise ValidationError(message, code='invalid_document')
    finally:
        uploaded_file.seek(0)
