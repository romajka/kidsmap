"""Private, actor-owned proposal working copies; never person authority."""
from uuid import uuid4
from django.conf import settings
from django.db import models
from .specialist import SpecialistDocument
from catalog.private_storage import specialist_private_storage, specialist_document_path


def proposal_photo_path(instance,filename):
    return f'specialist-proposal-photos/{uuid4().hex}.bin'


class SpecialistProposalDraft(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid4,editable=False)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='specialist_proposal_drafts')
    payload=models.JSONField(default=dict)
    version=models.PositiveIntegerField(default=1)
    photo=models.FileField(storage=specialist_private_storage,upload_to=proposal_photo_path,blank=True)
    photo_content_type=models.CharField(max_length=32,blank=True)
    submitted_specialist=models.ForeignKey('catalog.Specialist',null=True,blank=True,on_delete=models.SET_NULL,related_name='proposal_working_copies')
    submitted_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)


class SpecialistProposalDocument(models.Model):
    """Private working copy. Its author is the draft actor, never a claimed profile."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    draft = models.ForeignKey(SpecialistProposalDraft, on_delete=models.CASCADE, related_name='qualification_documents')
    name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=20, choices=SpecialistDocument.QUALIFICATION_TYPES)
    file = models.FileField(storage=specialist_private_storage, upload_to=specialist_document_path)
    publish = models.BooleanField(default=False)
    opted_in_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'pk']
