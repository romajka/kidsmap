"""Private, actor-owned proposal working copies; never person authority."""
from uuid import uuid4
from django.conf import settings
from django.db import models
from catalog.private_storage import specialist_private_storage


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
