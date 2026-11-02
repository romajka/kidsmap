"""Bounded authentication budgets; no stored raw identifiers.

All POST attempts count, including successful ones. Fixed windows never extend
on rejection; a boundary can admit two adjacent budgets. Redis increment/expiry
is one atomic script (Django's exists()+incr() alone has an expiry race).
Only Redis is accepted in production; LocMem is for isolated tests/development.
"""
import ipaddress
import math
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.core.cache.backends.locmem import LocMemCache
from django.core.cache.backends.redis import RedisCache
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.utils.crypto import salted_hmac


_INCREMENT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 or redis.call('TTL', KEYS[1]) < 0 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""


def _address(raw):
    try:
        address = ipaddress.ip_address(str(raw))
        return address.ipv4_mapped if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped else address
    except ValueError:
        return None


def client_address(request):
    peer = _address(request.META.get('REMOTE_ADDR', ''))
    trusted = [ipaddress.ip_network(value, strict=False)
               for value in settings.AUTH_THROTTLE_TRUSTED_PROXIES]
    address = peer
    if peer and any(peer in network for network in trusted):
        # The configured immediate proxy MUST overwrite this header. XFF is
        # deliberately ignored, including client-supplied chains and ports.
        address = _address(request.META.get('HTTP_X_REAL_IP', '')) or peer
    if address is None:
        return 'unknown'
    if address.version == 6:
        return str(ipaddress.ip_network((address, 64), strict=False))
    return str(address)


def _increment(backend, key, timeout):
    if isinstance(backend, RedisCache):
        # Django has no public atomic increment-with-expiry API. Keep this
        # backend-specific adapter small and covered against real Redis.
        client = backend._cache.get_client(key, write=True)
        return int(client.eval(_INCREMENT, 1, backend.make_key(key), timeout))
    if isinstance(backend, LocMemCache) and (settings.DEBUG or settings.TESTING):
        backend.add(key, 0, timeout=timeout)
        return backend.incr(key)
    raise ImproperlyConfigured('Authentication throttling requires shared Redis')


def _identity(request, action):
    field = 'email' if action == 'reset' else 'username'
    value = str(request.POST.get(field, '')).strip().casefold()[:1024]
    users = get_user_model().objects
    if action == 'reset':
        # Mirror the reset form's username-to-mailbox resolution, without
        # checking eligibility or exposing whether a mailbox exists.
        if '@' not in value:
            email = users.filter(username__iexact=value).exclude(email='').order_by('id').values_list('email', flat=True).first()
            value = email.strip().casefold() if email else value
        return 'mailbox:' + value
    user_id = users.filter(Q(username__iexact=value) | Q(email__iexact=value)).order_by('id').values_list('pk', flat=True).first()
    return f'account:{user_id}' if user_id else 'input:' + value


def retry_after(request, action):
    """Consume IP first, then identity; return 0 or seconds until next window.

    Exceptions intentionally propagate: the middleware fails closed before
    password verification or email sending. No fallback to per-process state.
    """
    policy = settings.AUTH_THROTTLE_LIMITS[action]
    window = int(policy['window'])
    if window < 1 or int(policy['ip']) < 1 or int(policy['identity']) < 1:
        raise ImproperlyConfigured('Authentication throttle limits must be positive')
    now = time.time()
    bucket = int(now // window)
    remaining = max(1, math.ceil(window - now % window))
    backend = caches['default']
    # Don't perform a user lookup once the IP budget is exhausted.
    for scope in ('ip', 'identity'):
        value = client_address(request) if scope == 'ip' else _identity(request, action)
        digest = salted_hmac('catalog.auth-throttle.v1', value, algorithm='sha256').hexdigest()
        key = f'auth-throttle:v1:{action}:{scope}:{bucket}:{digest}'
        if _increment(backend, key, window + 1) > int(policy[scope]):
            return remaining
    return 0
