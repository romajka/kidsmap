"""Clients for immutable test fixtures, never application HTTP caching."""
from django.test import Client


class ReadOnlyFixtureClient(Client):
    """Read-only fixture transport used by the internal-links command smoke test."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._read_responses = {}

    def get(self, path, *args, **kwargs):
        # Scope is one immutable command fixture. Every distinct request still
        # reaches the real view; cookies/arguments cannot share another reply.
        key = (path, repr(args), repr(sorted(kwargs.items())), self.cookies.output())
        if key not in self._read_responses:
            self._read_responses[key] = super().get(path, *args, **kwargs)
        return self._read_responses[key]

    def request(self, **request):
        if request.get('REQUEST_METHOD', 'GET') not in ('GET', 'HEAD'):
            raise ValueError('Immutable fixture client permits read requests only')
        return super().request(**request)
