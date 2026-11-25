"""IndexNow leases, successful submissions and delayed retries in the default cache."""
import hashlib
from contextlib import nullcontext
from threading import RLock
from uuid import uuid4

from django.core.cache import caches
from django.core.cache.backends.locmem import LocMemCache
from django.core.cache.backends.redis import RedisCache
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone


LEASE_SECONDS = 60
RETRY_SECONDS = (60, 300, 1800)
DUE_KEY = "indexnow:v2:due"
_local_lock = RLock()

# All changes are fenced by the lease obtained with cache.add(). Django's
# Redis serializer stores integers as decimal bytes, including our lease token.
_UPDATE = """
if redis.call('GET', KEYS[1]) ~= ARGV[1] then return 0 end
if ARGV[2] == 'schedule' then
    redis.call('SET', KEYS[3], ARGV[3])
    redis.call('ZADD', KEYS[4], ARGV[4], ARGV[5])
elseif ARGV[2] == 'clear' then
    redis.call('DEL', KEYS[3])
    redis.call('ZREM', KEYS[4], ARGV[5])
end
if tonumber(ARGV[6]) > 0 then
    redis.call('SET', KEYS[2], 1, 'EX', ARGV[6])
end
if ARGV[7] == '1' then redis.call('DEL', KEYS[1]) end
return 1
"""


def url_key(url):
    return "indexnow:v2:" + hashlib.sha256(url.encode()).hexdigest()


class DeliveryBatch:
    def __init__(self):
        self.cache = caches["default"]
        self.token = uuid4().int
        if isinstance(self.cache, RedisCache):
            self.redis = self.cache._cache.get_client(write=True)
            self.update_script = self.redis.register_script(_UPDATE)
            self.guard = nullcontext()
        elif isinstance(self.cache, LocMemCache):
            self.redis = None
            self.guard = _local_lock
        else:
            raise ImproperlyConfigured("IndexNow requires Redis or the local development cache")

    def due_urls(self, limit):
        now = timezone.now().timestamp()
        if self.redis is not None:
            members = self.redis.zrangebyscore(self.cache.make_key(DUE_KEY), "-inf", now, start=0, num=limit)
            return [member.decode() for member in members]
        with self.guard:
            due = self.cache.get(DUE_KEY, {})
            return sorted((url for url in due if due[url] <= now), key=due.get)[:limit]

    def _due_at(self, url):
        if self.redis is not None:
            return self.redis.zscore(self.cache.make_key(DUE_KEY), url)
        return self.cache.get(DUE_KEY, {}).get(url)

    def _update(self, url, action, *, retry=0, due=0, cooldown=0, release=True):
        base = url_key(url)
        lease, sent, count = base + ":lease", base + ":sent", base + ":retry"
        if self.redis is not None:
            keys = [self.cache.make_key(k) for k in (lease, sent, count, DUE_KEY)]
            args = [self.token, action, retry, due, url, cooldown, int(release)]
            return self.update_script(keys=keys, args=args)
        with self.guard:
            if self.cache.get(lease) != self.token:
                return False
            if action != "keep":
                schedule = self.cache.get(DUE_KEY, {})
                if action == "schedule":
                    self.cache.set(count, retry, timeout=None)
                    schedule[url] = due
                else:
                    self.cache.delete(count)
                    schedule.pop(url, None)
                self.cache.set(DUE_KEY, schedule, timeout=None)
            if cooldown:
                self.cache.set(sent, 1, timeout=cooldown)
            if release:
                self.cache.delete(lease)
            return True

    def _next_retry(self, url, retries_used, due, *, release):
        if retries_used >= len(RETRY_SECONDS):
            return self._update(url, "clear", release=release)
        return self._update(url, "schedule", retry=retries_used + 1, due=due, release=release)

    def claim(self, url, *, scheduled, force):
        base = url_key(url)
        with self.guard:
            if not self.cache.add(base + ":lease", self.token, timeout=LEASE_SECONDS):
                return None
            now = timezone.now().timestamp()
            if scheduled:
                # A concurrent edit may have replaced or cleared the selected retry.
                due = self._due_at(url)
                attempt = self.cache.get(base + ":retry")
                if due is None or attempt is None:
                    self._update(url, "clear")
                    return None
                eligible = due <= now
            else:
                attempt = 0
                eligible = force or not self.cache.get(base + ":sent")
            if not eligible:
                self._update(url, "keep")
                return None
            # If this worker exits during HTTP, cron can reclaim the expired lease.
            if self._next_retry(url, attempt, now + LEASE_SECONDS, release=False):
                return attempt
            return None

    def finish(self, url, attempt, *, transient, cooldown):
        if transient and attempt < len(RETRY_SECONDS):
            due = timezone.now().timestamp() + RETRY_SECONDS[attempt]
            self._next_retry(url, attempt, due, release=True)
        else:
            self._update(url, "clear", cooldown=cooldown)
