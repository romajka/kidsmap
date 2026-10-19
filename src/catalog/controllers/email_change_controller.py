"""Session-bound email confirmation. All mutations require POST and CSRF."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from catalog.services.email_change import (
    EmailChangeError, cancel_email_change, confirm_email_change, copy,
    pending_for, resend_email_change,
)


@login_required(login_url='account_login')
@require_http_methods(['GET', 'POST'])
def email_change(request):
    error = None
    if request.method == 'POST':
        action = request.POST.get('form_action', '')
        token = request.POST.get('challenge_token', '')
        try:
            if action == 'verify':
                result = confirm_email_change(actor=request.user, token=token, code=request.POST.get('code', ''))
            elif action == 'cancel':
                result = cancel_email_change(actor=request.user, token=token)
            elif action == 'resend':
                resend_email_change(actor=request.user, token=token)
                messages.success(request, copy('sent'))
                return redirect('account_email_change')
            else:
                raise EmailChangeError('unavailable')
            if result.ok:
                messages.success(request, result.message)
                return redirect('account_settings')
            error = result.message
        except EmailChangeError as exc:
            error = exc.messages[0]
    return render(request, 'pages/account_email_change.html', {
        'pending_email_change': pending_for(request.user), 'email_change_error': error,
    }, status=400 if error else 200)
