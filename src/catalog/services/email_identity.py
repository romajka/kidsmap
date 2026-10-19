"""Current mailbox identity for email-address-scoped privileges.

Rows without any proof are existing legacy accounts: keep their unchanged
address usable, but never manufacture proof. Where proof exists it must match
the current address; historical profile edits cannot borrow an old verification.
User.email is written by the staged change service only after mailbox proof.
"""
from django.contrib.auth import get_user_model


def normalize_email(value):
    return (value or '').strip().lower()


def current_email_for_privileges(user):
    from allauth.account.models import EmailAddress
    from catalog.models import UserEmailVerification

    if not getattr(user, 'is_authenticated', False) or not getattr(user, 'pk', None):
        return ''
    current = get_user_model().objects.filter(pk=user.pk, is_active=True).values_list('email', flat=True).first()
    email = normalize_email(current)
    if not email:
        return ''
    proof = UserEmailVerification.objects.filter(user_id=user.pk).first()
    if proof is not None and (not proof.is_verified or normalize_email(proof.email) != email):
        return ''
    addresses = EmailAddress.objects.filter(user_id=user.pk)
    if addresses.exists() and not addresses.filter(email__iexact=email, verified=True).exists():
        return ''
    return email
