"""The published release manifest and evidence of explicit acceptance."""
import hashlib
import json
from dataclasses import dataclass

from django.core import signing
from django.db import transaction

from catalog.legal_content import get_legal_page_content

from .models import LegalAcceptance, LegalDocumentSnapshot
from .releases import RELEASES, Release
OFFER_SALT = "kidsmap.legalconsent.offer.v1"


@dataclass(frozen=True)
class OfferedDocument:
    slug: str
    language: str
    release: Release
    content: dict
    fingerprint: str

    @property
    def title(self):
        return self.content["legal_title"]

    @property
    def version(self):
        return self.release.version


@dataclass(frozen=True)
class Offer:
    language: str
    documents: tuple[OfferedDocument, ...]
    token: str


class StaleOffer(ValueError):
    """The posted documents or language no longer match the displayed offer."""


def published_document(slug, language):
    release = RELEASES[slug]
    content = get_legal_page_content(page_slug=slug, language=language)
    snapshot = [
        slug, language, release.version, release.generation,
        release.published_on.isoformat(), release.updated_on.isoformat(), content,
    ]
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return OfferedDocument(slug, language, release, content, fingerprint)


def offer(language):
    if language not in {"ru", "az", "en"}:
        raise StaleOffer()
    documents = tuple(published_document(slug, language) for slug in RELEASES)
    token = signing.dumps([doc.fingerprint for doc in documents], salt=OFFER_SALT)
    return Offer(language, documents, token)


def validate_offer(language, token, *, current=None):
    """Validate against the documents displayed in this locale. Never trust posted ids."""
    if not isinstance(token, str):
        raise StaleOffer()
    try:
        fingerprints = signing.loads(token, salt=OFFER_SALT)
    except signing.BadSignature as exc:
        raise StaleOffer() from exc
    current = current if current is not None else offer(language)
    if current.language != language or fingerprints != [doc.fingerprint for doc in current.documents]:
        raise StaleOffer()
    return current


@transaction.atomic
def accept(user, language, token):
    current = validate_offer(language, token)
    for doc in current.documents:
        snapshot, _ = LegalDocumentSnapshot.objects.get_or_create(
            fingerprint=doc.fingerprint,
            defaults={
                "slug": doc.slug,
                "version": doc.version,
                "language": language,
                "title": doc.title,
                "generation": doc.release.generation,
                "published_on": doc.release.published_on,
                "updated_on": doc.release.updated_on,
                "content": doc.content,
            },
        )
        LegalAcceptance.objects.get_or_create(user=user, document=snapshot)


def needs_reconsent(user):
    required = {slug: doc.generation for slug, doc in RELEASES.items() if doc.generation > 1}
    if not required or not user.is_authenticated:
        return False
    receipts = LegalAcceptance.objects.filter(user=user, document__slug__in=required).values_list(
        "document__slug", "document__generation",
    )
    confirmed = {slug for slug, generation in receipts if generation >= required[slug]}
    return confirmed != required.keys()
