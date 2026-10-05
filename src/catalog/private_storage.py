"""Private documents have no direct URL and never share public media storage."""
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class SpecialistPrivateStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(file_permissions_mode=0o600, directory_permissions_mode=0o700)

    @property
    def base_location(self):
        configured = getattr(settings, 'PRIVATE_MEDIA_ROOT', None)
        root = Path(configured or (Path(settings.MEDIA_ROOT).parent / 'private-media')).resolve()
        public = Path(settings.MEDIA_ROOT).resolve()
        if root == public or root.is_relative_to(public):
            raise ImproperlyConfigured('Private documents must be outside MEDIA_ROOT')
        return str(root)

    @property
    def location(self):
        return self.base_location

    def url(self, name):
        raise ValueError('Private documents are available only through an authorized download')


def specialist_document_path(instance, filename):
    # No original name/user label in filesystem paths. Download is attachment-only.
    return f'specialist-documents/{uuid4().hex}.bin'


specialist_private_storage = SpecialistPrivateStorage()
