"""Genuine fictional documents for upload/ACL regression fixtures."""
from io import BytesIO
from PIL import Image


def image_document_bytes(format='PNG'):
    stream = BytesIO()
    Image.new('RGB', (32, 24), '#26754b').save(stream, format=format)
    return stream.getvalue()


def pdf_document_bytes(*, encrypted=False):
    from pypdf import PdfWriter
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=210, height=297)
    if encrypted:
        writer.encrypt('fictional-password')
    writer.write(stream)
    return stream.getvalue()
