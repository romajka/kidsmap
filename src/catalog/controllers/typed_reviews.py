"""Public, author, business and KidsMap reviewer flows share typed services."""
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import get_language
from django.views.decorators.http import require_http_methods, require_POST
from catalog.services.permanent_place_rules import copy as t
from catalog.services.review_versions import (review_types, submit_review, moderate_candidate, business_can_respond, respond_to_review, rating_summary, ReviewConflict, ReviewCooldown)
from catalog.services.content_quality import approved_review_queryset
from catalog.services.public_presentation import present


def _types(kind):
    types = review_types().get(kind)
    if not types:
        raise Http404
    return types


def _target(kind, pk, request):
    types = _types(kind)
    target = get_object_or_404(types[0], pk=pk)
    if kind in {'place', 'activity'}:
        visible = present(target, getattr(request, 'LANGUAGE_CODE', 'az'))['visible']
    elif kind == 'specialist':
        from catalog.services.features import is_specialists_section_enabled
        visible = is_specialists_section_enabled() and target.is_active and target.status == 'published'
    else:
        from catalog.services.features import is_events_section_enabled
        visible = is_events_section_enabled() and target.is_public
    if not visible and request.user.is_authenticated and request.user.is_active and request.user.is_staff:
        visible = request.user.has_perm('catalog.change_' + types[1]._meta.model_name)
    if not visible:
        raise Http404
    return target


@require_http_methods(['GET', 'POST'])
def target_reviews(request, kind, pk):
    target = _target(kind, pk, request)
    _, heads, _, _ = _types(kind)
    url = reverse('typed_reviews', args=[kind, pk])
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        from catalog.services.review_use_cases import _build_review_payload
        from catalog.services.review_moderation import moderate_review_content
        payload, error = _build_review_payload(request, require_text=True, use_account_author=True)
        if error:
            return HttpResponse(error, status=400)
        content = moderate_review_content(author_name=payload.author_name, text=payload.text)
        try:
            if kind == 'place':
                from catalog.services.place_review_submission import create_pending_place_review
                head, cooldown = create_pending_place_review(user=request.user, place=target, rating=payload.rating, text=content.text, author_name=content.author_name, contains_profanity=content.contains_profanity, expected_revision_id=request.POST.get('expected_revision_id') or None)
                if head is None:
                    response = JsonResponse({'ok': False, 'cooldown': cooldown}, status=429)
                    response['Retry-After'] = str(cooldown['retry_after'])
                    return response
            else:
                submit_review(target=target, user=request.user, rating=payload.rating, text=content.text,
                    author_name=content.author_name, contains_profanity=content.contains_profanity,
                    expected_revision_id=request.POST.get('expected_revision_id') or None, enforce_cooldown=kind != 'specialist')
        except ReviewConflict:
            return HttpResponse(t('Отзыв изменился. Обновите страницу.', 'Rəy dəyişib. Səhifəni yeniləyin.', 'The review changed. Reload the page.'), status=409)
        except ValidationError:
            return HttpResponse(status=400)
        except PermissionError:
            return HttpResponseForbidden()
        except ReviewCooldown as exc:
            from catalog.services.place_review_submission import cooldown_payload
            response = JsonResponse({'ok': False, 'cooldown': cooldown_payload(exc.next_allowed_at)}, status=429)
            response['Retry-After'] = str(cooldown_payload(exc.next_allowed_at)['retry_after'])
            return response
        from catalog.services.moderation_sla import submission_message
        messages.success(request, submission_message('review'))
        return redirect(url)
    reviews = list(approved_review_queryset(heads.objects.filter(**{kind: target})).select_related('current_revision').order_by('-moderated_at', '-pk'))
    from catalog.services.reactions import _mark_review_reactions
    reviews = _mark_review_reactions(reviews, request, reaction_model=_types(kind)[3])
    for head in reviews:
        head.can_reply = request.user.is_authenticated and business_can_respond(user=request.user, head=head)
        head.can_report = request.user.is_authenticated and business_can_respond(user=request.user, head=head, action='report')
        head.public_replies = head.current_revision.responses.filter(kind='reply') if head.current_revision_id else []
    own = heads.objects.filter(**{kind: target, 'user': request.user, 'is_current': True}).select_related('candidate_revision', 'current_revision').first() if request.user.is_authenticated else None
    can_review = request.user.is_active and request.user.is_staff and request.user.has_perm('catalog.change_' + heads._meta.model_name)
    candidates = list(heads.objects.filter(**{kind: target, 'is_current': True, 'candidate_revision__status': 'pending'}).select_related('candidate_revision')) if can_review else []
    return render(request, 'catalog/typed_reviews.html', {'kind': kind, 'target': target, 'target_name': getattr(target, 'name_i18n', None) or str(target), 'language': getattr(request, 'LANGUAGE_CODE', get_language()), 'reviews': reviews, 'own_review': own, 'candidates': candidates, 'review_rating': rating_summary(target)})


@require_POST
def review_action(request, kind, pk, action):
    _, heads, _, reactions = _types(kind)
    head = get_object_or_404(heads, pk=pk)
    target = _target(kind, getattr(head, kind + '_id'), request)
    if not request.user.is_authenticated or not request.user.is_active:
        return HttpResponseForbidden()
    revision_id = request.POST.get('revision_id')
    if not revision_id or len(revision_id) > 32 or not revision_id.isascii() or not revision_id.isdecimal() or int(revision_id) <= 0:
        return HttpResponse(status=400)
    try:
        if action in {'approve', 'reject'}:
            moderate_candidate(head=head, revision_id=int(revision_id), actor=request.user, approve=action == 'approve', reason=request.POST.get('reason', '')[:5000])
        elif action in {'reply', 'report'}:
            respond_to_review(head=head, actor=request.user, revision_id=revision_id, kind=action, text=request.POST.get('text', ''))
        elif action == 'react':
            if head.user_id == request.user.pk:
                return HttpResponseForbidden()
            from catalog.services.reactions import _toggle_review_reaction
            if request.POST.get('value') not in {'1', '-1'}:
                return HttpResponse(status=400)
            _toggle_review_reaction(review=head, request=request, value=int(request.POST['value']), reaction_model=reactions)
        else:
            raise Http404
    except PermissionError:
        return HttpResponseForbidden()
    except ReviewConflict:
        return HttpResponse(status=409)
    except ValidationError:
        return HttpResponse(status=400)
    return redirect('typed_reviews', kind=kind, pk=target.pk)
