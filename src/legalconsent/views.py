from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from catalog.services.auth_redirects import resolve_safe_next_url
from .forms import ConsentForm, STALE_MESSAGE
from .services import StaleOffer, accept, needs_reconsent, offer


def consent_form(request, language):
    form = ConsentForm(request.POST if request.method == "POST" else None, language=language)
    return form, form.legal_offer


def reject_stale_offer(form, language):
    form.clear_agreement()
    form.add_error("agreement", STALE_MESSAGE[language])
    form.legal_offer = offer(language)


def render_consent(request, form, legal_offer, *, purpose, next_url):
    if form.is_bound and "agreement" in form.errors:
        form.fields["agreement"].widget.attrs["autofocus"] = True
    return render(request, "auth/legal_consent.html", {
        "form": form, "legal_offer": legal_offer, "consent_purpose": purpose,
        "next_url": next_url,
    })


@never_cache
@login_required(login_url="account_login")
@require_http_methods(["GET", "POST"])
def renew_consent(request):
    next_url = resolve_safe_next_url(request, reverse("account_profile"))
    if not needs_reconsent(request.user):
        return redirect(next_url)
    form, current = consent_form(request, request.LANGUAGE_CODE)
    if form.is_bound and form.is_valid():
        try:
            accept(request.user, form.consent_language, form.data["legal_offer"])
        except StaleOffer:
            reject_stale_offer(form, form.consent_language)
            current = form.legal_offer
        else:
            return redirect(next_url)
    return render_consent(request, form, current, purpose="renew", next_url=next_url)
